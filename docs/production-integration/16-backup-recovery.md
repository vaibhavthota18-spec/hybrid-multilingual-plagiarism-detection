# 16 — Backup, Disaster Recovery, and Anti-Resurrection Ledger

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Scripts:** `scripts/backup_production.py`, `scripts/restore_production.py`  
**Status:** IMPLEMENTED & VERIFIED  

---

## 1. Disaster Recovery & Snapshot Lifecycle

A robust dual-track backup strategy protects database entities and private files against hardware failure or corruption:

1. **Database Snapshot:** Structured dump of all relational tables and vector associations (`database_dump.json`).
2. **Private Document Storage:** Gzip-compressed tar archive (`private_storage.tar.gz`) containing raw uploaded source files.
3. **Cryptographic Manifest:** `manifest.json` recording UTC timestamp, environment details, record counts per table, and SHA-256 integrity hashes for each archive file.

---

## 2. Anti-Resurrection Deletion Ledger

To comply with data privacy regulations (GDPR / institutional compliance):
- When a document is deleted via `DELETE /documents/{id}`, an immutable record is appended to the `deletion_ledger` table.
- During any disaster recovery restoration from prior backups, `restore_production.py` cross-references the `deletion_ledger`. Any document that was explicitly deleted subsequent to the backup snapshot is automatically expunged upon restoration, preventing accidental data resurrection.
