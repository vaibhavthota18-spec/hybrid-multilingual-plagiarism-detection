# Privacy, Access Governance & Data Retention Policy

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Ethical Privacy Foundation & Intellectual Property Rights

In accordance with academic privacy norms and international data protection laws (GDPR, FERPA, Indian DPDP Act):
1. **User Ownership:** Authors and students retain 100% intellectual property ownership of their submitted works. Uploading a document to this platform does NOT transfer copyright, grant publishing licenses, or authorize commercial exploitation.
2. **Private by Default:** Uploaded documents are private to the submitting user account. They are NEVER added to general search corpora or shared across tenants without explicit, affirmative opt-in consent.
3. **No Third-Party Transmission:** Document text, extracts, and embeddings are processed locally within the self-contained platform deployment. **No data is ever transmitted to third-party AI APIs (such as OpenAI, Anthropic, or external cloud LLMs).**

---

## 2. Authorization Matrix

| Action | Guest | Student | Researcher | Educator | Reviewer | Admin |
|---|---|---|---|---|---|---|
| Run Direct Comparison (Mode A) | Allowed | Allowed | Allowed | Allowed | Allowed | Allowed |
| Run One-to-Many Comparison (Mode B) | Denied | Allowed | Allowed | Allowed | Allowed | Allowed |
| Run Corpus Search (Mode C) | Denied | Permitted* | Permitted* | Permitted* | Permitted* | Allowed |
| Upload Document to Private Storage | Ephemeral | Allowed | Allowed | Allowed | Allowed | Allowed |
| Hard Delete Own Document | Auto (1h) | Allowed | Allowed | Allowed | Allowed | Allowed |
| Ingest Document into Collection (Corpus) | Denied | Denied | Permitted* | Permitted* | Permitted* | Allowed |
| Annotate Finding with Review Decision | Denied | Denied | Denied | Allowed | Allowed | Allowed |
| Export Signed PDF Report | Denied | Allowed | Allowed | Allowed | Allowed | Allowed |
| Manage User Roles & Collections | Denied | Denied | Denied | Denied | Denied | Allowed |

*\*Permitted only if granted explicit `READ` or `WRITE` permissions on the target collection.*

---

## 3. Data Retention & Right to Erasure (Hard Deletion)

### 3.1 Retention Periods
- **Ephemeral Guest Submissions:** Automatically purged from disk and database 1 hour following analysis completion.
- **Authenticated User Submissions:** Retained until explicitly deleted by the user or upon institutional account closure.
- **Reference Corpus Documents:** Retained indefinitely until removed by collection administrators.

### 3.2 Reliable Multi-Tier Deletion Workflow
Because deletion spans the relational database, local object storage, Redis cache, and background worker memory, cross-system operations **do not occur in a single atomic transaction**. The system implements a reliable, fenced, and verifiable deletion workflow:

1. **Authorization Gate:** Verification of document ownership or administrative privileges.
2. **Immediate Access Restriction:** The document status is set to `status = 'DELETING'` in a fast transaction, immediately filtering it out of all user dashboards, collection statistics, and search candidate matching.
3. **Durable Deletion Ledger (Independent Tombstone):** A permanent tombstone is written to an independent, append-only Deletion Ledger stream (`{ledger_id, document_id, requested_at, status: "PENDING"}`). This ledger is maintained outside standard operational database snapshots to survive backup restoration events.
4. **Worker Fencing & Job Cancellation:** Active or queued analysis jobs for the document are aborted using Redis fencing tokens (`fence:doc:{document_id}`). In-flight workers observing this token abort immediately, discarding partial results.
5. **Relational & Vector Hard Deletion (ACID Cascade):** PostgreSQL executes an ACID cascading delete across `findings`, `embeddings` (in `pgvector`), `fingerprints`, `passages`, `collection_documents`, `document_sources`, and `documents`.
6. **Idempotent Filesystem Unlinking:** Storage service unlinks the raw file (`storage/uploads/{id}.*`), extracted text caches, and generated PDF reports (`storage/reports/rep_{id}_*.pdf`). Missing files do not abort the workflow.
7. **Cache & Volatile Eviction:** Redis job states and candidate caches are purged immediately.
8. **Idempotent Retry & Completion Certification:** If transient filesystem locks (e.g., OneDrive sync locks) delay file unlinking, background retry workers retry with exponential backoff until all storage references are confirmed erased, updating the Deletion Ledger to `status = "COMPLETED"`.

