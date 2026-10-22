# Phase 2 — Implementation Plan: Document Ingestion, Text Extraction, Multilingual Preprocessing, and Reference Collection Management

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Phase:** Phase 2  
**Status:** Completed  
**Environment:** Windows 11 Native Localhost (No Docker, No WSL2)  

---

## 1. Executive Summary & Objectives

The primary objective of Phase 2 is to deliver a fully operational, production-architected document processing pipeline and reference collection management subsystem that executes reliably in native Windows 11 localhost development without requiring container virtualization (Docker or WSL2) or cloud infrastructure.

Phase 2 bridges the Phase 1 engineering foundation (React 18 + TypeScript frontend, FastAPI backend, local execution orchestration) with the upcoming Phase 3 lexical detection algorithms by creating the foundational ingestion, parsing, normalization, segmentation, and persistence layers.

### Key Milestones
1. **Local Development Storage & Database Adapters:** SQLite metadata repository with WAL mode and reentrant thread synchronization; secure private filesystem document store with SHA-256 deduplication and path traversal defenses; in-memory thread pool worker.
2. **Multi-Format Document Extractors:** Robust text extraction for `.txt` (UTF-8, UTF-16 LE/BE), `.pdf` (`pypdf`), and `.docx` (`python-docx` with XML defused parse & zip bomb checks).
3. **Multilingual Preprocessing & Normalization:** Unicode 15.0 NFC normalization with Devanagari and Telugu combining mark (matras, viramas) preservation; script and language detection (`en`, `hi`, `te`, `mixed`); regex-based word tokenization with exact character code-point offsets.
4. **Deterministic Passage Segmentation:** Sentence and passage chunking preserving absolute start and end offsets into original unnormalized text; language-aware sentence delimiters (standard punctuation plus Danda `।` and Double Danda `॥`).
5. **Collection & Comparison Management:** CRUD operations for user reference collections; linkage between collections and documents; pre-flight validation for Direct (1:1), One-to-Many (1:N), and Corpus (1:Collection) comparison setups.
6. **Frontend Ingestion UI:** Multi-file drag-and-drop upload dropzone, live document library with pagination/search/status polling, reference collection manager, raw text & passage preview modal with code-point inspectability, and comparison setup view with strict Phase 3 boundary enforcement.

---

## 2. Architectural Boundary & Strict Phase Separation

To preserve absolute architectural integrity and prevent synthetic or misleading metrics:
- **Zero Fictitious Plagiarism Scores:** Phase 2 does NOT generate, mock, simulate, or display similarity percentages, heatmaps, or alignment scores.
- **Explicit Phase 3 Notification:** When a user selects documents and clicks "Validate Comparison Setup", the system reports:
  > *"Documents are ready for analysis. Similarity detection will be implemented in Phase 3."*
- **Preserved Extensibility:** All database schemas, data transfer objects, and OpenAPI contracts are designed to seamlessly accept Phase 3 Winnowing fingerprints, BM25 indices, and Phase 4 dense multilingual embedding vectors without breaking changes.

---

## 3. Work Breakdown Structure (WBS)

### Work Package 1: Local Storage & Persistence Architecture
- `apps/backend/src/plagiarism/core/config.py`: Configuration flags for local runtime mode, SQLite database path (`storage/local_metadata.db`), private filesystem storage path (`storage/private`), and upload constraints (30 MB limit).
- `apps/backend/src/plagiarism/storage/private_store.py`: File storage abstraction with content-addressable storage, safe filename sanitation, path traversal containment, and SHA-256 digest computation.
- `apps/backend/src/plagiarism/storage/local_db.py`: SQLite metadata repository utilizing Python's `sqlite3`, enabling Write-Ahead Logging (`WAL`), enforcing `PRAGMA foreign_keys = ON`, reentrant locking (`threading.RLock`), table creation, and transactional CRUD methods.

### Work Package 2: Ingestion & Text Extraction Pipeline
- `apps/backend/src/plagiarism/services/extractors.py`:
  - Plaintext extractor supporting UTF-8 and UTF-16 variants with BOM stripping.
  - PDF extractor utilizing `pypdf` with page-by-page extraction and page break demarcation.
  - Word DOCX extractor using `python-docx` extracting headings, paragraphs, and table cell contents.
  - Magic byte validation and MIME-type enforcement preventing file masquerading.
