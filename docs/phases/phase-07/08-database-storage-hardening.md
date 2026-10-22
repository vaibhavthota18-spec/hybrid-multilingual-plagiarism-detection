# Phase 7 — Database & Storage Hardening

## 1. SQLite WAL Mode Configuration
The local SQLite repository enforces robust production-style settings:
- `PRAGMA foreign_keys = ON;` — Guarantees strict referential integrity across documents, passages, analyses, findings, and reviews.
- `PRAGMA journal_mode = WAL;` — Write-Ahead Logging allows concurrent readers alongside writers without blocking.
- `PRAGMA busy_timeout = 30000;` — 30-second busy handler timeout avoids `database is locked` exceptions during concurrent background thread operations.

## 2. Private Storage Safety
- **Directory Structure:**
  - `storage/documents/` — Raw uploaded files and extracted text.
  - `storage/db/metadata.db` — SQLite relational metadata and vector BLOBs.
- **OneDrive & Git Isolation:**
  - `.gitignore` explicitly excludes:
    - `storage/`
    - `data/backups/`
    - `*.db`, `*.db-wal`, `*.db-shm`
    - `.venv/`
    - `node_modules/`
  - Guarantees private student and research documents are never committed or unintentionally synced.
