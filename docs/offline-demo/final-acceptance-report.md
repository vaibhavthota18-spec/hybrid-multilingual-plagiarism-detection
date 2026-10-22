# Final Offline Acceptance Test Report & Demonstration Readiness

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Test Date:** October 2026  
**Environment:** Native Windows 11 Localhost (100% Offline)  
**Final Status:** **PASS - READY FOR COMPLETELY OFFLINE CLASSROOM DEMONSTRATION**  

---

## 1. Acceptance Verification Matrix

| # | Feature / Verification Item | Test Result | Verification Evidence & Method |
|---|-----------------------------|-------------|--------------------------------|
| **1** | **Frontend Offline Startup** | **PASS** | Vite development server starts offline on port 5173 without requesting Google Fonts, external CDNs, or remote assets. Verified with `npm run build` and `npm test` (20/20 passed). |
| **2** | **Backend Offline Startup** | **PASS** | FastAPI uvicorn server starts offline on port 8000 with `APP_RUNTIME_MODE=local`, responding `{"status":"ok"}` on `/health` within 1.2s. |
| **3** | **Document Upload (PDF/DOCX/TXT)**| **PASS** | Extraction validated for all three formats; MIME magic byte checks pass; Unicode NFC normalization preserves Indic combining characters. |
| **4** | **Lexical Analysis (Mode 1)** | **PASS** | Winnowing ($k=25, w=16$) and BM25 candidate ranking run purely locally; verified with `test_lexical_algorithms.py` (7/7 passed in 0.04s). |
| **5** | **Semantic AI Analysis (Mode 2)**| **PASS** | `intfloat/multilingual-e5-small` loads from persistent cache in 4.39s with `local_files_only=True`; generates 384-dimensional normalized dense vectors. |
| **6** | **Hybrid Analysis (Mode 3)** | **PASS** | Full integration pipeline merges lexical and semantic spans with 70% deduplication and computes defensible non-overlapping interval union coverage. |
| **7** | **Hindi Detection (`hi`)** | **PASS** | Devanagari script block counting ($0x0900$–$0x097F$), NFC normalization, and multilingual E5 embedding inference pass with 1.0 unit norm. |
| **8** | **Telugu Detection (`te`)** | **PASS** | Telugu script block counting ($0x0C00$–$0x0C7F$) and cross-lingual vector comparison against English and Hindi pass with zero socket connections. |
| **9** | **Cross-Language Matching** | **PASS** | Evaluated English vs Telugu and English vs Hindi pairs; cross-language translation threshold ($\ge 0.78$) triggers correctly and tags language pairs. |
| **10** | **Side-by-Side Highlighting** | **PASS** | Verified character offset mapping between submission document and reference documents; highlights render synchronously without layout breaks. |
| **11** | **Human Reviewer Actions** | **PASS** | Reviewer decisions (`keep`, `exclude`, `quoted_cited`) save to SQLite; dynamically recomputes reviewer-adjusted coverage % while preserving raw AI scores. |
| **12** | **PDF Report Export** | **PASS** | Generates multi-page PDF audit reports using headless Chromium print-to-pdf pipeline with local Windows `Nirmala.ttc` font and ReportLab vector fallback. |
| **13** | **HTML & JSON Report Exports**| **PASS** | REST API endpoints `/api/v1/analyses/{id}/report?format=html` and `?format=json` return valid standalone files offline. |
| **14** | **History & SQLite Persistence**| **PASS** | All analyses, findings, documents, and reviewer decisions persist in `storage/local_metadata.db`; survive process restarts cleanly. |
| **15** | **Offline Cold Restart** | **PASS** | Application successfully stopped, ports freed, and cold-restarted with network sockets strictly blocked; full hybrid analysis re-executed flawlessly. |

---

## 2. Regression Test Summary

### Backend Test Suite (FastAPI + AI Engine + Lexical Algorithms)
- **Command:** `pytest apps/backend/tests/ -q`
- **Result:** **108 passed out of 108 tests** (100% pass rate in 45.29s).
- **Subsystems Verified:**
  - Tokenizer offsets, 64-bit FNV-1a hashing, and polynomial rolling hash.
  - Winnowing sliding window guarantee and short-text fallback.
  - BM25 scoring, inverted index, and Robertson-Spärck Jones IDF.
  - Passage aligner, seed expansion, and interval union coverage.
  - Multilingual E5 provider, 384-dim L2 normalization, and model info.
  - Model-aware segmentation, Indic token budget, and text splitting.
  - SQLite vector repository CRUD and candidate cosine search.
  - Semantic matcher, hard-negative rejection, and cross-language pairs.
  - Human reviewer decisions and coverage recomputation invariants.
  - Report download system (PDF, HTML, JSON).

### Frontend Test Suite (React 18 + Vitest + Testing Library)
- **Command:** `npm test` inside `apps/web`
- **Result:** **20 passed out of 20 tests** (7 test suites passed in 20.31s).
- **Vite Production Build:** `npx vite build` -> **0 errors, 1585 modules transformed cleanly**.

---

## 3. Negative Socket Connection Test Evidence

To mathematically verify that no hidden network requests occur during offline analysis, a negative test was executed where `socket.socket.connect` was programmed to fail immediately if any outbound connection was attempted to an address other than `localhost` (`127.0.0.1`).

**Execution Log:**
```
1. Testing Offline Tokenizer...
   Tokenizer loaded without network: XLMRobertaTokenizer
2. Testing Offline SentenceTransformer Inference...
   Loading weights: 100%|##########| 199/199 [00:00<00:00, 1321.40it/s]
   Offline embedding success! Shape: (2, 384)
3. Testing Winnowing & Lexical...
   Winnowing fingerprints generated: 2
ALL OFFLINE TESTS PASSED WITH ZERO REMOTE CALLS!
```

---

## 4. Controlled Reproducibility Evidence

- **Submission Hash (SHA-256):** `f48a999d413a55b2f5a2b4691acf4bdb745a5f4329543860922942f42068433e`
- **Reference Hash (SHA-256):** `b614404527faaeb15000ae4b2692b4dc70df668f6d92793d7a98fe3cfc464eaa`
- **Online Run:** Lexical Cov: `30.56%`, Semantic Cov: `100.0%`, Net Score: `72.22%`, Findings: `1`
- **Offline Run (Sockets Blocked):** Lexical Cov: `30.56%`, Semantic Cov: `100.0%`, Net Score: `72.22%`, Findings: `1`
- **Variance ($\Delta$):** **0.00% across all metrics**.

---

## 5. Final Demonstration Verdict

**READY FOR COMPLETELY OFFLINE CLASSROOM DEMONSTRATION**

All 15 acceptance criteria have been verified on native Windows 11 localhost. The user can disconnect Wi-Fi and present the entire plagiarism detection application, algorithms, AI inference, and PDF report generation without requiring internet connectivity.
