# Phase 2 to Phase 3 — Technical Handoff Document

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**From:** Phase 2 (Document Ingestion, Text Extraction, Multilingual Preprocessing, and Reference Collection Management)  
**To:** Phase 3 (Lexical Matching, Fingerprinting, and Candidate Retrieval)  
**Status:** READY FOR HANDOFF  

---

## 1. Handoff Readiness & Preconditions

Phase 2 provides a fully verified, operational foundation for the lexical detection engine to be built in Phase 3. All necessary preconditions have been satisfied:

1. **Document Parsing & Text Extraction:** Reliable extraction for `.txt`, `.pdf`, and `.docx` is complete and verified.
2. **Deterministic Passage Segmentation:** Every document is segmented into sequential passages with exact start and end code-point offsets into raw unnormalized text.
3. **Multilingual Unicode Normalization:** Unbroken Indic combining vowel signs (matras, viramas) and script classification (`en`, `hi`, `te`, `mixed`) ensure consistent lexical representations.
4. **Reference Collections:** Researchers can assemble reference documents into named corpora for candidate comparison.
5. **Comparison Pre-Flight Validation:** Validation contracts for Direct (1:1), One-to-Many (1:N), and Corpus (1:Collection) comparisons are established.

---

## 2. Artifacts & Interfaces Consumed by Phase 3

### 2.1 Passages Schema & Access API
Phase 3 lexical algorithms will ingest passage records produced by Phase 2:
```python
# Available via LocalMetadataRepository or GET /api/v1/documents/{id}/passages
{
    "passage_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "document_id": "e6261a67-77b5-4fbd-95cb-389c301aa74a",
    "chunk_index": 0,
    "start_char": 0,
    "end_char": 497,
    "start_utf16": 0,
    "end_utf16": 497,
    "text": "A Comparative Study on Hybrid Plagiarism Detection...",
    "token_count": 61
}
```

### 2.2 Comparison Validation Interface
Phase 3 will upgrade the currently validated comparison setups (`/api/v1/comparisons/validate`) into active analysis jobs:
- `POST /api/v1/analyses`: Initiates candidate retrieval and lexical comparison pipeline.
- Comparison modes:
  - `direct`: 1 submission vs 1 reference document.
  - `one_to_many`: 1 submission vs N reference documents.
  - `corpus`: 1 submission vs an entire reference collection.

---

## 3. Phase 3 Implementation Directives

### 3.1 Winnowing Algorithm Specification
- Character k-gram size: $k = 25$ characters.
- Window size: $w = 16$ consecutive k-gram hashes.
- Match guarantee: $t = k + w - 1 = 40$ characters. Any verbatim substring match of length $\ge 40$ characters is mathematically guaranteed to share at least one selected fingerprint.
- Hash Function: 64-bit non-cryptographic rolling hash (e.g. Rabin-Karp or MurmurHash3) or SHA-256 truncated.
- Tie-breaking: Select the rightmost minimum hash in the window.

### 3.2 BM25 Retrieval Engine
- Inverted index built across passage tokens for fast candidate filtering in One-to-Many and Corpus modes.
- Tuning parameters: $k_1 = 1.2$, $b = 0.75$.
- Language-specific tokenization and stopword filtering for English, Hindi, and Telugu.

### 3.3 New Database Tables for Phase 3
In `storage/local_db.py` (and corresponding PostgreSQL schema in Phase 7):
- `fingerprints`: `(document_id, passage_id, hash_val, start_char, end_char)`
- `analyses`: Analysis job state (`queued`, `processing`, `completed`, `failed`), comparison mode, parameters.
- `lexical_matches`: Matching intervals between submission and reference passages with similarity metrics.

---

## 4. Operational Transition Check

To begin Phase 3 development:
1. Ensure both development servers are running (`scripts/run_local.ps1`).
2. Run `scripts/run_tests.ps1` to confirm all 171 existing checks pass before introducing Phase 3 changes.
3. Retain the existing local SQLite repository and filesystem store.
