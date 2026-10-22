# ADR-0007: Background Job Architecture (Redis + Python RQ)

- **Status:** Accepted
- **Deciders:** Principal Software Architect, Senior Backend Architect, DevOps Engineer
- **Date:** October 2026
- **Technical Story:** Asynchronous job processing, message queuing, and worker strategy

---

## Context
Document ingestion, text extraction, Winnowing fingerprinting, transformer embedding inference, passage alignment, and PDF generation are CPU-intensive operations. Executing these inside synchronous HTTP request/response lifecycles causes connection timeouts (HTTP 504), worker process starvation, and poor user experience.
The architecture requires a dependable, lightweight asynchronous task processing mechanism.

## Decision
We select **Redis 7+ with Python RQ (Redis Queue)** as the single, authoritative background task execution engine for all asynchronous workloads.
- **Queue Engine:** Redis 7+ in Docker.
- **Worker Library:** Python `rq` with worker processes executing the unified backend package (`apps/backend/src/plagiarism/jobs/`).
- **State Synchronization:** Job state (`queued`, `processing`, `completed`, `failed`, `cancelled`) is mirrored into the PostgreSQL `analysis_jobs` table with timestamps, error codes, and progress percentages.

## Alternatives Considered & Fallback Strategy
1. **Celery:**
   - *Evaluation:* Celery is feature-rich but significantly more complex to configure, maintain, and debug. It introduces intricate broker/result-backend settings, Windows process execution quirks, and heavy dependencies.
   - *Fallback Strategy:* If Phase 7 load testing demonstrates that specialized task priority routing across multi-language worker pools cannot be serviced by RQ, Celery will serve as the secondary fallback. To preserve portability, all job functions in `apps/backend/src/plagiarism/jobs/` are authored as standard Python callables decoupled from RQ internals.
2. **FastAPI BackgroundTasks:** Rejected because it runs in-process inside the web server process. Long CPU-intensive embedding generation blocks the event loop and is destroyed if the web container restarts.

## Rationale
- RQ is simple, stable, transparent, and native to Python.
- Redis is already lightweight and low-memory (~50 MB baseline RAM).
- Decouples long-running ML tasks from the web server, allowing worker containers to be scaled horizontally according to CPU/GPU availability.

## Consequences & Trade-offs
- **Positive:** Fast API response times ($<200$ ms for HTTP 202 Accepted); isolated worker crashes do not terminate web traffic; transparent job inspection via `rq-dashboard` or API endpoints.
- **Negative:** Requires running and monitoring Redis and at least one worker daemon process.

## Validation Requirements
Automated queue integration tests verifying task dispatch, progress reporting, timeout handling (10-minute cap), and error state transitions.
