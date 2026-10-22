"""
Unit Tests for Deterministic Passage Segmentation Service
Verifies sentence splitting across English, Hindi, and Telugu, code-point offset preservation,
and short document handling.
"""

import pytest
from plagiarism.services.segmentation import (
    split_sentences_with_offsets,
    segment_document_passages,
)


def test_split_sentences_english():
    text = "First sentence here. Second sentence starts now! Is this the third sentence? Yes it is."
    sentences = split_sentences_with_offsets(text)
    assert len(sentences) == 4
    for s_text, start, end in sentences:
        assert text[start:end].strip() == s_text
        assert end > start


def test_split_sentences_hindi():
    text = "यह पहला वाक्य है। यह दूसरा वाक्य है॥ क्या यह तीसरा वाक्य है? हाँ यह है।"
    sentences = split_sentences_with_offsets(text)
    assert len(sentences) == 4
    for s_text, start, end in sentences:
        assert text[start:end].strip() == s_text
        assert end > start


def test_split_sentences_telugu():
    text = "ఇది మొదటి వాక్యం. ఇది రెండవ వాక్యం! ఇది మూడవ వాక్యమా? అవును."
    sentences = split_sentences_with_offsets(text)
    assert len(sentences) == 4
    for s_text, start, end in sentences:
        assert text[start:end].strip() == s_text
        assert end > start


def test_passage_segmentation_offsets_integrity():
    text = (
        "Plagiarism analysis requires robust passage alignment. "
        "Each passage must retain exact offsets to the original source text. "
        "This ensures that future highlighting matches the raw uploaded document without distortion. "
        "Here is additional text to ensure adequate length for segmentation across multiple blocks."
    )
    doc_id = "doc-test-123"
    passages = segment_document_passages(
        document_id=doc_id,
        original_text=text,
        detected_language="en",
        target_tokens_per_passage=15,
        min_tokens_per_passage=5
    )

    assert len(passages) >= 2
    for p in passages:
        assert p.document_id == doc_id
        assert p.end_offset > p.start_offset
        # Exact substring match check
        slice_text = text[p.start_offset:p.end_offset].strip()
        assert slice_text == p.text_content
        assert p.token_count > 0


def test_short_document_retention():
    """Verify that short documents (e.g. 15 words) are NOT discarded, but retained as a valid passage."""
    short_text = "Short abstract document with twenty words to test boundary handling in plagiarism engine."
    passages = segment_document_passages(
        document_id="doc-short-001",
        original_text=short_text,
        detected_language="en",
        min_tokens_per_passage=5
    )
    assert len(passages) == 1
    p = passages[0]
    assert p.text_content == short_text
    assert p.start_offset == 0
    assert p.end_offset == len(short_text)
