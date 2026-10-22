"""
Semantic Plagiarism Matcher and Candidate Retrieval.
Executes dense vector search, paraphrase classification, and cross-lingual alignment.
Uses intfloat/multilingual-e5-small embeddings with calibrated thresholds to identify
same-language paraphrases and cross-language semantic equivalents across English, Hindi, and Telugu.
"""

from dataclasses import dataclass
import hashlib
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from plagiarism.core.config import get_settings
from plagiarism.services.semantic.provider import (
    SemanticEmbeddingProvider,
    get_embedding_provider,
)
from plagiarism.services.semantic.segmentation import ModelAwareSegmenter
from plagiarism.storage.vector_store import (
    PassageVectorRecord,
    VectorIndex,
    VectorSearchResult,
    get_vector_repository,
)
from plagiarism.storage.local_db import LocalMetadataRepository, get_local_repo
from plagiarism.services.segmentation import SegmentedPassage

logger = logging.getLogger(__name__)


@dataclass
class SemanticFinding:
    finding_id: str
    submission_document_id: str
    reference_document_id: str
    reference_source_title: str
    category: str  # 'paraphrase' or 'potential_translation'
    confidence: str  # 'high', 'moderate', 'low'
    submission_start_offset: int
    submission_end_offset: int
    submission_excerpt: str
    reference_start_offset: int
    reference_end_offset: int
    reference_excerpt: str
    reference_page_number: int
    matched_token_count: int
    lexical_similarity: float
    semantic_similarity: float
    is_quoted: bool
    is_excluded: bool
    language_pair: str
    model_name: str


