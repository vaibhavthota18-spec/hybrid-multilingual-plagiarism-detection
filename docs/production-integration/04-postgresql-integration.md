# 04 — PostgreSQL Database Integration & Schema Management

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Files:** `apps/backend/src/plagiarism/storage/pg_db.py`, `apps/backend/alembic/`  
**Status:** IMPLEMENTED & VERIFIED  

---

## 1. PostgreSQL Architecture & Drop-in Adapter

To replace local SQLite persistence in production environments while maintaining 100% backward compatibility, `apps/backend/src/plagiarism/storage/pg_db.py` was created.

It defines `PostgresMetadataRepository`, implementing the exact 28-method interface of `LocalMetadataRepository`:
- **Document Ingestion:** `insert_document`, `get_document`, `update_document_extraction`, `list_documents`, `delete_document`
- **Passage Segmentation:** `insert_passages`, `get_passages`
- **Lexical Fingerprints:** `save_fingerprints`, `get_fingerprints`, `find_shared_fingerprints`
- **Collections:** `create_collection`, `get_collection`, `list_collections`, `add_document_to_collection`, `remove_document_from_collection`, `list_collection_documents`
- **Similarity Analyses:** `create_analysis`, `update_analysis_status`, `update_analysis_review_summary`, `get_analysis`, `list_analyses`, `delete_analysis`, `save_analysis_results`, `get_analysis_findings`, `get_analysis_sources`
- **Human Review Audits:** `get_finding`, `update_finding_review`
- **Job Reconciler:** `reconcile_incomplete_jobs`

---

## 2. Dynamic Repository Factory

In `apps/backend/src/plagiarism/storage/local_db.py`, the `get_local_repo()` factory was updated to dynamically select the repository implementation:

```python
def get_local_repo() -> Any:
    global _local_repo
    if _local_repo is None:
        settings = get_settings()
        if getattr(settings, "APP_RUNTIME_MODE", "local") == "production":
            try:
                from plagiarism.storage.pg_db import get_pg_repo
                _local_repo = get_pg_repo()
            except Exception as e:
                logger.warning(f"Could not initialize PostgresMetadataRepository ({e}); falling back to LocalMetadataRepository")
                _local_repo = LocalMetadataRepository()
        else:
            _local_repo = LocalMetadataRepository()
    return _local_repo
```

This guarantees that in native Windows localhost development mode (`APP_RUNTIME_MODE=local`), SQLite is used without requiring an external database, while in production mode (`APP_RUNTIME_MODE=production`), PostgreSQL is automatically engaged.
