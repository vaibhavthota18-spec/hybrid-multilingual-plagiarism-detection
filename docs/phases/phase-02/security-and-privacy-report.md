# Phase 2 — Security & Privacy Architecture Report

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Phase:** Phase 2  
**Topic:** Threat Mitigation, File Security, Access Boundaries, and Data Privacy  

---

## 1. Threat Modeling & Attack Surface in Ingestion

Document ingestion systems process untrusted user-supplied binary files and text strings, creating significant potential security vulnerabilities:
1. Directory Traversal / Path Manipulation
2. Malicious File Uploads / File Masquerading (MIME spoofing)
3. Decompression Bombs (Zip Bombs in DOCX)
4. Memory Exhaustion via Large Payloads (DoS)
5. SQL Injection via Malformed Document Metadata
6. Premature Privacy Leakage or Data Remanence

---

## 2. Defensive Controls Implemented in Phase 2

### 2.1 Directory Traversal Neutralization
- **Vulnerability:** Attackers may upload files named `../../../../Windows/System32/evil.dll` or similar paths to overwrite critical host files.
- **Defense Implementation:**
  - Filenames supplied in multipart headers are never used as on-disk storage targets.
  - Stored files are assigned cryptographically random UUIDv4 identifiers: `storage/private/<uuid4>`.
  - In `private_store.py`, every file path is checked with `Path.resolve()` and tested against `base_dir.resolve()`:
    ```python
    try:
        resolved.relative_to(self.base_dir.resolve())
    except ValueError:
        raise ValueError("Path traversal attempt detected")
    ```

### 2.2 Magic Byte Verification & MIME Spoofing Defense
- **Vulnerability:** Attackers may rename an executable (`.exe`) to `.txt` or `.docx` to bypass file extension filters.
- **Defense Implementation:**
  - `apps/backend/src/plagiarism/services/extractors.py` reads the initial bytes of incoming files:
    - **PDF:** Must begin with the signature `%PDF-` (`0x25 0x50 0x44 0x46 0x2D`).
    - **DOCX:** Must begin with the standard ZIP magic number `PK\x03\x04` (`0x50 0x4B 0x03 0x04`).
    - **TXT:** Probed for valid UTF-8/UTF-16 encoding with rejection of non-text binary controls.
  - Files failing magic byte validation are rejected immediately with `HTTP 415 Unsupported Media Type`.

### 2.3 Zip Bomb Defense (DOCX)
- **Vulnerability:** A tiny DOCX file (e.g. 50 KB) can decompress into 50 GB of repetitive XML, exhausting server memory and crashing the process.
- **Defense Implementation:**
  - Zip header inspection calculates total uncompressed stream size prior to decompression.
  - Maximum compression ratio threshold of 100:1 enforced.
  - Maximum uncompressed XML size capped at 100 MB.

### 2.4 Streaming Uploads & Memory Exhaustion Controls
- **Vulnerability:** Uploading massive 5 GB files can exhaust RAM if loaded into memory at once.
- **Defense Implementation:**
  - Files are streamed in 64 KB chunks directly to disk.
  - A running byte counter checks against `MAX_UPLOAD_SIZE_BYTES` (30 MB limit). If exceeded during streaming, the stream is terminated, the partial file on disk is deleted, and `HTTP 413 Payload Too Large` is returned.

### 2.5 SQL Parameterization & Injection Defense
- **Vulnerability:** Malicious filenames or titles containing SQL injection strings (`'; DROP TABLE documents; --`).
- **Defense Implementation:**
  - All SQLite operations in `LocalMetadataRepository` use parameterized queries exclusively (`?` placeholders). Zero string concatenation or formatting is used in SQL query execution.

### 2.6 Privacy, Retention, and Cascade Deletion
- **Vulnerability:** Orphaned documents or deleted files remaining accessible on disk.
- **Defense Implementation:**
  - When `DELETE /api/v1/documents/{id}` is executed:
    1. Associated database records in `passages` are deleted.
    2. Associated records in `collection_documents` are deleted.
    3. The `document_sources` record is deleted.
    4. The primary `documents` record is deleted.
    5. The raw file stored on disk in `storage/private/<uuid4>` is securely unlinked.
  - Subsequent requests to access the deleted document return `HTTP 404 Not Found`.

---

## 3. Development vs Production Access Control

To facilitate agile Windows 11 localhost development without requiring an active Keycloak identity provider:
- `core/security.py` provides `get_current_user_or_dev`:
  - When a valid `Authorization: Bearer <token>` is passed, it validates the JWT against security policies.
  - When unauthenticated in `APP_RUNTIME_MODE = 'local'`, it transparently defaults to the verified development user `researcher@plagiarism.local` (`00000000-0000-0000-0000-000000000001`).
  - Strict authentication endpoint `/api/v1/auth/me` preserves full Bearer token rejection (`HTTP 401 Unauthorized`), maintaining test fidelity.
