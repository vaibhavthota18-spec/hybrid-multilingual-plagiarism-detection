# Phase 4 Implementation Plan: Multilingual Semantic AI & Hybrid Plagiarism Detection

## 1. Executive Summary & Objective

Phase 4 introduces local, multilingual semantic similarity detection into the *Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System*. The primary objective is to transcend exact and near-exact lexical matching (established in Phase 3) by detecting sophisticated paraphrasing, idea restructuring, and cross-language translation plagiarism across **English**, **Hindi**, and **Telugu**, without relying on external cloud APIs, virtualization, or paid third-party infrastructure.

All components execute natively on Windows 11 localhost, maintaining strict compatibility with SQLite development persistence, private filesystem document storage, and existing Phase 0–3 contracts.

---

## 2. Engineering Team Roles & Responsibilities

| Role | Responsibility |
|---|---|
| **Principal AI/ML Engineer** | Model selection (`intfloat/multilingual-e5-small`), embedding provider architecture, prefix semantics (`query: `, `passage: `), and L2 normalization. |
| **Multilingual NLP Engineer** | Token sequence budget enforcement, sentence boundary segmentation preserving Unicode offsets across Devanagari and Telugu scripts. |
| **Vector Storage Architect** | Design of local IEEE 754 float32 binary BLOB vector storage in SQLite (`passage_embeddings`), maintaining abstraction boundaries for future pgvector migration. |
| **FastAPI Backend Engineer** | Implementation of `HybridAnalysisService`, `/analyses/models/info` endpoint, and orchestration of lexical, semantic, and hybrid detection modes. |
| **Information Retrieval Engineer** | Threshold calibration (0.82 for paraphrases, 0.80 for cross-lingual), confidence grading, and deduplication of overlapping lexical/semantic matches. |
| **React/TypeScript Developer** | Implementation of Detection Mode selector cards, 5 metric dashboard cards, and multilingual color-coded highlight overlays in UI. |
| **QA & Verification Engineer** | Authoring unit test suite (`test_phase4_semantic.py`), benchmark evaluation (`evaluate_phase4_model.py`), and 14-scenario E2E acceptance suite (`verify_phase4_e2e.py`). |

---

## 3. Scope Boundaries & Mandatory Constraints

1. **Native Localhost Execution Only**: No Docker containers, no WSL2 virtualization, no cloud services.
2. **Local Inference Independence**: Zero dependence on OpenAI, Anthropic, Google Cloud Translation, or external embedding endpoints.
3. **Preservation of Preceding Milestones**:
   - Phase 0: Requirements, threat models, and OpenAPI 3.1 contracts preserved.
   - Phase 1: Native Windows virtual environment and health probes maintained.
   - Phase 2: PDF, DOCX, TXT extractors and Unicode NFC preprocessing preserved.
   - Phase 3: Winnowing algorithm ($k=25, w=16$) and BM25Okapi candidate retrieval preserved.
4. **Future Compatibility (ADR-0004)**: Vector index interfaces (`VectorIndex`) designed to swap seamlessly to PostgreSQL `pgvector` upon container deployment.
5. **Phase Boundary Adherence**: Strictly concludes Phase 4 without initiating Phase 5 (citation attribution / authorship verification).

---

## 4. Key Milestones Completed

- [x] **Milestone 4.1: ML Environment & Local Model Caching** — Installed PyTorch CPU, HuggingFace transformers, and sentence-transformers; cached `intfloat/multilingual-e5-small` (~470.6 MB) in private local storage.
- [x] **Milestone 4.2: Model-Aware Passage Segmentation** — Implemented token sequence limit compliance (<500 tokens) with sentence boundary splitting and Unicode code-point offset tracking.
- [x] **Milestone 4.3: Local SQLite Vector Storage** — Implemented raw binary IEEE 754 float32 BLOB storage with vectorized NumPy inner-product cosine similarity search and cascade deletion.
- [x] **Milestone 4.4: Dense Semantic Matcher** — Implemented multilingual candidate scoring, threshold calibration (0.82/0.80), and finding categorization (`paraphrase`, `potential_translation`).
- [x] **Milestone 4.5: Hybrid Analysis Orchestrator** — Integrated Winnowing, BM25, and dense embeddings; computed non-overlapping union coverage and composite net scores.
- [x] **Milestone 4.6: React Dashboard & UI Extensions** — Extended dashboard with 5 metric cards, active model metadata banner, and category-specific text highlight overlays.
- [x] **Milestone 4.7: Automated Testing & Verification** — Verified 90/90 backend tests, 19/19 frontend tests, 10/10 contract checks, and 14/14 end-to-end acceptance scenarios.
