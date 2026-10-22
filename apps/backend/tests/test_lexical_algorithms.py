"""
Comprehensive Unit Tests for Phase 3 Lexical Detection Algorithms:
Tokenizer, Rolling Hash, Winnowing, BM25, Aligner, and Coverage.
"""

import pytest
from plagiarism.services.lexical.tokenizer import LexicalTokenizer, detect_token_script
from plagiarism.services.lexical.rolling_hash import fnv1a_64, compute_kgram_hash, RollingHash
from plagiarism.services.lexical.winnowing import WinnowingEngine, Fingerprint
from plagiarism.services.lexical.bm25 import BM25Index
from plagiarism.services.lexical.aligner import PassageAligner
from plagiarism.services.lexical.coverage import CoverageCalculator, merge_token_intervals


def test_tokenizer_offsets_and_multilingual():
    tokenizer = LexicalTokenizer()
    text = "Hello world! यह एक हिंदी शोध पत्र है। ఇది ఒక పరిశోధన వ్యాసం."
    tokens = tokenizer.tokenize(text)

    assert len(tokens) > 0
    # Strict offset invariant: raw_text[start:end] == token.text
    for t in tokens:
        assert text[t.start_char : t.end_char] == t.text
        assert t.start_char <= t.end_char
        assert t.start_utf16 <= t.end_utf16

    # Verify script detection
    scripts = {t.norm_text: t.script for t in tokens}
    assert scripts["hello"] == "LATIN"
    assert scripts["शोध"] == "DEVANAGARI"
    assert scripts["పరిశోధన"] == "TELUGU"


def test_rolling_hash_deterministic_and_sliding():
    # 1. Determinism
    h1 = fnv1a_64("algorithm")
    h2 = fnv1a_64("algorithm")
    assert h1 == h2
    assert isinstance(h1, int)
    assert h1 != fnv1a_64("different")

    # 2. Sliding matches direct computation for all positions
    tokens = ["the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"]
    token_hashes = [fnv1a_64(t) for t in tokens]
    k = 4
    rh = RollingHash(token_hashes, k=k)
    sliding_hashes = rh.compute_all()

    assert len(sliding_hashes) == len(tokens) - k + 1
    for start_idx, h_val in sliding_hashes:
        expected = compute_kgram_hash(token_hashes[start_idx : start_idx + k])
        assert h_val == expected, f"Mismatch at start_idx {start_idx}"


def test_winnowing_guarantee_and_determinism():
    tokenizer = LexicalTokenizer()
    engine = WinnowingEngine(k=25, w=16)
    assert engine.t == 40  # Guarantee threshold t = 25 + 16 - 1

    # Base text with > 40 tokens
    words = [f"word{i}" for i in range(50)]
    text_shared = " ".join(words)
    doc_a = f"Introduction. {text_shared} Conclusion."
    doc_b = f"Different header. {text_shared} Epilogue."

    tokens_a = tokenizer.tokenize(doc_a)
    tokens_b = tokenizer.tokenize(doc_b)

    fps_a = engine.fingerprint_tokens(tokens_a)
    fps_b = engine.fingerprint_tokens(tokens_b)

    assert len(fps_a) > 0
    assert len(fps_b) > 0

    hashes_a = {fp.hash_val for fp in fps_a}
    hashes_b = {fp.hash_val for fp in fps_b}
    shared = hashes_a.intersection(hashes_b)

    # Theoretical guarantee: since verbatim match length >= 40 tokens, at least 1 fingerprint MUST match!
    assert len(shared) >= 1, "Winnowing guarantee failed to capture verbatim sequence >= 40 tokens"


def test_winnowing_short_text_fallback():
    tokenizer = LexicalTokenizer()
    engine = WinnowingEngine(k=25, w=16)

    # Document with only 10 tokens (less than k=25)
    short_text = "This is a short academic excerpt that has few words."
    tokens = tokenizer.tokenize(short_text)
    assert len(tokens) == 10

    fps = engine.fingerprint_tokens(tokens)
    assert len(fps) == 1
    assert fps[0].is_short_fallback is True
    assert fps[0].token_start == 0
    assert fps[0].token_end == 10


