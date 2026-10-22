"""
Model-Aware Passage Segmentation.
Ensures all document passages strictly adhere to the dense embedding model's
maximum token sequence budget (e.g. 512 tokens for multilingual-e5-small)
while preserving exact Unicode code-point offsets into the original text.
"""

import logging
from typing import List, Optional, Tuple
from transformers import AutoTokenizer

from plagiarism.core.config import get_settings
from plagiarism.services.segmentation import (
    SegmentedPassage,
    segment_document_passages,
    split_sentences_with_offsets,
)
from plagiarism.services.preprocessing import normalize_text_nfc, normalize_nfc

logger = logging.getLogger(__name__)


class ModelAwareSegmenter:
    """
    Validates and splits passages against the embedding model's tokenizer budget.
    """

    def __init__(
        self,
        tokenizer_name: Optional[str] = None,
        max_tokens: int = 500,
        cache_dir: Optional[str] = None,
    ):
        settings = get_settings()
        self.tokenizer_name = tokenizer_name or settings.SEMANTIC_MODEL_NAME
        self.max_tokens = min(max_tokens, settings.SEMANTIC_MAX_SEQ_LENGTH - 12)  # reserve for prefixes
        self.cache_dir = cache_dir or str(settings.SEMANTIC_MODEL_CACHE_DIR)
        self._tokenizer = None
        self._load_tokenizer()

    def _load_tokenizer(self) -> None:
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.tokenizer_name,
                cache_dir=self.cache_dir,
                use_fast=True,
                local_files_only=True,
            )
        except Exception as offline_err:
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.tokenizer_name,
                    cache_dir=self.cache_dir,
                    use_fast=True,
                )
            except Exception as e:
                logger.warning("Could not load HuggingFace tokenizer (%s); falling back to word estimation: %s", self.tokenizer_name, e)
                self._tokenizer = None

    def count_tokens(self, text: str) -> int:
        """Accurately counts tokens for the model tokenizer."""
        if not text:
            return 0
        if self._tokenizer:
            return len(self._tokenizer.encode(text, add_special_tokens=False))
        # Fallback conservative heuristic
        return int(len(text.split()) * 1.35)

    def prepare_passages(
        self,
        document_id: str,
        original_text: str,
        existing_passages: Optional[List[SegmentedPassage]] = None,
        detected_language: str = "en",
    ) -> List[SegmentedPassage]:
        """
        Takes raw text or existing Phase 2 passages and ensures all chunks strictly obey
        the embedding model sequence length. Sub-divides oversized chunks at sentence boundaries.
        """
        nfc_text = normalize_nfc(original_text)
        if not nfc_text.strip():
            return []

        # If no passages provided, segment first using Phase 2 pipeline
        base_passages = existing_passages
        if not base_passages:
            base_passages = segment_document_passages(
                document_id=document_id,
                original_text=nfc_text,
                detected_language=detected_language,
                target_tokens_per_passage=100,
                min_tokens_per_passage=10,
            )

        final_passages: List[SegmentedPassage] = []
        seq_idx = 0

        for p in base_passages:
            tok_count = self.count_tokens(p.text_content)
            if tok_count <= self.max_tokens:
                p.sequence_index = seq_idx
                p.token_count = tok_count
                final_passages.append(p)
                seq_idx += 1
            else:
                # Oversized passage: sub-divide along sentence boundaries
                sentences = split_sentences_with_offsets(p.text_content)
                current_chunk_sentences: List[str] = []
                current_start = p.start_offset
                current_end = p.start_offset

                for sent_text, s_start, s_end in sentences:
                    test_chunk = " ".join(current_chunk_sentences + [sent_text])
                    if self.count_tokens(test_chunk) > self.max_tokens and current_chunk_sentences:
                        # Flush current chunk
                        chunk_str = " ".join(current_chunk_sentences)
                        final_passages.append(
                            SegmentedPassage(
                                passage_id=f"{document_id}_p{seq_idx}",
                                document_id=document_id,
                                sequence_index=seq_idx,
                                start_offset=current_start,
                                end_offset=current_end,
                                text_content=chunk_str,
                                token_count=self.count_tokens(chunk_str),
                                page_number=p.page_number,
                                language=p.language,
                            )
                        )
                        seq_idx += 1
                        current_chunk_sentences = [sent_text]
                        current_start = p.start_offset + s_start
                        current_end = p.start_offset + s_end
                    else:
                        current_chunk_sentences.append(sent_text)
                        current_end = p.start_offset + s_end

                if current_chunk_sentences:
                    chunk_str = " ".join(current_chunk_sentences)
                    final_passages.append(
                        SegmentedPassage(
                            passage_id=f"{document_id}_p{seq_idx}",
                            document_id=document_id,
                            sequence_index=seq_idx,
                            start_offset=current_start,
                            end_offset=current_end,
                            text_content=chunk_str,
                            token_count=self.count_tokens(chunk_str),
                            page_number=p.page_number,
                            language=p.language,
                        )
                    )
                    seq_idx += 1

        return final_passages
