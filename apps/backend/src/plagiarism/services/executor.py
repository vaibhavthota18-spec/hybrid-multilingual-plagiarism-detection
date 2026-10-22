"""
Local Document Processing Executor
Executes extraction, preprocessing, and passage segmentation in a controlled thread pool.
Manages job lifecycle: queued -> processing -> completed / failed.
"""

import concurrent.futures
import logging
from pathlib import Path
from typing import Optional

from plagiarism.services.extractors import extract_document
from plagiarism.services.preprocessing import preprocess_text
from plagiarism.services.segmentation import segment_document_passages
from plagiarism.storage.local_db import get_local_repo

logger = logging.getLogger("plagiarism.executor")


class LocalProcessingExecutor:
    """
    Local development-only task executor.
    Decouples document extraction from HTTP request threads without requiring Redis/RQ.
    """
    def __init__(self, max_workers: int = 2):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.repo = get_local_repo()
        # Reconcile any prior jobs interrupted by restart
        reconciled = self.repo.reconcile_incomplete_jobs()
        if reconciled > 0:
            logger.warning(f"Reconciled {reconciled} interrupted document processing jobs on startup")

    def process_document_sync(
        self,
        document_id: str,
        storage_path: str,
        extension: str,
        language_hint: Optional[str] = "auto"
    ) -> None:
        """
        Processes document synchronously. Used for tests and deterministic flows.
        """
        try:
            # Mark processing
            self.repo.update_document_extraction(
                document_id=document_id,
                status="processing",
                page_count=1,
                char_count=0,
                word_count=0,
                raw_text="",
                detected_language="en",
                warnings=""
            )

            file_path = Path(storage_path)
            # 1. Extraction
            extraction = extract_document(file_path, extension)

            # 2. Preprocessing
            preprocessing = preprocess_text(extraction.raw_text, language_hint=language_hint)

            # 3. Segmentation
            passages = segment_document_passages(
                document_id=document_id,
                original_text=preprocessing.original_text,
                detected_language=preprocessing.detected_language,
                page_texts=extraction.page_texts
            )

            # 4. Persistence
            passage_dicts = [
                {
                    "id": p.passage_id,
                    "document_id": p.document_id,
                    "sequence_index": p.sequence_index,
                    "start_offset": p.start_offset,
                    "end_offset": p.end_offset,
                    "text_content": p.text_content,
                    "token_count": p.token_count,
                    "page_number": p.page_number,
                    "language": p.language
                }
                for p in passages
            ]
            self.repo.insert_passages(passage_dicts)

            warnings_combined = "; ".join(extraction.warnings + preprocessing.warnings)

            # 5. Mark completed
            self.repo.update_document_extraction(
                document_id=document_id,
                status="completed",
                page_count=extraction.page_count,
                char_count=len(preprocessing.original_text),
                word_count=preprocessing.token_count,
                raw_text=preprocessing.original_text,
                detected_language=preprocessing.detected_language,
                warnings=warnings_combined
            )

        except Exception as e:
            logger.error(f"Extraction failed for document {document_id}: {str(e)}", exc_info=True)
            self.repo.update_document_extraction(
                document_id=document_id,
                status="failed",
                page_count=0,
                char_count=0,
                word_count=0,
                raw_text="",
                detected_language="en",
                warnings=f"Extraction failure: {str(e)}"
            )

    def submit_document_processing(
        self,
        document_id: str,
        storage_path: str,
        extension: str,
        language_hint: Optional[str] = "auto"
    ) -> None:
        """Submits document extraction job to RQ queue in production, or thread pool in local mode."""
        from plagiarism.core.config import get_settings
        settings = get_settings()

        if getattr(settings, "APP_RUNTIME_MODE", "local") == "production":
            try:
                from plagiarism.jobs.queue import get_queue
                from plagiarism.jobs.tasks import process_document_job
                from rq import Retry

                q = get_queue()
                job = q.enqueue(
                    process_document_job,
                    document_id=document_id,
                    storage_path=storage_path,
                    extension=extension,
                    language_hint=language_hint,
                    job_timeout=600,
                    retry=Retry(max=3, interval=[10, 30, 60]),
                    job_id=f"doc_{document_id}"
                )
                logger.info(f"Enqueued document extraction to RQ queue: job_id={job.id}")
                return
            except Exception as e:
                logger.warning(f"Failed to enqueue to RQ ({e}); falling back to local thread pool")

        self.executor.submit(
            self.process_document_sync,
            document_id,
            storage_path,
            extension,
            language_hint
        )

    def submit_analysis(
        self,
        analysis_id: str,
        owner_user_id: str,
        submission_document_id: str,
        mode: str,
        detection_mode: str = "hybrid",
        reference_document_id: Optional[str] = None,
        reference_document_ids: Optional[list] = None,
        collection_id: Optional[str] = None,
    ) -> None:
        """Submits similarity analysis job to RQ queue in production, or thread pool in local mode."""
        from plagiarism.core.config import get_settings
        settings = get_settings()

        if getattr(settings, "APP_RUNTIME_MODE", "local") == "production":
            try:
                from plagiarism.jobs.queue import get_queue
                from plagiarism.jobs.tasks import run_hybrid_analysis_job
                from rq import Retry

                q = get_queue()
                job = q.enqueue(
                    run_hybrid_analysis_job,
                    analysis_id=analysis_id,
                    owner_user_id=owner_user_id,
                    submission_document_id=submission_document_id,
                    mode=mode,
                    detection_mode=detection_mode,
                    reference_document_id=reference_document_id,
                    reference_document_ids=reference_document_ids,
                    collection_id=collection_id,
                    job_timeout=1200,
                    retry=Retry(max=2, interval=[15, 45]),
                    job_id=f"analysis_{analysis_id}"
                )
                logger.info(f"Enqueued similarity analysis to RQ queue: job_id={job.id}")
                return
            except Exception as e:
                logger.warning(f"Failed to enqueue analysis to RQ ({e}); falling back to local thread pool")

        from plagiarism.services.hybrid_service import get_hybrid_service
        hybrid_service = get_hybrid_service()
        self.executor.submit(
            hybrid_service.run_analysis,
            analysis_id,
            owner_user_id,
            submission_document_id,
            mode,
            detection_mode,
            reference_document_id,
            reference_document_ids,
            collection_id,
        )

    def submit_task(self, fn, *args, **kwargs):
        """Submits an arbitrary callable task to the background thread pool or queue."""
        return self.executor.submit(fn, *args, **kwargs)


_executor: Optional[LocalProcessingExecutor] = None


def get_executor() -> LocalProcessingExecutor:
    """Returns singleton LocalProcessingExecutor instance."""
    global _executor
    if _executor is None:
        _executor = LocalProcessingExecutor()
    return _executor


get_task_executor = get_executor

