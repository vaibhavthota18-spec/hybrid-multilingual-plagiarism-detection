# Environment Configuration & Observability Framework

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Environment Variables Specification

The system is configured via environment variables following Twelve-Factor App principles. Configuration is validated at application boot using Pydantic `BaseSettings`:

| Variable Name | Type | Default | Description & Security Impact |
|---|---|---|---|
| `ENVIRONMENT` | string | `development` | `development`, `staging`, `production`, `test`. Controls debug flags. |
| `LOG_LEVEL` | string | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`. Must be `INFO` in production. |
| `APP_SECRET_KEY` | string | `change-me` | Cryptographic key for session signing. **CRITICAL: Rotate in production.** |
| `API_V1_PREFIX` | string | `/api/v1` | URL prefix for all API routes. |
| `CORS_ORIGINS` | string | `http://localhost:5173` | Comma-delimited permitted web origins. |
| `DATABASE_URL` | string | `postgresql+asyncpg://...` | Asynchronous SQLAlchemy connection string. |
| `DATABASE_POOL_SIZE` | integer | `20` | PostgreSQL asyncpg connection pool size. |
| `REDIS_URL` | string | `redis://localhost:6379/0` | Connection URI for Redis message queue and caching. |
| `QUEUE_DEFAULT_NAME` | string | `plagiarism_jobs` | Task queue name for background worker daemons. |
| `JOB_TIMEOUT_SECONDS` | integer | `600` | Maximum runtime cap before worker terminates task. |
| `STORAGE_BACKEND` | string | `local` | `local` filesystem volume or `s3` bucket. |
| `STORAGE_ROOT_DIR` | string | `./storage` | Base filesystem directory for private file uploads. |
| `MAX_UPLOAD_SIZE_BYTES`| integer| `31457280` | File upload cap (30 MB). |
| `JWT_SECRET_KEY` | string | `change-me` | HMAC secret for signing JWT access tokens. |
| `AI_EMBEDDING_MODEL_ID`| string | `intfloat/multilingual-e5-base` | Hugging Face model identifier. |
| `AI_EMBEDDING_DEVICE` | string | `cpu` | `cpu` or `cuda`. Controls PyTorch execution device. |
| `AI_BATCH_SIZE` | integer | `16` | Passages per embedding inference forward pass. |
| `ENABLE_PROMETHEUS` | boolean| `true` | Exposes `/metrics` endpoint for Prometheus scraping. |

---

## 2. Structured JSON Logging & Privacy Redaction

All logs emitted by FastAPI and RQ workers use structured JSON format with standard correlation identifiers:

```json
{
  "timestamp": "2026-10-13T14:40:02.124Z",
  "level": "INFO",
  "logger": "plagiarism.services.retrieval",
  "trace_id": "9a8b7c6d-5e4f-3a2b-1c0d",
  "job_id": "8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  "user_id": "usr-11223344",
  "action": "candidate_retrieval_completed",
  "channel": "hybrid",
  "candidate_count": 34,
  "duration_ms": 342,
  "memory_rss_mb": 1140
}
```

### Privacy Safe-Harbor Filter
The logging pipeline enforces a strict redaction middleware. The following keys are **strictly scrubbed** and replaced with `[REDACTED]`:
- `password`, `secret`, `authorization`, `token`, `cookie`
- `raw_text`, `file_content`, `passage_text`, `submission_excerpt`

*Under no circumstances may raw submitted student text or document extracts be written to disk logs.*

---

## 3. Metrics Telemetry (Prometheus)

The platform exposes operational metrics on port 9090 (or `/metrics`):
- `plagiarism_analyses_total{mode, status}`: Counter of all completed/failed analyses.
- `plagiarism_analysis_duration_seconds{mode}`: Histogram of end-to-end analysis processing time.
- `plagiarism_queue_depth`: Gauge of pending jobs waiting in Redis.
- `plagiarism_embedding_inference_latency_seconds`: Latency of transformer forward passes.
- `plagiarism_active_workers`: Count of healthy background worker processes.

---

## 4. Operational Alerts & Thresholds

| Alert Name | Condition & Rule | Severity | Remediation Action |
|---|---|---|---|
| `HighQueueBacklog` | `plagiarism_queue_depth > 50` for 10 min | Warning | Scale up additional worker containers via Docker Compose. |
| `WorkerProcessFailure` | `rate(plagiarism_analyses_failed[5m]) > 0.05` | High | Inspect worker logs for memory exhaustion or model crash. |
| `DiskSpaceCritical` | Host storage volume $> 85\%$ utilized | Critical | Trigger purge of expired guest documents and prune temp files. |
| `HighAnalysisLatency` | `p95(analysis_duration) > 240s` for 15 min | Warning | Check CPU throttling or large multi-page document queue spikes. |
