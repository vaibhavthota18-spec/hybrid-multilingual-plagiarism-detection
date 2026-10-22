# Phase 3 Implementation Plan: Lexical Plagiarism Detection Engine

## 1. Executive Summary & Objectives

Phase 3 transitions the platform from document ingestion and text segmentation (established in Phase 2) to genuine, deterministic lexical plagiarism detection. The primary objective is to implement a production-grade, mathematically sound lexical comparison engine that operates autonomously on local Windows 11 hardware without cloud dependencies, external paid APIs, or virtualized infrastructure.

### Core Objectives:
1. **Deterministic Lexical Tokenization & Fingerprinting**: Implement high-throughput Unicode-aware tokenization with exact code-point and UTF-16 code-unit tracking for English, Hindi (Devanagari), and Telugu scripts.
2. **Winnowing Algorithm Implementation**: Deliver deterministic character/token-level winnowing ($k=25, w=16$, guarantee threshold $t=40$ tokens) using polynomial rolling hashes ($B=313, M=2^{61}-1$) with zero dependence on Python's randomized `hash()`.
3. **BM25 Candidate Retrieval**: Implement Okapi BM25 ($k_1=1.2, b=0.75$) with inverse document frequency indexing for scalable pre-filtering in corpus comparison mode.
4. **Passage Alignment & Evidence Verification**: Implement fine-grained passage alignment that expands exact anchor matches, merges adjacent matches within 4 tokens, classifies matches into exact copy versus near-exact rewrite, and strictly verifies offsets against original raw text.
5. **Non-Overlapping Coverage Scoring**: Compute true lexical coverage as the union of non-overlapping matched token intervals over total submission tokens, bounded strictly in $[0.0\%, 100.0\%]$.
6. **Dual Persistence Architecture**: Extend the SQLite local repository with relational tables for document fingerprints, analyses, findings, and matched source breakdowns.
7. **Interactive Results Dashboard**: Provide a dual-pane, side-by-side highlighted text comparison UI in React/TypeScript with zero XSS vulnerabilities (rendering disjoint spans as React nodes without `dangerouslySetInnerHTML`).

---

## 2. Architecture & Pipeline Stages

The Lexical Plagiarism Engine executes as a deterministic, multi-stage processing pipeline:

```
[Candidate Submission + Reference(s)]
                │
                ▼
   Stage 1: Tokenization & Offset Mapping (English, Hindi, Telugu)
                │
                ▼
   Stage 2: Deterministic Rolling Hash (FNV-1a + Polynomial Modulo 2^61 - 1)
                │
                ▼
   Stage 3: Winnowing Window Minimization (k=25, w=16, Monotonic Deque)
                │
                ▼
   Stage 4: Candidate Retrieval & Pre-filtering (BM25Okapi Ranking)
                │
                ▼
   Stage 5: Fine-Grained Passage Alignment & Anchor Extension
                │
                ▼
   Stage 6: Verbatim Slicing & Offset Cross-Check
                │
                ▼
   Stage 7: Union-Based Lexical Coverage Calculation
                │
                ▼
   Stage 8: Relational Persistence (SQLite: analyses, findings, sources)
                │
                ▼
   Stage 9: REST API Response & React Results Dashboard
```

---

## 3. Algorithmic Parameter Specifications

| Parameter | Value | Justification |
| :--- | :--- | :--- |
| **K-Gram Size ($k$)** | 25 tokens | Long enough to prevent coincidental phrase collisions; short enough to detect copied sub-sentences. |
| **Window Size ($w$)** | 16 hashes | Yields a guaranteed detection threshold $t = k + w - 1 = 40$ tokens (~200–260 characters). |
| **Hash Modulus ($M$)** | $2^{61} - 1$ | 9th Mersenne prime; guarantees collision resistance across large corpus fingerprint stores. |
| **Polynomial Base ($B$)** | 313 | Prime base larger than typical ASCII/extended alphabetic token counts. |
| **BM25 $k_1$** | 1.2 | Standard term frequency saturation constant for academic text retrieval. |
| **BM25 $b$** | 0.75 | Standard document length normalization penalty. |
| **Max Merge Gap** | 4 tokens | Connects fragmented verbatim sequences separated by minor connective words or punctuation. |
| **Min Match Length** | 6 tokens | Minimum threshold for fine-grained aligned match findings to prevent noise. |

---

## 4. Work Breakdown & Milestones

1. **Milestone 3.1: Algorithmic Core (`services/lexical/`)**
   - Tokenizer with Unicode offset mapper (`tokenizer.py`)
   - 64-bit FNV-1a & polynomial rolling hash (`rolling_hash.py`)
   - Monotonic deque sliding-window Winnowing engine (`winnowing.py`)
   - In-memory BM25 Okapi indexer (`bm25.py`)
   - Span alignment & boundary expander (`aligner.py`)
   - Interval-union coverage calculator (`coverage.py`)

2. **Milestone 3.2: Storage & Repository (`storage/local_db.py`)**
   - DDL migration for `document_fingerprints`, `analyses`, `analysis_findings`, `analysis_sources`.
   - Reconcile interrupted jobs on server restart.
   - Cascading deletion for analyses and evidence records.

3. **Milestone 3.3: REST Endpoints & Orchestration (`api/v1/analyses.py`)**
   - `POST /analyses`: Synchronous or background dispatch via bounded thread pool.
   - `GET /analyses/{id}`: Detailed inspection model with findings and source breakdowns.
   - `GET /analyses`: History listing with pagination and search.
   - `DELETE /analyses/{id}`: Cascade cleanup.
   - `GET /analyses/{id}/report`: Formatted audit report.

4. **Milestone 3.4: React Frontend UI (`apps/web/`)**
   - Live Results Dashboard (`ResultsDashboardPage.tsx`) with side-by-side synchronized view.
   - Analysis History Page (`AnalysisHistoryPage.tsx`) with quick-run modal and filters.
   - Comparison Setup activation in `IngestionPage.tsx`.

5. **Milestone 3.5: Comprehensive Quality Assurance & Acceptance**
   - Algorithm unit tests (7 tests).
   - API integration tests (5 tests).
   - Frontend Vitest suite (19 tests).
   - Production Vite bundle build.
   - End-to-end acceptance script (`verify_phase3_e2e.py`) validating scenarios A–J.