def test_bm25_scoring_and_ranking():
    bm25 = BM25Index(k1=1.2, b=0.75)

    doc1 = ["plagiarism", "detection", "using", "winnowing", "fingerprints"]
    doc2 = ["machine", "learning", "neural", "networks", "classification"]
    doc3 = ["hybrid", "plagiarism", "detection", "in", "multilingual", "documents"]

    bm25.add_document("doc1", doc1)
    bm25.add_document("doc2", doc2)
    bm25.add_document("doc3", doc3)

    assert bm25.total_docs == 3
    assert bm25.avg_doc_length == pytest.approx(5.333, rel=1e-2)

    # Query with plagiarism terms
    query = ["plagiarism", "detection", "framework"]
    rankings = bm25.rank_candidates(query, top_k=3)

    assert len(rankings) == 2
    top_doc_id, top_score = rankings[0]
    assert top_doc_id in ["doc1", "doc3"]
    assert top_score > 0.0
    # doc2 contains none of the query terms and must not be ranked
    ranked_ids = [doc_id for doc_id, _ in rankings]
    assert "doc2" not in ranked_ids


def test_passage_aligner_exact_and_multilingual():
    tokenizer = LexicalTokenizer()
    aligner = PassageAligner(min_token_match=5, min_char_length=20, max_merge_gap=4)

    # Copied paragraph in English and Hindi separated by a long distinct gap
    shared_text = "This research demonstrates that hybrid architectures significantly reduce false positives in plagiarism detection."
    shared_hindi = "इस शोध पत्र में साहित्यिक चोरी का सटीक विश्लेषण प्रस्तुत किया गया है।"

    gap_sub = "A completely different and elaborate methodology discussion that spans many sentences to keep findings cleanly separated."
    gap_ref = "An entirely divergent historical background analysis exploring various ancient traditions and scholarly archival preservation."

    sub_raw = f"Initial chapter. {shared_text} {gap_sub} {shared_hindi} Final notes."
    ref_raw = f"Prior publication. {shared_text} {gap_ref} {shared_hindi} References."

    sub_tokens = tokenizer.tokenize(sub_raw)
    ref_tokens = tokenizer.tokenize(ref_raw)

    findings = aligner.align_documents(
        submission_id="sub-1",
        submission_raw_text=sub_raw,
        submission_tokens=sub_tokens,
        reference_id="ref-1",
        reference_title="Published Work",
        reference_raw_text=ref_raw,
        reference_tokens=ref_tokens,
    )

    assert len(findings) >= 2
    # Verify offset invariant for all findings
    for f in findings:
        sub_slice = sub_raw[f.submission_start_offset : f.submission_end_offset]
        ref_slice = ref_raw[f.reference_start_offset : f.reference_end_offset]
        assert sub_slice == f.submission_excerpt
        assert ref_slice == f.reference_excerpt
        assert f.category == "exact_copy"
        assert f.confidence in ["high", "moderate"]


def test_coverage_calculator_intervals_and_bounds():
    calc = CoverageCalculator()

    # Test merge_token_intervals
    intervals = [(0, 10), (5, 15), (20, 30), (25, 35)]
    merged = merge_token_intervals(intervals)
    assert merged == [(0, 15), (20, 35)]

    # Test 100% coverage
    tokenizer = LexicalTokenizer()
    aligner = PassageAligner(min_token_match=5)
    identical_text = "An identical document that has exactly the same words in the same order."
    tokens = tokenizer.tokenize(identical_text)

    findings = aligner.align_documents(
        "sub-id", identical_text, tokens,
        "ref-id", "Ref Title", identical_text, tokens
    )
    assert len(findings) == 1

    cov, sources = calc.calculate(len(tokens), findings)
    assert cov == 100.0
    assert len(sources) == 1
    assert sources[0].lexical_coverage_percent == 100.0

    # Test empty document / 0 findings
    cov_empty, sources_empty = calc.calculate(0, [])
    assert cov_empty == 0.0
    assert sources_empty == []
