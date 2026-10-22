# Algorithm Source Code Map

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Project Root:** `C:\Users\vaibh\OneDrive\Documents\plagarism engine`  
**Backend Directory:** `apps/backend/src/plagiarism/`  
**Frontend Directory:** `apps/web/src/`  

---

## 1. Core Algorithm Source Map

| # | Algorithm / Component | Exact Source File | Class / Function | Line Numbers | Purpose & Scientific Formula |
|---|------------------------|-------------------|------------------|--------------|------------------------------|
| **1** | **64-bit FNV-1a Token Hash** | `apps/backend/src/plagiarism/services/lexical/rolling_hash.py` | `fnv1a_64(token_str)` | `18–27` | Deterministic 64-bit hash: $H = (H \oplus b) \times \text{PRIME} \pmod{2^{64}}$. Process-independent, immune to Python hash randomization. |
| **2** | **Polynomial Rolling Hash** | `apps/backend/src/plagiarism/services/lexical/rolling_hash.py` | `RollingHash.compute_all()` | `45–105` | Sliding window hash over token $k$-grams in $O(1)$ time per token using Mersenne prime $M_{61} = 2^{61}-1$, base $313$. |
| **3** | **Winnowing Algorithm** | `apps/backend/src/plagiarism/services/lexical/winnowing.py` | `WinnowingEngine.fingerprint_tokens()` | `25–153` | Schleimer et al. (2003) algorithm ($k=25, w=16$, guarantee $t=40$). Monotonic deque implementation with rightmost tie-breaking (lines 116–153). |
| **4** | **Okapi BM25 Index & Retrieval** | `apps/backend/src/plagiarism/services/lexical/bm25.py` | `BM25Index.rank_candidates()`, `score_document()`, `idf()` | `12–104` | Lexical candidate ranking: $k_1 = 1.2$, $b = 0.75$. Probabilistic term relevance for candidate retrieval before deep alignment. |
| **5** | **Passage Alignment (Seed & Extend)** | `apps/backend/src/plagiarism/services/lexical/aligner.py` | `PassageAligner.align_documents()`, `_merge_adjacent_spans()` | `39–238` | Dynamic seed discovery (5-grams) with bidirectional token extension and gap-tolerant span consolidation. |
| **6** | **Interval Union Coverage** | `apps/backend/src/plagiarism/services/lexical/coverage.py` | `merge_token_intervals()`, `CoverageCalculator.calculate()` | `22–42`, `45–126` | Non-overlapping token union coverage: sorts and merges overlapping intervals $[s_i, e_i)$ to prevent double-counting. Strictly bounded $[0\%, 100\%]$. |
| **7** | **Multilingual E5 AI Embeddings** | `apps/backend/src/plagiarism/services/semantic/provider.py` | `LocalSentenceTransformerProvider` (`encode_queries()`, `encode_passages()`) | `42–173` | `intfloat/multilingual-e5-small` (384 dims, L2 normalized). Asymmetric prompt formatting: `query: ` and `passage: `. |
| **8** | **Cosine Similarity Vector Search** | `apps/backend/src/plagiarism/storage/vector_store.py` | `SQLiteVectorRepository.search_candidates()` & `PgVectorRepository` | `82–327`, `330–544` | Dense matrix multiplication $\mathbf{Q} \mathbf{R}^T$ via NumPy dot product (SQLite) or `<=>` cosine distance operator (PostgreSQL/pgvector). |
| **9** | **Semantic & Cross-Language Classification** | `apps/backend/src/plagiarism/services/semantic/matcher.py` | `SemanticMatcher.match_documents()` | `57–250` | Classifies matches into `exact`, `paraphrase`, and `cross_lingual` across English, Hindi, and Telugu with language pair metadata and confidence calibration. |
| **10** | **Hybrid Evidence Fusion & Scoring** | `apps/backend/src/plagiarism/services/hybrid_service.py` | `HybridAnalysisService._integrate_and_score()` | `288–473` | Deduplicates lexical and semantic spans (70% overlap threshold) and computes unified net score: $\text{Net} = 0.40 \cdot \text{Lexical} + 0.60 \cdot \text{Semantic}$ bounded by hybrid union. |
| **11** | **Human Reviewer Re-Scoring** | `apps/backend/src/plagiarism/services/hybrid_service.py` | `HybridAnalysisService.recompute_reviewer_adjusted_coverage()` | `475–552` | Mathematically dynamically recalculates net coverage after reviewer decisions (`keep`, `exclude`, `quoted_cited`) without altering raw model scores. |
| **12** | **Unicode NFC & Indic Normalization** | `apps/backend/src/plagiarism/services/preprocessing.py` | `identify_language()`, `normalize_text_nfc()`, `OffsetMapper` | `27–128` | Script block counting for Devanagari, Telugu, and Latin. NFC Unicode normalization while preserving Indic combining characters (matras, halants). |
| **13** | **Dual PDF Report Generation** | `apps/backend/src/plagiarism/services/reports/report_generator.py` | `ReportGenerator.generate_pdf_report()` & `_generate_pdf_reportlab()` | `691–753`, `756–970` | Headless Chromium print-to-pdf for Indic font shaping with ReportLab defensive vector fallback. |
| **14** | **Async Job Execution Engine** | `apps/backend/src/plagiarism/services/executor.py` | `LocalProcessingExecutor.submit_analysis()` | `20–220` | Dual-mode executor: bounded ThreadPoolExecutor on Windows localhost, Redis/RQ in production. |
| **15** | **Frontend Analysis Trigger & Polling** | `apps/web/src/pages/WorkflowPage.tsx` | `handleAnalyze()` | `221–258` | Initiates analysis job via REST API, polls progress with real-time stage updates, navigates to results dashboard. |
| **16** | **Interactive Results & Audit UI** | `apps/web/src/pages/ResultsDashboardPage.tsx` | `ResultsDashboardPage`, `handleDownloadReport()` | `37–861` | Side-by-side synchronized evidence highlighting, reviewer audit decision controls, multi-format report exports (PDF, HTML, JSON). |
