# 08 — Private Object Storage and Secure File Lifecycle

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Files:** `apps/backend/src/plagiarism/storage/private_store.py`, `apps/backend/src/plagiarism/storage/s3_store.py`  
**Status:** IMPLEMENTED & VERIFIED  

---

## 1. Private Document Storage Invariants

All submitted documents (PDF, DOCX, TXT) and generated similarity reports (PDF, HTML, JSON) are classified as private intellectual property. The system enforces strict isolation guarantees:

1. **No Public Static Exposure:** Files are stored strictly outside web server static routes (`/static/` or public web roots). All downloads must pass through authenticated FastAPI endpoints (`/analyses/{analysis_id}/reports/{format}`).
2. **Directory Traversal Protection:** Every internal path is validated using `candidate.resolve().relative_to(root_dir)`. Any request containing `..`, null bytes, or directory separators is rejected with HTTP 400 `SECURITY_VIOLATION`.
3. **Streaming Size Limit Enforcement:** Files are read in 64 KiB chunks with incremental SHA-256 calculation. If an upload exceeds 30 MiB (`MAX_UPLOAD_SIZE_BYTES = 31,457,280`), streaming aborts immediately, the temporary file is deleted, and HTTP 413 `PayloadTooLargeError` is returned.

---

## 2. Multi-Backend Support (Local & S3 / MinIO)

| Backend | Configuration | Use Case |
|---|---|---|
| **Local Private Storage** | `STORAGE_BACKEND=local`<br>`LOCAL_PRIVATE_STORAGE_ROOT=/app/storage/private` | Native Windows localhost and Docker Compose with shared persistent volume |
| **S3 / Cloud Object Store** | `STORAGE_BACKEND=s3`<br>`S3_BUCKET_NAME=plagiarism-platform-private`<br>`S3_ENDPOINT_URL=...` | Multi-node cloud deployments (AWS S3, Cloudflare R2, MinIO) with server-side encryption (`AES256`) |
