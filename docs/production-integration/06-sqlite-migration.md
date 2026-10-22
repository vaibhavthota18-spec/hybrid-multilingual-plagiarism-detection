# 06 — Safe SQLite-to-PostgreSQL Data Migration Tool

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Script:** `scripts/migrate_sqlite_to_postgres.py`  
**Status:** IMPLEMENTED & TESTED  

---

## 1. Migration Objective & Principles

The migration tool transfers all persisted historical metadata and dense embeddings from the local SQLite database (`storage/local_metadata.db`) to the production PostgreSQL + pgvector database.

### Mandatory Rules Followed
1. **Zero Data Loss:** All documents, sources, passages, fingerprints, collections, analyses, findings, and reviews must be copied.
2. **Binary BLOB Vector Deserialization:** SQLite stores IEEE 754 float32 byte buffers in `passage_embeddings.embedding`. The migration tool decodes them with `np.frombuffer(raw_blob, dtype=np.float32)` and inserts them as native pgvector arrays.
3. **Idempotence & Safety:** Every insert utilizes `ON CONFLICT DO NOTHING` or upserts, allowing repeated executions without creating duplicate records or crashing.
4. **Dry-Run by Default:** Running without `--execute` performs a non-destructive dry-run that checks source counts, validates constraints, and tests connectivity without modifying target data.

---

## 2. CLI Usage & Verification

```powershell
# Dry Run Verification (Non-destructive)
python scripts/migrate_sqlite_to_postgres.py --dry-run

# Live Execution to Target PostgreSQL
python scripts/migrate_sqlite_to_postgres.py --execute --postgres-url "postgresql://user:pass@host:5432/plagiarism_platform"
```

### Table Migration Mapping

| Table | Source Type | Target PostgreSQL Type | Special Transformation |
|---|---|---|---|
| `documents` | SQLite row | `documents` | Foreign key to `users` ensured |
| `document_sources` | SQLite row | `document_sources` | Provenance URI preserved |
| `passages` | SQLite row | `passages` | Sequence offsets validated |
| `document_fingerprints` | SQLite row | `fingerprints` | BigInteger hash preserved |
| `collections` | SQLite row | `collections` | Tenant isolation preserved |
| `collection_documents` | SQLite row | `collection_documents` | Primary key pair preserved |
| `analyses` | SQLite row | `analyses` & `analysis_jobs` | Coverage scores converted to Numeric(5,2) |
| `passage_embeddings` | SQLite BLOB | `passage_embeddings` | `vector(384)` formatted via pgvector |
