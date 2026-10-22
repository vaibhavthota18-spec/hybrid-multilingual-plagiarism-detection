# Phase 7 — Backend Reliability & Background Execution

## 1. Local Task Scheduling & ThreadPool Hardening
The backend utilizes `LocalProcessingExecutor` with a bounded Python `concurrent.futures.ThreadPoolExecutor(max_workers=2)`.

### Key Hardening Measures:
1. **Bounded Concurrency:** Limits active concurrent extraction and analysis tasks to prevent CPU starvation and excessive RAM consumption on laptop hardware.
2. **Interrupted Job Reconciliation:**
   - On startup, `LocalMetadataRepository.reconcile_incomplete_jobs()` executes automatically:
     - Documents in `status = 'processing'` are updated to `status = 'failed'` with warning `"Processing interrupted by server restart"`.
     - Analyses in `status IN ('queued', 'processing')` are transitioned to `status = 'failed'` with `error_code = 'INTERRUPTED'` and message `"Analysis interrupted by server restart"`.
   - Prevents stale jobs from being permanently stuck in `processing`.
3. **Graceful Exception Propagation:**
   - Analysis execution exceptions are captured and stored in the database record with exact error message and timestamp, preventing unhandled background thread crashes.

## 2. API Error Handling Architecture
- Standard error envelope conforming to Phase 0 contracts:
```json
{
  "error": {
    "code": "BAD_REQUEST | NOT_FOUND | UNAUTHORIZED | FORBIDDEN | VALIDATION_ERROR",
    "message": "Human readable explanation",
    "status": 400,
    "timestamp": "2026-10-15T01:50:00Z",
    "request_id": "uuid",
    "details": []
  }
}
```
- No internal stack traces or database driver paths leaked in production or user-facing responses.