### 3.3 Disaster Recovery Backups, Anti-Resurrection & Physical Retention Limits
- **Time-Limited Safe-Harbor:** Encrypted WAL archives and daily database snapshots retain recovery data for up to 30 days solely for disaster recovery.
- **Post-Restore Anti-Resurrection Reconciliation:** In the event of a database recovery from a historical backup, an automated startup reconciliation hook queries the independent Durable Deletion Ledger and immediately cascades deletion for any restored records marked deleted post-snapshot, preventing silent document resurrection.
- **Physical Storage Boundaries:** Operating system file unlinks remove directory allocation entries and free blocks for reuse. Raw physical storage blocks remain on SSD/HDD media until overwritten by subsequent write cycles. OS journal logs and cloud storage snapshots follow infrastructure retention policies.

---

## 4. Academic Fair Use & Source Licensing Governance

Reference documents ingested into persistent collections must declare formal licensing metadata:
- **Permitted Licenses:** `CC-BY-4.0`, `CC-BY-SA-4.0`, `CC-0 / Public Domain`, or `Institutional-Internal-Authorized`.
- **Fair Use Evidentiary Principle:** Similarity analysis extracts and compares short bounded passages for originality verification—an established Fair Use academic doctrine. The system preserves source attribution (author, title, publication year) for every matching passage.

---

## 5. Evaluation Data Handling & Anonymization

Datasets curated for Phase 5 benchmarking (`evaluation/datasets/`):
- Must be stripped of sensitive student personal identifiable information (PII, student IDs, phone numbers).
- Text snippets sourced from student papers must have obtained academic research consent or be completely synthesized/anonymized.
- Evaluation manifests and annotations are version-controlled without committing private unconsented documents.

---

## 6. Workspace Environment & Cloud Sync Safeguards (OneDrive Isolation)

Because the project workspace root resides within a Microsoft OneDrive path (`C:\Users\vaibh\OneDrive\Documents\plagarism engine`), automated background cloud synchronization introduces three specific operational risks that must be governed:

1. **File-Locking & Concurrency Conflicts:** OneDrive background sync periodically locks newly created files, which can cause `EPERM`, `EBUSY`, or write-collision failures in fast-writing processes (e.g., SQLite WAL logs, model cache downloads, rapid test runs).
2. **Cloud Quota & Bandwidth Churn:** Transformer model weights (`~1.1 GB`), evaluation fixture corpora, Python virtual environments, and `node_modules` will exhaust personal OneDrive storage quotas and cause high network overhead if synced.
3. **Privacy Exposure Risk:** Private test uploads (`storage/uploads/`) must never be synchronized to an external personal cloud drive.

### Mandatory Safeguards:
- **Docker Volume Isolation:** In all containerized development and deployment setups (`compose.yml`), PostgreSQL data (`/var/lib/postgresql/data`) and file storage (`/storage`) MUST use Docker named volumes (`postgres_data`, `storage_volume`) managed within the Docker daemon storage engine, rather than host directory bind-mounts inside the OneDrive path.
- **Local Dev Fallback Configuration:** In `.env.example`, `STORAGE_ROOT_DIR` is pre-configured to a local subpath that is strictly ignored by `.gitignore`. For local native runs, developers may optionally set `STORAGE_ROOT_DIR=%LOCALAPPDATA%\plagiarism_platform\storage` outside the OneDrive synchronization tree.
- **Git & Sync Ignore:** `.gitignore` excludes `storage/uploads/`, `storage/reports/`, `models/weights/`, `.venv/`, and `node_modules/`. Developers can apply the Windows cloud-unpin attribute (`attrib +u "storage"`) to prevent local folders from uploading to the cloud.