- `apps/backend/src/plagiarism/services/preprocessing.py`:
  - Unicode NFC normalization.
  - Script identification and multilingual classification (`en`, `hi`, `te`, `mixed`).
  - Combining character preservation ensuring Indic conjuncts (matras, halant/virama) remain intact.
  - Tokenization retaining exact code-point offset ranges into raw text.
- `apps/backend/src/plagiarism/services/segmentation.py`:
  - Chunking strategy generating passage records of ~150-250 words while respecting sentence boundaries (period, exclamation, question mark, Devanagari Danda `।`, Double Danda `॥`).
  - Calculating exact start and end offsets (`start_char`, `end_char`, `start_utf16`, `end_utf16`).

### Work Package 3: Background Worker & Execution Management
- `apps/backend/src/plagiarism/services/executor.py`:
  - Local background worker powered by Python `concurrent.futures.ThreadPoolExecutor`.
  - Job state transitions: `queued` $\to$ `processing` $\to$ `completed` / `failed`.
  - Startup reconciliation transitioning orphaned in-flight jobs to `failed` upon server restart.
  - Optional synchronous processing flag (`sync_processing=true`) for deterministic automated testing and CLI scripts.

### Work Package 4: REST API Endpoints & Contract Conformance
- `apps/backend/src/plagiarism/api/v1/documents.py`:
  - `POST /api/v1/documents`: Multipart upload, magic byte check, hashing, background ingestion dispatch.
  - `GET /api/v1/documents`: List uploaded documents with status, pagination, and sorting.
  - `GET /api/v1/documents/{id}`: Document metadata and processing status.
  - `GET /api/v1/documents/{id}/text`: Extracted raw text preview with offset statistics.
  - `GET /api/v1/documents/{id}/passages`: Segmented passages with offset intervals.
  - `DELETE /api/v1/documents/{id}`: Cascade deletion of metadata, passages, and stored binary files.
- `apps/backend/src/plagiarism/api/v1/collections.py`:
  - `POST /api/v1/collections`: Create reference corpus collection.
  - `GET /api/v1/collections`: List collections.
  - `GET /api/v1/collections/{id}`: Collection metadata and document count.
  - `POST /api/v1/collections/{id}/documents`: Add document reference to collection.
  - `GET /api/v1/collections/{id}/documents`: List member documents.
  - `DELETE /api/v1/collections/{id}/documents/{doc_id}`: Remove document reference from collection.
- `apps/backend/src/plagiarism/api/v1/comparisons.py`:
  - `POST /api/v1/comparisons/validate`: Pre-flight verification of Direct (1:1), One-to-Many (1:N), and Corpus (1:Collection) inputs with honest Phase 3 boundary response.

### Work Package 5: React Frontend Integration (`apps/web`)
- TypeScript schema synchronization (`apps/web/src/types/generated/api.ts`).
- Typed API client module (`apps/web/src/lib/api/documents.ts`).
- Modal component (`apps/web/src/components/TextPreviewModal.tsx`) showing raw text and segmented passages with character count and code-point indices.
- Comprehensive Ingestion view (`apps/web/src/pages/IngestionPage.tsx`) featuring:
  - Drag-and-drop file upload with progress indicator.
  - Live document table with status badges and actions (Preview, View Passages, Delete).
  - Reference Collections manager (Create corpus, add/remove member documents).
  - Comparison Setup workflow (Select submission document, select reference targets, validate setup).

### Work Package 6: Verification & Test Automation
- Backend Pytest suite verifying extractors, normalization, segmentation, storage, and API endpoints.
- Vitest suite verifying React components, user workflows, and comparison validation.
- End-to-end localhost acceptance test script (`scripts/verify_phase2_e2e.py`) executing all 24 required verification workflow steps against live servers on localhost:8000 and localhost:5173.
- Contract validation and OpenAPI spec generation.

---

## 4. Resource Allocation & Execution Timeline

| Work Package | Primary Responsibility | Validation Method |
| :--- | :--- | :--- |
| WP1: Storage & SQLite DB | Backend & Database Engineering | `test_local_storage_db.py` |
| WP2: Parsing & Multilingual NLP | NLP & Document Processing Engineering | `test_extractors.py`, `test_preprocessing.py`, `test_segmentation.py` |
| WP3: Executor & Worker | Systems Engineering | `test_worker.py` |
| WP4: REST API & Contracts | API Integration Engineering | `test_phase2_api.py`, `validate_contract.ps1` |
| WP5: React UI & Components | Frontend & UI/UX Engineering | `npm run test`, `vite build` |
| WP6: End-to-End Acceptance | QA & Test Automation | `verify_phase2_e2e.py` (24 steps) |
