# 15 — Production Monitoring, Observability, and Health Checks

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Status:** COMPLETE  

---

## 1. Multi-Tier Health Probes

Every service in the production cluster exposes lightweight, deterministic health check probes:

| Service | Endpoint / Command | Type | Target Response / Criteria | Interval / Timeout |
|---|---|---|---|---|
| **Nginx Web** | `http://localhost:80/health` | HTTP GET | HTTP 200 `{"status":"healthy","service":"web"}` | 15s / 5s |
| **FastAPI Backend** | `http://localhost:8000/health` | HTTP GET | HTTP 200 `{"status":"healthy","database":"connected","queue":"ready"}` | 15s / 5s |
| **PostgreSQL** | `pg_isready -U postgres -d plagiarism_platform` | CLI Shell | Exit Code 0 | 10s / 5s |
| **Redis** | `redis-cli ping` | CLI Shell | `PONG` (Exit Code 0) | 10s / 5s |
| **RQ Worker** | Heartbeat daemon ping | Redis Key | TTL refresh within 60s | Continuous |

---

## 2. Structured JSON Logging

All logs are formatted as structured JSON payloads containing:
- `timestamp`: UTC ISO 8601 string
- `level`: `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `service`: `plagiarism-backend`, `plagiarism-worker`, or `plagiarism-web`
- `request_id`: Tracing UUID propagated across API calls
- `user_id`: Authenticated principal UUID (redacted in public logs)
- `duration_ms`: Execution time for analysis operations and document parsing
