# 04 — Redis Queue & RQ Worker Dispatch Verification

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Milestone:** Live Deployment & Production Verification Audit  
**Date:** 2026-10-16  
**Files:** `apps/backend/src/plagiarism/jobs/worker.py`, `apps/backend/src/plagiarism/jobs/tasks.py`, `apps/backend/src/plagiarism/services/executor.py`  
**Status:** CODE COMPLETE & SYNTHETICALLY VERIFIED  

---

## 1. Background Worker Lifecycle & Dispatch

The worker integration ensures that computationally intensive AI analysis does not degrade HTTP response times:

```
[Client Request: POST /api/v1/analyses]
                  |
                  v
[FastAPI create_analysis()]
                  |
         [APP_RUNTIME_MODE]
        /                  \
 (production)            (local)
      v                     v
[Enqueue to Redis]     [ThreadPoolExecutor]
      |                     |
      v                     v
[plagiarism_worker]    [In-process Thread]
      |                     |
      +---> Executed: run_hybrid_analysis_job()
            - Winnowing Lexical Detection
            - BM25 Candidate Retrieval
            - E5 Small Vector Inferences
            - Interval Union Coverage Calculation
            - PostgreSQL Result Persistence
```

---

## 2. Worker Test Suite & Fault Recovery

The worker test suite was executed via `pytest apps/backend/tests/test_worker.py`:
- `test_ping_job`: Validated task parameter serialization, PID verification, and SHA-256 output checksums.
- `test_simulate_calculation`: Validated deterministic mathematical operations.
- `test_simulate_calculation_division_by_zero`: Validated exception trapping.
- `test_simulate_calculation_invalid_op`: Validated input sanitization.
- `test_failing_job`: Validated worker exception logging and retry handling.

**Result:** **5 passed out of 5 tests in 0.02s**.
