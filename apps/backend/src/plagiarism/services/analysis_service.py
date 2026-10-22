"""
Lexical Analysis Service.
Coordinates the end-to-end plagiarism detection pipeline:
Tokenization -> Winnowing -> BM25 Candidate Retrieval -> Passage Alignment -> Evidence Verification -> Coverage Calculation.
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from plagiarism.services.lexical.tokenizer import LexicalTokenizer, LexicalToken
from plagiarism.services.lexical.winnowing import WinnowingEngine, Fingerprint
from plagiarism.services.lexical.bm25 import BM25Index
from plagiarism.services.lexical.aligner import PassageAligner, AlignedFinding
from plagiarism.services.lexical.coverage import CoverageCalculator, SourceCoverageSummary
from plagiarism.storage.local_db import LocalMetadataRepository, get_local_repo
from plagiarism.core.errors import BadRequestError, NotFoundError

logger = logging.getLogger(__name__)


class LexicalAnalysisService:
    """
    Executes real lexical plagiarism detection on uploaded documents.
    """

    def __init__(
        self,
        repo: Optional[LocalMetadataRepository] = None,
        tokenizer: Optional[LexicalTokenizer] = None,
        winnowing: Optional[WinnowingEngine] = None,
        aligner: Optional[PassageAligner] = None,
        coverage_calc: Optional[CoverageCalculator] = None,
    ):
        self.repo = repo or get_local_repo()
        self.tokenizer = tokenizer or LexicalTokenizer()
        self.winnowing = winnowing or WinnowingEngine(k=25, w=16)
        self.aligner = aligner or PassageAligner(min_token_match=8, min_char_length=25)
        self.coverage_calc = coverage_calc or CoverageCalculator()

    def run_analysis(
        self,
        analysis_id: str,
        owner_user_id: str,
        submission_document_id: str,
        mode: str,
        reference_document_id: Optional[str] = None,
        reference_document_ids: Optional[List[str]] = None,
        collection_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes complete lexical detection synchronously.
        Can be invoked directly or in a background thread.
        """
        try:
            # 1. Load submission document
            self.repo.update_analysis_status(
                analysis_id, status="processing", progress_percent=10, current_step="loading_submission"
            )
            sub_doc = self.repo.get_document(submission_document_id)
            if not sub_doc:
                raise NotFoundError(f"Submission document {submission_document_id} not found")
            if sub_doc["status"] != "completed":
                raise BadRequestError(f"Submission document is in {sub_doc['status']} status; must be 'completed'")

            sub_raw_text = sub_doc.get("raw_text", "")
            sub_tokens = self.tokenizer.tokenize(sub_raw_text)

            # Fingerprint submission document if not already indexed
            sub_fps = self.repo.get_fingerprints(submission_document_id)
            if not sub_fps:
                generated_fps = self.winnowing.fingerprint_tokens(sub_tokens)
                self.repo.save_fingerprints(
                    submission_document_id, generated_fps, self.winnowing.algorithm_version
                )

            # 2. Resolve Candidate Reference Documents
            self.repo.update_analysis_status(
                analysis_id, status="processing", progress_percent=25, current_step="resolving_candidates"
            )
            candidate_docs: List[Dict[str, Any]] = []

            if mode == "direct":
                if not reference_document_id:
                    raise BadRequestError("Direct comparison mode requires 'reference_document_id'")
                ref = self.repo.get_document(reference_document_id)
                if not ref:
                    raise NotFoundError(f"Reference document {reference_document_id} not found")
                if ref["status"] != "completed":
                    raise BadRequestError(f"Reference document is in '{ref['status']}' status")
                candidate_docs.append(ref)

            elif mode == "one_to_many":
                ref_ids = reference_document_ids or []
                if not ref_ids:
                    raise BadRequestError("One-to-many mode requires 'reference_document_ids'")
                for rid in ref_ids:
                    if rid == submission_document_id:
                        continue  # Do not compare against self
                    ref = self.repo.get_document(rid)
                    if ref and ref["status"] == "completed":
                        candidate_docs.append(ref)
                if not candidate_docs:
                    raise BadRequestError("No completed reference documents available for comparison")

            elif mode == "corpus":
                if not collection_id:
                    raise BadRequestError("Corpus mode requires 'collection_id'")
                col = self.repo.get_collection(collection_id)
                if not col:
                    raise NotFoundError(f"Collection {collection_id} not found")
                col_members = self.repo.list_collection_documents(collection_id)
                for mem in col_members:
                    if mem["document_id"] == submission_document_id:
                        continue
                    if mem["status"] == "completed":
                        candidate_docs.append(mem)
                if not candidate_docs:
                    raise BadRequestError(f"Collection {collection_id} contains no eligible completed documents")

            else:
                raise BadRequestError(f"Unknown comparison mode '{mode}'")

            # 3. Candidate Retrieval & BM25 Ranking
            self.repo.update_analysis_status(
                analysis_id, status="processing", progress_percent=40, current_step="candidate_retrieval"
            )
            bm25 = BM25Index(k1=1.2, b=0.75)
            ref_tokens_cache: Dict[str, List[LexicalToken]] = {}

            candidate_ids = [c["document_id"] for c in candidate_docs]
            for c in candidate_docs:
                c_id = c["document_id"]
                c_raw = c.get("raw_text", "")
                c_toks = self.tokenizer.tokenize(c_raw)
                ref_tokens_cache[c_id] = c_toks
                bm25.add_document(c_id, [t.norm_text for t in c_toks])

                # Ensure reference fingerprints exist
                c_fps = self.repo.get_fingerprints(c_id)
                if not c_fps:
                    c_gen_fps = self.winnowing.fingerprint_tokens(c_toks)
                    self.repo.save_fingerprints(c_id, c_gen_fps, self.winnowing.algorithm_version)

            sub_norm_tokens = [t.norm_text for t in sub_tokens]
            bm25_rankings = bm25.rank_candidates(sub_norm_tokens, candidate_ids, top_k=len(candidate_ids))
            bm25_score_map = dict(bm25_rankings)

            # Query shared fingerprints
            shared_fps = self.repo.find_shared_fingerprints(submission_document_id, candidate_ids)
            shared_fp_counts: Dict[str, int] = {}
            for sfp in shared_fps:
                r_id = sfp["reference_document_id"]
                shared_fp_counts[r_id] = shared_fp_counts.get(r_id, 0) + 1

            candidate_metadata = {
                "total_candidates_evaluated": len(candidate_docs),
                "bm25_scores": bm25_score_map,
                "shared_fingerprint_counts": shared_fp_counts,
                "algorithm_version": self.winnowing.algorithm_version,
            }

            # 4. Detailed Passage Alignment
            self.repo.update_analysis_status(
                analysis_id, status="processing", progress_percent=65, current_step="aligning_passages"
            )
            all_findings: List[AlignedFinding] = []

            for c in candidate_docs:
                c_id = c["document_id"]
                c_title = c.get("title") or c.get("filename") or "Reference Document"
                c_raw = c.get("raw_text", "")
                c_toks = ref_tokens_cache[c_id]

                findings = self.aligner.align_documents(
                    submission_id=submission_document_id,
                    submission_raw_text=sub_raw_text,
                    submission_tokens=sub_tokens,
                    reference_id=c_id,
                    reference_title=c_title,
                    reference_raw_text=c_raw,
                    reference_tokens=c_toks,
                )
                all_findings.extend(findings)

            # 5. Coverage Calculation
            self.repo.update_analysis_status(
                analysis_id, status="processing", progress_percent=85, current_step="calculating_coverage"
            )
            overall_cov, source_summaries = self.coverage_calc.calculate(
                len(sub_tokens), all_findings
            )

            # 6. Save Analysis Results
            self.repo.save_analysis_results(
                analysis_id=analysis_id,
                overall_lexical_cov=overall_cov,
                findings=all_findings,
                sources=source_summaries,
                candidate_metadata=candidate_metadata,
            )

            return self.repo.get_analysis(analysis_id)

        except Exception as e:
            logger.exception("Error executing lexical analysis %s: %s", analysis_id, str(e))
            self.repo.update_analysis_status(
                analysis_id,
                status="failed",
                progress_percent=0,
                current_step="failed",
                error_code="ANALYSIS_EXECUTION_ERROR",
                error_message=str(e),
            )
            raise


_analysis_service: Optional[LexicalAnalysisService] = None


def get_analysis_service() -> LexicalAnalysisService:
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = LexicalAnalysisService()
    return _analysis_service
