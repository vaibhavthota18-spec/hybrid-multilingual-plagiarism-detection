# 07 — Redis Queue & Python RQ Background Worker Architecture

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Files:** `apps/backend/src/plagiarism/jobs/worker.py`, `apps/backend/src/plagiarism/jobs/tasks.py`, `apps/backend/src/plagiarism/services/executor.py`  
**Status:** IMPLEMENTED & VERIFIED  

---

## 1. Background Worker Architecture

In production mode (`APP_RUNTIME_MODE=production`), long-running document extraction and hybrid similarity analyses are offloaded from FastAPI HTTP request threads to dedicated Python RQ background workers connected via Redis 7.2.

```
FastAPI HTTP Request
      |
      v
executor.submit_analysis()
      |
      +---> [APP_RUNTIME_MODE == "production"] ---> Enqueue to RQ Queue (Redis :6379)
      |                                                    |
      |                                                    v
      |                                            plagiarism_worker
      |                                            (Python RQ Daemon)
      |                                                    |
      |                                                    +-> Winnowing
      |                                                    +-> BM25 Retrieval
      |                                                    +-> E5 Inference
      |                                                    +-> Interval Union
      |                                                    +-> Postgres Persistence
      |
      +---> [APP_RUNTIME_MODE == "local"] -----------> Local ThreadPoolExecutor
```

---

## 2. Queue Configuration & Retry Resilience

1. **Job Enqueueing:** `executor.py` enqueues tasks using `plagiarism.jobs.tasks.process_document_job` and `run_hybrid_analysis_job`.
2. **Exponential Backoff Retries:** Tasks use RQ's `Retry` handler:
   ```python
   retry = Retry(max=3, interval=[10, 30, 60])
   ```
3. **Execution Timeouts:**
   - Document Extraction: 600 seconds (10 minutes)
   - Hybrid Similarity Analysis: 1,200 seconds (20 minutes)
4. **Interrupted Job Reconciliation:** On startup, `reconcile_incomplete_jobs()` scans PostgreSQL for any jobs left in `processing` status due to unexpected container termination and safely transitions them to `failed`, preventing zombie locks.
