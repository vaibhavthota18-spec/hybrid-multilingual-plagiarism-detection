# Evaluation Metrics, Provisional Targets & Acceptance Gates

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Target Execution Phase:** Phase 5 (Multilingual Evaluation)  
> **Date:** October 2026  

---

## 1. Status Notice: Targets vs. Achieved Results

> **CRITICAL TRANSPARENCY NOTICE:**  
> The metrics listed in this document represent **provisional engineering target thresholds** and acceptance criteria established during Phase 0 architecture planning. They are **NOT** claimed as achieved experimental results. Actual performance metrics will be measured, recorded, and certified exclusively upon execution of the Phase 5 benchmark suite.

---

## 2. Core Detection & Retrieval Acceptance Targets

| Metric | Provisional Target | Evaluation Split | Architectural Significance |
|---|---|---|---|
| **High-Confidence Exact-Copy Precision** | $\ge 95.0\%$ | Test (Verbatim) | Ensures false accusations do not occur when flagging verbatim copying. |
| **Exact / Near-Exact Recall** | $\ge 85.0\%$ | Test (Verbatim/Rewrite) | Minimizes undetected verbatim and lightly edited copying. |
| **Mean Matching-Span IoU** | $\ge 0.80$ | Test (Alignment) | Evaluates token-level boundary alignment accuracy against human gold spans. |
| **Source Recall@20 (Monolingual)** | $\ge 90.0\%$ | Test (EN-EN, HI-HI, TE-TE) | Measures Stage 1 retrieval ability to include the true source in top-20 candidates. |
| **Cross-Language Recall@20** | $\ge 80.0\%$ | Test (EN-HI, EN-TE, HI-TE) | Measures Stage 1 retrieval across translation pairs. |
| **Paraphrase Detection F1** | $\ge 0.75$ | Test (Paraphrase) | Balances precision and recall on semantic paraphrases. |
| **Hard-Negative False-Positive Rate** | $\le 5.0\%$ | Test (Hard Negatives) | Protects against false alarms on standard definitions and topical similarities. |
| **Highlight Accuracy on Eligible Fixtures** | $\ge 99.0\%$ | Verification Suite | Verifies that rendered character highlights match underlying code points. |
| **Optional HNSW Recall vs. Exact Search** | $\ge 98.0\%$ | Benchmark (Corpus) | Gate for enabling HNSW index optimization (ADR-0004). |

---

## 3. Latency & Resource Utilization Targets

### 3.1 10-Page Warmed Benchmark Specification
- **Hardware Profile:** 8 CPU cores (x86_64), 16 GB RAM, no GPU acceleration (CPU-only PyTorch inference).
- **Corpus Scale:** 1,000 indexed reference documents (approx. 25,000 passages).
- **Document Scale:** 10-page submission document (approx. 3,500 words / 45 passages).
- **Target Latency:**
  - **Median (p50):** $\le 90$ seconds.
  - **95th Percentile (p95):** $\le 180$ seconds.

### 3.2 Latency Accounting Boundaries
To ensure unambiguous profiling, latency measurement is strictly demarcated:
- **Included in Processing Time:**
  1. Reading raw document bytes from storage.
  2. PyMuPDF text extraction and Unicode NFC normalization.
  3. Passage segmentation and code-point offset indexing.
  4. Query fingerprint generation (Winnowing).
  5. Dense query embedding generation via Multilingual E5 (`CPU batched inference`).
  6. Stage 1 candidate retrieval (pgvector query + inverted index query).
  7. Candidate deduplication and fusion.
  8. Stage 2 token-level local sequence alignment.
  9. Deduplicated coverage calculation and finding persistence.
- **Excluded from Processing Time:**
  - Client-to-server network upload transfer time.
  - Redis task wait time in cases of external worker queue congestion.
  - Client-side browser DOM rendering and font loading.

---

## 4. Phase 5 Acceptance Criteria Gate

Phase 5 (Multilingual Evaluation) can be signed off if and only if:
1. Benchmark scripts run automatically and reproducibly via `evaluation/scripts/run_benchmarks.py`.
2. All 12 ablation experiments in `docs/05-evaluation/benchmark-plan.md` produce complete confusion matrices.
3. Actual achieved metrics meet or exceed the provisional targets above.
4. Separate performance scores are published for all six language pairs (including explicit verification of Telugu performance).
5. Zero data leakage between development, validation, and held-out test splits is verified by script assertions.
