# Algorithm Verification and Unit Test Execution Guide

This guide contains the exact commands to execute unit tests verifying each algorithm in native Windows terminal, along with the expected passing outputs.

**Working Directory:**
```powershell
cd "C:\Users\vaibh\OneDrive\Documents\plagarism engine"
```

---

## 1. Fast Lexical Algorithm Suite (Takes ~0.05s)
Tests FNV-1a hashing, Rolling Hash sliding correctness, Winnowing guarantee ($k=25, w=16$), short text fallback, BM25 scoring, Passage Aligner, and Interval Union Coverage calculation.

**Command:**
```powershell
apps\backend\.venv\Scripts\python.exe -m pytest apps/backend/tests/test_lexical_algorithms.py -v
```

**Verified Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
collected 7 items

apps\backend\tests\test_lexical_algorithms.py::test_tokenizer_offsets_and_multilingual PASSED [ 14%]
apps\backend\tests\test_lexical_algorithms.py::test_rolling_hash_deterministic_and_sliding PASSED [ 28%]
apps\backend\tests\test_lexical_algorithms.py::test_winnowing_guarantee_and_determinism PASSED [ 42%]
apps\backend\tests\test_lexical_algorithms.py::test_winnowing_short_text_fallback PASSED [ 57%]
apps\backend\tests\test_lexical_algorithms.py::test_bm25_scoring_and_ranking PASSED [ 71%]
apps\backend\tests\test_lexical_algorithms.py::test_passage_aligner_exact_and_multilingual PASSED [ 85%]
apps\backend\tests\test_lexical_algorithms.py::test_coverage_calculator_intervals_and_bounds PASSED [100%]

============================== 7 passed in 0.04s ==============================
```

---

## 2. Multilingual Semantic & AI Model Suite (Takes ~20s)
Tests Multilingual E5 embedding generation, 384-dimensional normalization, query/passage prefixing, Model-Aware Indic segmentation, SQLite vector repository cosine search, semantic matcher hard-negative filtering, and hybrid union scoring.

**Command:**
```powershell
apps\backend\.venv\Scripts\python.exe -m pytest apps/backend/tests/test_phase4_semantic.py -v
```

**Verified Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
collected 11 items

apps\backend\tests\test_phase4_semantic.py::test_provider_embedding_dimensions_and_normalization PASSED [  9%]
apps\backend\tests\test_phase4_semantic.py::test_provider_prefix_handling_and_determinism PASSED [ 18%]
apps\backend\tests\test_phase4_semantic.py::test_provider_empty_input PASSED [ 27%]
apps\backend\tests\test_phase4_semantic.py::test_provider_model_info PASSED [ 36%]
apps\backend\tests\test_phase4_semantic.py::test_model_aware_segmenter_token_budget PASSED [ 45%]
apps\backend\tests\test_phase4_semantic.py::test_model_aware_segmenter_multilingual_indic PASSED [ 54%]
apps\backend\tests\test_phase4_semantic.py::test_sqlite_vector_repository_crud_and_search PASSED [ 63%]
apps\backend\tests\test_phase4_semantic.py::test_semantic_matcher_multilingual_and_hard_negatives PASSED [ 72%]
apps\backend\tests\test_phase4_semantic.py::test_hybrid_analysis_modes_and_union_coverage PASSED [ 81%]
apps\backend\tests\test_phase4_semantic.py::test_api_analyses_models_info PASSED [ 90%]
apps\backend\tests\test_phase4_semantic.py::test_api_create_analysis_with_detection_mode PASSED [100%]

======================= 11 passed, 1 warning in 20.27s ========================
```

---

## 3. Human Reviewer Decisions & PDF Report Suite (Takes ~10s)
Tests review decision persistence, reviewer-adjusted coverage recomputation, HTML report generation, and dual-engine PDF export.

**Command:**
```powershell
apps\backend\.venv\Scripts\python.exe -m pytest apps/backend/tests/test_phase6_review_and_reports.py -v
```

---

## 4. Full Backend Verification (108 Tests Total)
Runs the complete test suite spanning all phases.

**Command:**
```powershell
apps\backend\.venv\Scripts\python.exe -m pytest apps/backend/tests/ -q
```

**Expected Result:**
```
108 passed in ~35s
```
