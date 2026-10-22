# Phase 7 — Complete System Audit

## 1. Inventory of Subsystems & Components

| Subsystem | Core Files | Responsibility | Local Runtime Adapter | Production Target |
| :--- | :--- | :--- | :--- | :--- |
| **Document Ingestion** | `extractors.py`, `preprocessing.py`, `segmentation.py` | PDF, DOCX, TXT text extraction, Unicode normalization (NFC), sentence segmentation | Native Windows filesystem, `pypdf`, `python-docx` | S3 / MinIO, distributed workers |
| **Lexical Engine** | `winnowing.py`, `rolling_hash.py`, `bm25.py`, `passage_aligner.py` | Deterministic fingerprints ($k=25, w=16$), BM25 candidate retrieval, Smith-Waterman alignment | Local Python in-memory / SQLite | PostgreSQL inverted indexes |
| **Semantic AI** | `provider.py`, `embeddings.py`, `vector_store.py` | Multilingual E5 Small ($384\text{d}$) embeddings, dense cosine similarity, SQLite BLOB store | Local PyTorch CPU / Windows DirectML | `pgvector` HNSW index |
| **Hybrid Analysis** | `hybrid_service.py`, `analysis_service.py` | Non-overlapping token union coverage, candidate pooling | Local ThreadPoolExecutor (2 workers) | Redis + RQ async workers |
| **Reviewer Workflow** | `analyses.py`, `local_db.py` | Human review actions (`keep`, `exclude`, `quoted_cited`, `needs_review`), notes, dynamic adjusted coverage | SQLite WAL tables (`analyses`, `analysis_findings`) | PostgreSQL transactions |
| **Reporting** | `report_generator.py` | Formal PDF, standalone offline HTML (@media print), structured JSON exports | ReportLab 5.0.1 + Nirmala UI Indic TrueType | Headless browser / PDF microservice |
| **Frontend UI** | `WorkflowPage.tsx`, `ResultsDashboardPage.tsx`, `App.tsx` | iLovePDF-inspired 5-stage workflow, dual-pane synchronized evidence viewer | Vite 5.4.21, React 18, Tailwind CSS | Nginx / CDN static hosting |

## 2. Verified Baseline Health
- **Backend Test Suite:** 104 / 104 passed in 125.42s (`pytest apps/backend/tests -q`).
- **Frontend Test Suite:** 21 / 21 passed in 19.32s (`npm test -- --run`).
- **Production Build:** 0 TypeScript or Vite bundling errors (`npm run build`).
- **Phase 6 Regression:** 14 / 14 scenarios passed (`scripts/verify_phase6_e2e.py`).
- **Phase 7 E2E Suite:** 26 / 26 scenarios passed (`scripts/verify_phase7_e2e.py`).
