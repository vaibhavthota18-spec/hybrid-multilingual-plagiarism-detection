# Phase 1: Environment and Setup Guide

**System:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Phase:** 1 of 7  
**Status:** Approved  
**Date:** October 2026  
**Document Version:** 1.0.0  

---

## 1. Prerequisites and Environmental Matrix

The application foundation is engineered to run seamlessly across developer workstations and production clusters.

### 1.1 Host Tooling Requirements (Local Development)
* **Operating System:** Windows 11 / Linux (Ubuntu 22.04+) / macOS (Sonoma+)
* **Container Runtime (Recommended):** Docker Desktop (with WSL2 engine on Windows) or Docker Engine 24.0+ with Compose v2
* **Python Runtime (Optional for direct host execution):** Python 3.11 or 3.12 (with `pip` and `virtualenv`)
* **Node.js Runtime (Optional for direct host execution):** Node.js 20 LTS (with `npm` or `pnpm`)
* **PostgreSQL (Optional for host mode):** PostgreSQL 16 with `pgvector` extension installed
* **Redis (Optional for host mode):** Redis 7.0+

---

## 2. Environment Variables Specification

The system uses Pydantic v2 `BaseSettings` reading from environment variables or a `.env` file at the root.

| Variable Name | Default Value | Required in Production | Description |
| :--- | :--- | :---: | :--- |
| `ENVIRONMENT` | `development` | Yes | Runtime environment (`development`, `testing`, `production`). |
| `DEBUG` | `true` | Yes | Enable debug traceback. Must be `false` in production. |
| `SERVICE_NAME` | `plagiarism-backend` | No | Service identifier emitted in structured JSON logs. |
| `APP_VERSION` | `1.0.0` | No | Application semantic version. |
| `POSTGRES_HOST` | `localhost` (or `db` in Docker) | Yes | PostgreSQL server hostname. |
| `POSTGRES_PORT` | `5432` | Yes | PostgreSQL port. |
| `POSTGRES_DB` | `plagiarism_platform` | Yes | Database name. |
| `POSTGRES_USER` | `postgres` | Yes | Database user. |
| `POSTGRES_PASSWORD` | `postgres_dev_password_change_in_production` | Yes | Database password. |
| `REDIS_HOST` | `localhost` (or `redis` in Docker) | Yes | Redis server hostname. |
| `REDIS_PORT` | `6379` | Yes | Redis port. |
| `REDIS_DB` | `0` | No | Redis database index. |
| `JWT_SECRET_KEY` | *(dev key)* | Yes | Cryptographic HMAC secret. Must be >= 32 characters in production. |
| `JWT_ALGORITHM` | `HS256` | No | Pinned cryptographic algorithm. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | No | Bearer token validity period in minutes. |
| `STORAGE_ROOT` | `./storage` (or `/app/storage` in Docker) | Yes | Base filesystem directory for uploads and generated reports. |
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:5173"]` | Yes | Allowed web origins. |

---

## 3. OneDrive Synchronization Shielding

The project root is located within a OneDrive-synchronized folder:  
`C:\Users\vaibh\OneDrive\Documents\plagarism engine`

Running high-throughput databases or hot-reloading file watchers directly inside OneDrive-synchronized folders can trigger file lock contention (`EPERM` / `EBUSY`), excessive network bandwidth consumption, and file corruption.

### Mitigation Strategies Implemented:
1. **Named Docker Volumes:**
   * PostgreSQL data is mounted to named volume `plagiarism_postgres_data`.
   * Redis persistence is mounted to named volume `plagiarism_redis_data`.
   * Raw document storage is mounted to named volume `plagiarism_storage_volume`.
   Named volumes reside inside the Docker VM / WSL2 ext4 filesystem, completely isolated from OneDrive.
2. **Git & Sync Ignores:**
   * Node modules (`node_modules`), Python bytecode (`__pycache__`), virtual environments (`.venv`), build artifacts (`dist`, `build`), and local storage (`storage/`) are registered in `.gitignore` and `.dockerignore`.

---

## 4. Execution Procedures

### 4.1 Recommended: One-Command Docker Compose

```powershell
# From project root
powershell -ExecutionPolicy Bypass -File scripts\run_local.ps1 -Build
```

Or using standard Docker Compose:
```bash
docker compose up -d --build
```

#### Service Endpoints:
* **Web Application:** [http://localhost:3000](http://localhost:3000)
* **Backend API Root:** [http://localhost:8000](http://localhost:8000)
* **OpenAPI Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **OpenAPI Documentation (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Probe Endpoint:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 4.2 Manual Host Execution (Without Docker)

If Docker is not running on the host:
```bash
# Terminal 1: Database & Redis (Host services)
# Ensure PostgreSQL 16 + pgvector is listening on 5432 and Redis on 6379

# Terminal 2: Backend API
cd apps/backend
pip install -e .
alembic upgrade head
uvicorn plagiarism.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Background Worker Daemon
cd apps/backend
python -m plagiarism.jobs.worker

# Terminal 4: Frontend Web App
cd apps/web
npm install
npm run dev
# Web app will be accessible at http://localhost:5173
```
