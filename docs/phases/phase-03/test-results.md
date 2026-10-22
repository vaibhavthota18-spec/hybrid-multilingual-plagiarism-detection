# Automated Test Results and Verification Evidence

## 1. Test Suite Summary

All tests executed natively on Windows 11 using PowerShell, Python 3.12, and Node.js v22.

| Stage | Test Suite | Scope | Passed | Failed | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1/6** | `validate_contract.ps1` | OpenAPI 3.1.0 Contract Verification | 10 | 0 | **PASS** |
| **2/6** | `validate_phase0.ps1` | Phase 0 Document Architecture Consistency | 57 | 0 | **PASS** |
| **3/6** | `pytest` (Backend) | Unit, Contract, Security, Algorithm & API Tests | 79 | 0 | **PASS** |
| **4/6** | `vitest` + `tsc` (Web) | TypeScript Typecheck + React Component Tests | 19 | 0 | **PASS** |
| **4/6** | `vite build` (Web) | Frontend Production Asset Compilation | 1585 mod | 0 | **PASS** |
| **5/6** | `verify_phase2_e2e.py` | Phase 2 Document Ingestion Acceptance (24 steps) | 24 | 0 | **PASS** |
| **6/6** | `verify_phase3_e2e.py` | Phase 3 Lexical Engine Acceptance (Scenarios A–J) | 10 | 0 | **PASS** |
| **Total** | **Comprehensive Full-Stack** | **Complete System Acceptance** | **199** | **0** | **100% PASS** |

---

## 2. Phase 3 Algorithmic Unit Tests (`test_lexical_algorithms.py`)

- `test_tokenizer_offsets_and_multilingual`: Validates tokenization, word boundaries, code-point offsets, and UTF-16 surrogate calculations for English, Hindi, and Telugu.
- `test_rolling_hash_deterministic_and_sliding`: Validates that polynomial rolling hash computes in $O(1)$ and matches batch computation across 10,000 randomized tokens.
- `test_winnowing_guarantee_and_determinism`: Validates $k=25, w=16$, guarantee threshold $t=40$, and rightmost minimum tie-breaking rule.
- `test_winnowing_short_text_fallback`: Validates that documents with $< 25$ tokens generate fallback fingerprints rather than crashing.
- `test_bm25_scoring_and_ranking`: Validates Okapi BM25 scoring, term saturation ($k_1=1.2$), and document length normalization ($b=0.75$).
- `test_passage_aligner_exact_and_multilingual`: Validates anchor extension, gap bridging ($\le 4$ tokens), and classification.
- `test_coverage_calculator_intervals_and_bounds`: Validates non-overlapping interval union, deduplication, and mathematical bounds $[0.0\%, 100.0\%]$.

---

## 3. Phase 3 API Integration Tests (`test_phase3_api.py`)

- `test_analysis_direct_mode_exact_copy`: Creates two identical documents; runs direct analysis; verifies $100\%$ coverage and `exact_copy` classification.
- `test_analysis_unrelated_documents_zero_coverage`: Compares unrelated texts; verifies $0.0\%$ similarity and zero findings.
- `test_analysis_one_to_many_and_corpus_mode`: Evaluates composite document against multiple references and a collection.
- `test_analysis_multilingual_hindi_and_telugu`: Validates Devanagari and Telugu verbatim matches and code-point integrity.
- `test_analyses_list_status_and_report_endpoints`: Validates `/analyses`, `/analyses/{id}/status`, `/analyses/{id}/report`, and `/analyses/{id}` delete cascading.

---

## 4. Phase 3 End-to-End Acceptance Scenarios (`verify_phase3_e2e.py`)

- **Scenario A (Identical Comparison)**: Identical document yields $100.0\%$ lexical coverage. **PASS**
- **Scenario B (Partial Copy)**: Partial copy localized with exact character boundaries ($50.0\%$ coverage). **PASS**
- **Scenario C (Unrelated Documents)**: Unrelated texts produce $0.0\%$ coverage and zero false findings. **PASS**
- **Scenario D (Multiple References)**: 1:N comparison matches two separate reference sources ($67.39\%$ coverage). **PASS**
- **Scenario E (Corpus Retrieval)**: BM25 retrieves target microservices text from among collection filler. **PASS**
- **Scenario F (Hindi Matching)**: Devanagari script matched with $100.0\%$ coverage. **PASS**
- **Scenario G (Telugu Matching)**: Telugu script matched with $100.0\%$ coverage. **PASS**
- **Scenario H (SQLite Durability)**: Analysis records and findings survive fresh repository connection across restart. **PASS**
- **Scenario I (Cascade Deletion)**: Deleting analysis removes findings and sources, returning HTTP 404. **PASS**
- **Scenario J (Phase Boundary Integrity)**: Semantic coverage is strictly $0.0\%$; net adjusted score equals lexical coverage. **PASS**
