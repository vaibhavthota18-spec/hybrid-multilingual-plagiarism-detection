"""
Deterministic Passage Segmentation Service
Segments documents into contiguous passages with exact code-point offsets into the original text.
Uses sentence and paragraph boundaries across English, Hindi, and Telugu.
"""

import re
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from plagiarism.services.preprocessing import identify_language, tokenize_unicode


@dataclass
class SegmentedPassage:
    passage_id: str
    document_id: str
    sequence_index: int
    start_offset: int
    end_offset: int
    text_content: str
    token_count: int
    page_number: int
    language: str


# Sentence delimiter regex across English, Hindi, and Telugu
# Includes Devanagari danda (\u0964), double danda (\u0965), periods, question marks, exclamation marks
SENTENCE_END_PATTERN = re.compile(r'([.?!।॥]+(?:\s+|\n+|$))')


def split_sentences_with_offsets(text: str) -> List[Tuple[str, int, int]]:
    """
    Splits text into sentences while tracking exact code-point start and end offsets [start, end).
    """
    sentences = []
    current_idx = 0

    parts = SENTENCE_END_PATTERN.split(text)
    # Recombine sentence content with its punctuation delimiter
    i = 0
    while i < len(parts):
        chunk = parts[i]
        delimiter = parts[i + 1] if (i + 1) < len(parts) else ""
        sentence_str = chunk + delimiter
        i += 2

        if not sentence_str:
            continue

        start_offset = text.find(sentence_str, current_idx)
        if start_offset == -1:
            start_offset = current_idx
        end_offset = start_offset + len(sentence_str)
        current_idx = end_offset

        clean_text = sentence_str.strip()
        if clean_text:
            sentences.append((clean_text, start_offset, end_offset))

    # Fallback if no punctuation matched
    if not sentences and text.strip():
        sentences.append((text.strip(), 0, len(text)))

    return sentences


def segment_document_passages(
    document_id: str,
    original_text: str,
    detected_language: str = "en",
    page_texts: Optional[List[Tuple[int, str]]] = None,
    target_tokens_per_passage: int = 120,
    min_tokens_per_passage: int = 12
) -> List[SegmentedPassage]:
    """
    Deterministically segments original text into contiguous passages.
    Preserves exact [start_offset, end_offset) into original_text.
    """
    if not original_text.strip():
        return []

    # Map page boundaries if page_texts are provided
    page_offset_map = []
    if page_texts:
        curr = 0
        for page_num, ptext in page_texts:
            if not ptext:
                continue
            idx = original_text.find(ptext, curr)
            if idx != -1:
                page_offset_map.append((idx, idx + len(ptext), page_num))
                curr = idx + len(ptext)

    def get_page_number_for_offset(offset: int) -> int:
        for p_start, p_end, p_num in page_offset_map:
            if p_start <= offset < p_end:
                return p_num
        return 1

    sentences = split_sentences_with_offsets(original_text)
    passages: List[SegmentedPassage] = []

    current_chunk_sentences = []
    current_chunk_tokens = 0
    current_start = -1
    current_end = -1
    seq_index = 0

    for s_text, s_start, s_end in sentences:
        tokens = tokenize_unicode(s_text)
        token_count = len(tokens)

        if not current_chunk_sentences:
            current_start = s_start
            current_end = s_end
            current_chunk_sentences.append(s_text)
            current_chunk_tokens = token_count
        else:
            # Check if adding this sentence exceeds target size and current chunk is >= min_tokens
            if (current_chunk_tokens + token_count > target_tokens_per_passage) and (current_chunk_tokens >= min_tokens_per_passage):
                # Emit current passage
                combined_text = original_text[current_start:current_end].strip()
                p_id = str(uuid.uuid4())
                passages.append(
                    SegmentedPassage(
                        passage_id=p_id,
                        document_id=document_id,
                        sequence_index=seq_index,
                        start_offset=current_start,
                        end_offset=current_end,
                        text_content=combined_text,
                        token_count=current_chunk_tokens,
                        page_number=get_page_number_for_offset(current_start),
                        language=identify_language(combined_text, hint=detected_language)
                    )
                )
                seq_index += 1
                # Start new chunk
                current_start = s_start
                current_end = s_end
                current_chunk_sentences = [s_text]
                current_chunk_tokens = token_count
            else:
                current_chunk_sentences.append(s_text)
                current_chunk_tokens += token_count
                current_end = s_end

    # Emit final remaining chunk
    if current_chunk_sentences:
        combined_text = original_text[current_start:current_end].strip()
        p_id = str(uuid.uuid4())
        passages.append(
            SegmentedPassage(
                passage_id=p_id,
                document_id=document_id,
                sequence_index=seq_index,
                start_offset=current_start,
                end_offset=current_end,
                text_content=combined_text,
                token_count=current_chunk_tokens,
                page_number=get_page_number_for_offset(current_start),
                language=identify_language(combined_text, hint=detected_language)
            )
        )

    return passages
