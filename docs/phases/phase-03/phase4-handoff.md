# Phase 4 Handoff Specification: Semantic Analysis & Multilingual AI

## 1. Executive Summary & Transition Context

Phase 3 establishes the complete lexical detection tier, source alignment engine, SQLite relational persistence, and interactive side-by-side Results Dashboard.

Phase 4 will build directly upon this foundation to introduce **Semantic Plagiarism Detection, Dense Vector Embeddings (Multilingual E5), and Cross-Lingual Alignment**.

---

## 2. Interface Contracts for Phase 4

### 1. Hybrid Score Formulation (ADR-0003)
Phase 4 will combine Phase 3's lexical coverage with semantic dense cosine similarity:

$$\text{Score}_{\text{hybrid}} = w_{\text{lex}} \cdot \text{Score}_{\text{lexical}} + w_{\text{sem}} \cdot \text{Score}_{\text{semantic}}$$

where:
- $\text{Score}_{\text{lexical}}$: Non-overlapping lexical coverage percentage computed by `CoverageCalculator` (established in Phase 3).
- $\text{Score}_{\text{semantic}}$: Dense embedding cosine similarity computed across passage chunks using Multilingual E5.
- $w_{\text{lex}} = 0.40, w_{\text{sem}} = 0.60$ (default institutional weighting).

### 2. Relational Schema Handoff
Phase 3's database schema already defines the semantic columns required for Phase 4:
- In `analyses`:
  - `overall_semantic_coverage_percent`: Populated with 0.0 in Phase 3; will hold semantic coverage in Phase 4.
  - `net_adjusted_score_percent`: Currently mirrors lexical coverage; will hold the hybrid weighted score in Phase 4.
- In `analysis_findings`:
  - `category`: Currently emits `exact_copy` and `near_exact_rewrite`; Phase 4 will emit `paraphrase` and `potential_translation`.
  - `semantic_similarity`: Populated with 0.0 in Phase 3; will store dense vector cosine similarity in Phase 4.
- In `analysis_sources`:
  - `semantic_coverage_percent`: Populated with 0.0 in Phase 3; will store per-source semantic contribution in Phase 4.

### 3. Vector Embedding Storage
The PostgreSQL production schema (`infra/docker/init-db/01-init.sql`) defines `embedding VECTOR(1024)` on `document_passages`.
In Phase 4, passage embeddings will be generated locally via `intfloat/multilingual-e5-base` or `intfloat/multilingual-e5-small` using ONNX Runtime or PyTorch CPU, with an in-memory cosine index adapter for localhost development.

---

## 3. Strict Boundary Rules for Phase 4

1. **Preserve Phase 3 Lexical Engine**: Do NOT alter the Winnowing algorithm ($k=25, w=16$), rolling hash, or BM25 indexer.
2. **Preserve Evidence Transparency**: Verbatim highlighted text spans must remain visible alongside semantic matches.
3. **Preserve Determinism**: Lexical scores must remain 100% reproducible regardless of AI model temperature or device backend.
4. **Preserve Local Execution**: Semantic embeddings must run locally on Windows 11 CPU without requiring external paid APIs or cloud GPU instances.
