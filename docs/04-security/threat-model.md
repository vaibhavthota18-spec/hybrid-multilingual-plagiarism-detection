# Security Architecture & Threat Model (STRIDE)

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Threat Modeling Methodology

This document evaluates system vulnerabilities using the Microsoft STRIDE methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) mapped across the document analysis lifecycle.

---

## 2. Threat Analysis & Mitigation Matrix

### 2.1 File Upload & Malicious Payloads
- **Threat:** Malicious executable files disguised as PDFs, polyglot payloads, or files containing embedded malware.
- **Likelihood:** High | **Impact:** Critical
- **Mitigations:**
  1. Strict magic-byte header inspection via `python-magic`, ignoring user-supplied file extensions and MIME headers.
  2. Complete filename sanitization: Client filenames are discarded; storage uses generated random UUIDs.
  3. Storage outside public web server roots (`./storage/uploads/`).
  4. Execution permissions stripped (`chmod 0644`).
- **Verification:** Automated tests uploading polyglot files (e.g., PHP shell prepended with `%PDF-1.4`) asserting rejection with HTTP 400 (`INVALID_FILE_FORMAT`).

### 2.2 Unsafe Document Parsing & Decompression Bombs
- **Threat:** Malformed PDF object trees or DOCX XML External Entity (XXE) / zip bombs consuming all worker memory and crashing daemon processes.
- **Likelihood:** Medium | **Impact:** High
- **Mitigations:**
  1. PyMuPDF parsing executes inside sandboxed worker processes bounded by OS memory limits (`RLIMIT_AS` / container memory limits).
  2. `python-docx` parser uses `defusedxml` to block entity expansions (billion laughs attack) and external DTD fetching.
  3. Max uncompressed size limit (100 MB maximum extracted text buffer).
- **Verification:** Fuzzing tests injecting malformed XML into DOCX test fixtures and corrupted PDF streams asserting graceful failure without worker death.

### 2.3 Path Traversal Attacks
- **Threat:** Uploads or report requests supplying filenames like `../../../../etc/passwd` or `..\..\Windows\win.ini`.
- **Likelihood:** High | **Impact:** Critical
- **Mitigations:**
  1. Internal filesystem paths are constructed exclusively using canonical UUIDs (`uuid.uuid4()`) and fixed base directories.
  2. Filepaths are resolved with strict directory boundary validation:
     ```python
     resolved = Path(base_dir).joinpath(safe_filename).resolve()
     if not resolved.is_relative_to(Path(base_dir).resolve()):
         raise SecurityException("Path traversal attempt detected")
     ```
- **Verification:** Automated tests attempting path traversal parameters asserting immediate HTTP 400 rejection.

### 2.4 Authentication Bypass & Token Tampering
- **Threat:** Forged JWT access tokens, algorithm confusion attacks (e.g., changing `RS256` to `none`), or expired token reuse.
- **Likelihood:** Medium | **Impact:** Critical
- **Mitigations:**
  1. Explicit algorithm pinning (`algorithms=["HS256"]` or `["RS256"]`).
  2. Strict signature verification with secure secrets rotated via environment variables.
  3. Short-lived access tokens (60 minutes) combined with secure, HttpOnly refresh cookies.
- **Verification:** Automated security tests attempting `alg: none` JWTs and altered signatures asserting HTTP 401 Unauthorized.

### 2.5 Insecure Direct Object References (IDOR) & Collection Access
- **Threat:** User A alters the `collection_id` parameter to query or download reference documents from User B's private departmental collection.
- **Likelihood:** High | **Impact:** High
- **Mitigations:**
  1. Mandatory database authorization join on `collection_permissions` scoped to `user_id`.
  2. Vector and BM25 queries execute with non-bypassable SQL collection filter predicates.
- **Verification:** Multi-tenant test suite attempting cross-account document downloads and corpus searches asserting HTTP 403 Forbidden.

### 2.6 Embedding & Fingerprint Reconstruction (Information Disclosure)
- **Threat:** Model inversion attacks or brute-force rainbow tables attempting to reconstruct raw manuscript text from stored 768-dim embeddings or Winnowing hash values.
- **Likelihood:** Low | **Impact:** Medium
- **Mitigations:**
  1. High-dimensional embeddings and rolling hashes are stored in the private database behind authentication, never exposed via public APIs.
  2. Winnowing fingerprints use a salted rolling hash with a rotating deployment seed.
  3. Deletion of a document cascades to immediately delete all corresponding embeddings and fingerprints.
- **Verification:** Document deletion assertions confirming zero remaining vector or hash records.

### 2.7 Worker Resource Exhaustion & Algorithmic DoS
- **Threat:** Submitting a crafted 10,000-page document or repeating token sequences that cause quadratic time explosions ($O(N \cdot M)$) in Smith-Waterman local alignment.
- **Likelihood:** Medium | **Impact:** High
- **Mitigations:**
  1. Maximum document cap: 100 pages / 30 MB.
  2. Local alignment is restricted to bounded candidate passage windows ($\le 1,500$ characters), preventing macro-scale quadratic runtime.
  3. Strict job execution timeout capped at 600 seconds (10 minutes).
- **Verification:** Benchmark testing against pathological repetitive strings asserting strict timeout cutoffs.

### 2.8 Unsafe Logging & PII Leakage
- **Threat:** Logging raw extracted student essays, passwords, or Authorization headers to standard stdout or log aggregation systems.
- **Likelihood:** High | **Impact:** High
- **Mitigations:**
  1. Structured JSON logger includes explicit redaction filters for fields named `password`, `token`, `file`, and `raw_text`.
  2. Logs record only metadata: `document_id`, `page_count`, `job_id`, `latency_ms`.
- **Verification:** Log output inspection tests asserting complete absence of raw text or tokens in log streams.

### 2.9 Incomplete Deletion & Backup Restoration Resurrection
- **Threat:** Relational database records are deleted but raw PDF files, vector rows, or cached embeddings remain accessible, or older database backups restored during disaster recovery silently resurrect previously deleted documents.
- **Likelihood:** Medium | **Impact:** High
- **Mitigations:**
  1. Reliable multi-tier deletion workflow: immediate access restriction (`status = 'DELETING'`), worker task fencing token (`fence:doc:{id}`), ACID database cascade (`ON DELETE CASCADE`), idempotent filesystem unlinking, and Redis cache eviction.
  2. Durable Deletion Ledger: Append-only tombstone recorded outside standard relational snapshots so deletion intent survives historical database restorations.
  3. Disaster recovery anti-resurrection hook: Database restoration runbooks require an automated startup reconciliation hook that queries the Durable Deletion Ledger and re-purges any restored records deleted post-snapshot before opening the API to traffic.
  4. Physical storage boundary disclosure: Filesystem unlinks free allocation entries; complete physical bit sanitization occurs as storage reallocates blocks.
- **Verification:** Automated purge integration test asserting zero leftover rows/files, plus backup restore simulation asserting successful reconciliation re-purge.

### 2.10 Host Workspace Cloud-Sync Leakage & Lock Contention
- **Threat:** Automated cloud sync (OneDrive) locks SQLite/WAL/Docker bind mount files or uploads private test documents to external cloud storage.
- **Likelihood:** Medium | **Impact:** Medium
- **Mitigations:**
  1. Mandate Docker named volumes (`postgres_data`, `storage_volume`) for database and upload persistence.
  2. Ignore all storage and cache folders in `.gitignore`.
  3. Support non-synced local fallback path via `STORAGE_ROOT_DIR` in `.env.example`.
- **Verification:** Verification that Docker compose specifies named volumes and `.gitignore` ignores all storage and model paths.
