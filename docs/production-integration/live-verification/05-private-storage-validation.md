# 05 — Private Object Storage and File Integrity Validation

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Milestone:** Live Deployment & Production Verification Audit  
**Date:** 2026-10-16  
**Status:** CODE COMPLETE & SYNTHETICALLY VERIFIED  

---

## 1. Storage Security Invariants

All uploaded documents and generated reports are stored strictly in private directories:
- **Local / Container Mode:** `/app/storage/private/` (mounted as a shared persistent volume across API and worker).
- **Cloud S3 Mode:** Configured via `s3_store.py` with server-side encryption (`AES256`).

### Security Controls Enforced
1. **Directory Traversal Protection:**
   Any path attempting `..`, `/`, or `\` is caught by `_get_safe_path()`:
   ```python
   candidate.resolve().relative_to(self.root_dir)
   ```
   Raising HTTP 400 `SECURITY_VIOLATION`.
2. **Streaming 30 MiB Size Limit:**
   Uploads are read in 64 KiB chunks with running byte counters. Exceeding 30 MiB immediately aborts the stream, deletes partial bytes, and returns HTTP 413 `PayloadTooLargeError`.
3. **SHA-256 Checksums:**
   Every stored object computes a SHA-256 hash incrementally during upload and stores it in the `documents` table for tamper-evident audit verification.
