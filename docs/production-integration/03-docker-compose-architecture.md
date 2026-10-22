# 03 — Docker Compose Architecture and Container Topography

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Files:** `compose.yaml`, `Dockerfile` (Backend/Worker), `Dockerfile` (Web)  
**Status:** COMPLETE  

---

## 1. Container Topography

The containerized stack consists of five tightly coupled services operating on an isolated bridge network (`plagiarism_net`):

```
                        +----------------------------+
                        |       Client Browser       |
                        +--------------+-------------+
                                       |
                                       | HTTP :3000
                                       v
                        +----------------------------+
                        |   plagiarism_web (Nginx)   |
                        +--------------+-------------+
                                       | Reverse Proxy (/api/)
                                       v
                        +----------------------------+
                        |   plagiarism_api (FastAPI) |
                        +--------+----------+--------+
                                 |          |
                   PostgreSQL    |          | Redis Enqueue
                   Port 5432     |          | Port 6379
                                 v          v
+-----------------------+ +--------------+ +---------------------+
| plagiarism_db         | | Shared Disk  | | plagiarism_redis    |
| (pgvector / pg16)     | | (storage_vol)| | (Redis 7.2-alpine)  |
+-----------------------+ +-------+------+ +----------+----------+
                                  ^                   |
                                  | Shared Disk       | Dequeue Job
                                  |                   v
                        +---------+------------------+
                        | plagiarism_worker (Python RQ) |
                        +----------------------------+
```

---

## 2. Service Specifications

| Service | Image / Build Context | Ports | Storage Volumes | Healthcheck |
|---|---|---|---|---|
| **`db`** | `pgvector/pgvector:pg16` | `5432:5432` | `postgres_data:/var/lib/postgresql/data` | `pg_isready -U postgres -d plagiarism_platform` |
| **`redis`** | `redis:7.2-alpine` | `6379:6379` | `redis_data:/data` | `redis-cli ping` |
| **`api`** | `./apps/backend/Dockerfile` | `8000:8000` | `storage_volume:/app/storage` | `curl -f http://localhost:8000/health` |
| **`worker`** | `./apps/backend/Dockerfile` | — | `storage_volume:/app/storage` | Managed by RQ heartbeat |
| **`web`** | `./apps/web/Dockerfile` | `3000:80` | None (Static bundle) | `wget -q -O - http://localhost:80/health` |

---

## 3. Volume Persistence & Shared State

1. **`postgres_data`:** Named volume persisting relational tables, Alembic migration state, and pgvector HNSW embedding index trees across container reboots.
2. **`redis_data`:** Named volume storing Redis Append-Only File (AOF) state, preserving queued jobs and execution history.
3. **`storage_volume`:** Shared volume mounted at `/app/storage` in both `api` and `worker`. When an upload arrives at the API container, it is saved into `/app/storage/private/`, and the background worker reads directly from the same path without cross-container network transmission.