class SemanticMatcher:
    """
    Coordinates passage embedding, indexing, vector search, and semantic evidence alignment.
    """

    def __init__(
        self,
        provider: Optional[SemanticEmbeddingProvider] = None,
        vector_repo: Optional[VectorIndex] = None,
        segmenter: Optional[ModelAwareSegmenter] = None,
        repo: Optional[LocalMetadataRepository] = None,
    ):
        self.provider = provider or get_embedding_provider()
        self.vector_repo = vector_repo or get_vector_repository()
        self.segmenter = segmenter or ModelAwareSegmenter()
        self.repo = repo or get_local_repo()
        self.settings = get_settings()

    def ensure_document_indexed(
        self,
        document_id: str,
        raw_text: str,
        detected_language: str = "en",
    ) -> List[PassageVectorRecord]:
        """
        Generates and persists passage embeddings if not already cached for current model revision.
        """
        model_info = self.provider.get_model_info()
        model_id = model_info["model_name"]
        model_rev = model_info["revision"]

        if self.vector_repo.is_indexed(document_id, model_id, model_rev):
            return self.vector_repo.get_document_embeddings(document_id)

        # 1. Segment document into model-aware passages
        passages: List[SegmentedPassage] = self.segmenter.prepare_passages(
            document_id=document_id,
            original_text=raw_text,
            detected_language=detected_language,
        )

        if not passages:
            return []

        # 2. Encode passages using passage prefix
        texts = [p.text_content for p in passages]
        embeddings = self.provider.encode_passages(texts)

        # 3. Store vector records
        records = []
        now_str = self.repo._get_connection().execute("SELECT datetime('now')").fetchone()[0]
        for p, emb in zip(passages, embeddings):
            text_hash = hashlib.sha256(p.text_content.encode("utf-8")).hexdigest()
            records.append(
                PassageVectorRecord(
                    passage_id=p.passage_id,
                    document_id=document_id,
                    sequence_index=p.sequence_index,
                    start_offset=p.start_offset,
                    end_offset=p.end_offset,
                    text_content=p.text_content,
                    model_id=model_id,
                    model_revision=model_rev,
                    embedding=emb,
                    text_hash=text_hash,
                    created_at=now_str,
                )
            )

        self.vector_repo.store_document_embeddings(records)
        return records

    def match_documents(
        self,
        submission_document_id: str,
        submission_text: str,
        submission_lang: str,
        candidate_docs: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[SemanticFinding]:
        """
        Performs dense semantic retrieval and evidence mapping across candidate documents.
        """
        if not submission_text.strip() or not candidate_docs:
            return []

        # 1. Segment submission into query passages
        sub_passages: List[SegmentedPassage] = self.segmenter.prepare_passages(
            document_id=submission_document_id,
            original_text=submission_text,
            detected_language=submission_lang,
        )

        if not sub_passages:
            return []

        # 2. Encode query passages using query prefix
        query_texts = [p.text_content for p in sub_passages]
        query_embeddings = self.provider.encode_queries(query_texts)

        # 3. Ensure all candidate documents have passage embeddings indexed
        candidate_ids = []
        candidate_doc_map = {}
        for c in candidate_docs:
            cid = c["document_id"]
            candidate_ids.append(cid)
            candidate_doc_map[cid] = c
            self.ensure_document_indexed(
                document_id=cid,
                raw_text=c.get("raw_text", ""),
                detected_language=c.get("detected_language", "en"),
            )

        # 4. Dense cosine candidate search
        min_cutoff = min(
            self.settings.SEMANTIC_PARAPHRASE_THRESHOLD - 0.05,
            self.settings.SEMANTIC_TRANSLATION_THRESHOLD - 0.05,
        )
        search_results: List[List[VectorSearchResult]] = self.vector_repo.search_candidates(
            query_vectors=query_embeddings,
            candidate_document_ids=candidate_ids,
            top_k=top_k,
            min_similarity=min_cutoff,
        )

        model_info = self.provider.get_model_info()
        model_name = model_info["model_name"]
        sub_lang = submission_lang or "en"
        findings: List[SemanticFinding] = []

        # 5. Evaluate and classify findings
        for q_idx, res_list in enumerate(search_results):
            sub_p = sub_passages[q_idx]

            for hit in res_list:
                score = hit.cosine_similarity
                ref_doc = candidate_doc_map.get(hit.reference_document_id, {})
                ref_lang = ref_doc.get("detected_language", "en")
                ref_title = ref_doc.get("title") or ref_doc.get("filename") or "Reference Document"

                is_cross_lang = (
                    sub_lang != ref_lang
                    and sub_lang in ("en", "hi", "te")
                    and ref_lang in ("en", "hi", "te")
                )

                threshold = (
                    self.settings.SEMANTIC_TRANSLATION_THRESHOLD
                    if is_cross_lang
                    else self.settings.SEMANTIC_PARAPHRASE_THRESHOLD
                )

                if score < threshold:
                    # Filter out sub-threshold candidates (including hard negatives)
                    continue

                category = "potential_translation" if is_cross_lang else "paraphrase"

                # Assign confidence based on calibrated margins
                if score >= 0.88:
                    confidence = "high"
                elif score >= 0.83:
                    confidence = "moderate"
                else:
                    confidence = "low"

                lang_pair = f"{sub_lang}-{ref_lang}"

                findings.append(
                    SemanticFinding(
                        finding_id=str(uuid.uuid4()),
                        submission_document_id=submission_document_id,
                        reference_document_id=hit.reference_document_id,
                        reference_source_title=ref_title,
                        category=category,
                        confidence=confidence,
                        submission_start_offset=sub_p.start_offset,
                        submission_end_offset=sub_p.end_offset,
                        submission_excerpt=sub_p.text_content,
                        reference_start_offset=hit.reference_start_offset,
                        reference_end_offset=hit.reference_end_offset,
                        reference_excerpt=hit.reference_text_content,
                        reference_page_number=1,
                        matched_token_count=sub_p.token_count,
                        lexical_similarity=0.0,
                        semantic_similarity=round(score, 4),
                        is_quoted=False,
                        is_excluded=False,
                        language_pair=lang_pair,
                        model_name=model_name,
                    )
                )

        return findings
