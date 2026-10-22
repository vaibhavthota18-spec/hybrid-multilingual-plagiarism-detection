# Phase 2 — Implementation Report: Document Ingestion, Text Extraction, Multilingual Preprocessing, and Reference Collection Management

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Phase:** Phase 2  
**Status:** COMPLETE (Pass with Non-Blocking Findings)  
**Execution Environment:** Native Windows 11 Localhost (FastAPI :8000, Vite :5173, Python 3.12, Node.js v22.14.0)  

---

## 1. Executive Summary

Phase 2 implementation has been executed completely and verified natively on Windows 11 localhost. In accordance with user directives, no Docker containers, WSL2 instances, or cloud services were used.

All ingestion, parsing, multilingual preprocessing, normalization, segmentation, collection management, and comparison pre-flight validation requirements have been delivered with 100% test success across unit, contract, integration, and end-to-end acceptance suites.

### Key Outcomes
- **Multi-Format Extraction:** Seamless parsing of `.txt` (UTF-8, UTF-16), `.pdf` (`pypdf`), and `.docx` (`python-docx` with XML defused parse & zip bomb defense).
- **Multilingual Support:** Tested and verified on English, Hindi (Devanagari script with combining matras and Danda `।`), Telugu (Brahmic script with virama and dependent vowel signs), and mixed-language academic documents.
- **Precise Offset Tracking:** Strict preservation of absolute start and end code-point offsets into raw unnormalized text, establishing a sound foundation for Phase 3 lexical matches and Phase 6 interactive dual-pane document viewing.
- **Local Development Adapters:** High-performance, concurrency-safe SQLite metadata repository (`WAL` mode, reentrant locking), private filesystem storage (`storage/private`) with SHA-256 deduplication and path traversal sanitization, and thread pool worker (`concurrent.futures`).
- **Strict Phase 3 Boundary Notice:** Absolutely zero mocked or simulated plagiarism similarity scores. Comparison validation returns an honest status: *"Documents are ready for analysis. Similarity detection will be implemented in Phase 3."*

---

## 2. Implemented Components & Directory Manifest

### Backend Architecture (`apps/backend/src/plagiarism/`)
1. **Core Configuration & Security:**
   - `core/config.py`: Added `APP_RUNTIME_MODE = 'local'`, `LOCAL_PRIVATE_STORAGE_ROOT`, `LOCAL_SQLITE_PATH`, and `MAX_UPLOAD_SIZE_BYTES = 31457280` (30 MB).
   - `core/errors.py`: Added domain exceptions: `BadRequestError` (HTTP 400), `PayloadTooLargeError` (HTTP 413), `UnsupportedMediaTypeError` (HTTP 415).
   - `core/security.py`: Enhanced authentication helper `get_current_user_or_dev` enabling seamless localhost development (`researcher@plagiarism.local`) while preserving strict Bearer token authentication in production.
2. **Storage Subsystem:**
   - `storage/local_db.py`: SQLite repository managing 5 core relational tables:
     - `documents`: Document ID, filename, content hash (SHA-256), MIME type, byte size, detected language, script, status, char count, word count, page count, paragraph count.
     - `document_sources`: Raw binary storage paths, original filenames, ingestion timestamps.
     - `passages`: Chunk ID, sequence index, start char, end char, start UTF-16, end UTF-16, text, token count.
     - `collections`: Collection ID, name, description, timestamps.
     - `collection_documents`: Association table linking collections to reference documents.
   - `storage/private_store.py`: Local private filesystem storage manager enforcing path confinement, safe random UUID naming, streaming byte capture, and SHA-256 calculation.
3. **Services & NLP Pipeline:**
   - `services/extractors.py`: Plaintext, PDF, and DOCX extractors with magic byte inspection and size verification.
   - `services/preprocessing.py`: Unicode 15.0 NFC normalization, script identification (`LATIN`, `DEVANAGARI`, `TELUGU`), language classification (`en`, `hi`, `te`, `mixed`), and tokenization preserving Indic combining vowels.
   - `services/segmentation.py`: Sentence and passage segmenter with exact code-point offsets.
   - `services/executor.py`: ThreadPoolExecutor managing background asynchronous tasks with startup job reconciliation.
4. **API Endpoints (`api/v1/`):**
   - `documents.py`: Document upload, metadata retrieval, raw text preview, passage retrieval, and cascade deletion.
   - `collections.py`: Reference corpus collection CRUD and document membership management.
   - `comparisons.py`: Direct (1:1), One-to-Many (1:N), and Corpus (1:Collection) pre-flight validation.
   - `router.py`: Registered all Phase 2 routers.

### Frontend Architecture (`apps/web/src/`)
1. **API Client & Types:**
   - `types/generated/api.ts`: Full TypeScript interfaces for `DocumentMetadata`, `Collection`, `Passage`, `ComparisonValidation`.
   - `lib/api/documents.ts`: Complete typed REST client for documents, collections, and comparison workflows.
2. **Components & Views:**
   - `components/TextPreviewModal.tsx`: Dual-tab inspector for raw text and segmented passages with offset indicators.
   - `pages/IngestionPage.tsx`: Full-featured tabbed workspace containing:
     - Drag-and-drop file uploader with status badges.
     - Document library table with search, pagination, preview modal trigger, and deletion.
     - Reference Collections manager for building benchmark corpora.
     - Comparison Setup tab for configuring and validating 1:1, 1:N, and 1:Collection comparisons.
   - `components/Navigation.tsx`: Activated Document Ingestion navigation item.
   - `App.tsx`: Mounted IngestionPage into main application layout.

---

## 3. Execution Verification Summary

| Suite / Check | Total Checks / Tests | Passed | Failed | Status |
| :--- | :--- | :--- | :--- | :--- |
| OpenAPI Contract Check | 10 | 10 | 0 | PASS |
| Phase 0 Guard Validation | 57 | 57 | 0 | PASS |
| Backend Pytest Suite | 67 | 67 | 0 | PASS |
| Frontend Vitest Suite | 13 | 13 | 0 | PASS |
| Frontend Production Build | 1,582 modules | 1,582 | 0 | PASS |
| 24-Step Localhost E2E | 24 | 24 | 0 | PASS |
| **Total Automated Evidence** | **171 checks** | **171** | **0** | **100% PASS** |
