# Phase 1 Implementation Handoff Blueprint

> **Target Phase:** Phase 1 — Engineering Foundation  
> **Source Milestone:** Phase 0 — Blueprint & Architecture Complete  
> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Date:** October 2026  

---

## 1. Phase 1 Objective & Charter

The charter of **Phase 1 (Engineering Foundation)** is to establish the operational engineering skeleton of the platform. By the conclusion of Phase 1, the developer will be able to run `docker compose up` and access a live React frontend talking to a live FastAPI backend, with authenticated sessions, database migrations in PostgreSQL (`pgvector`), a healthy Redis worker pool, and passing CI/CD pipelines.

> **Scope Boundary:** Phase 1 establishes infrastructure, skeletons, database foundations, and worker wiring. **Document text extraction (PyMuPDF), Winnowing fingerprinting, AI embedding downloads, and comparison algorithms are OUT OF SCOPE for Phase 1** (scheduled for Phases 2, 3, and 4).

---

## 2. Phase 1 Deliverables & Scope Checklist

### 2.1 Project Scaffolding & Monorepo Wiring
- Initialize `apps/web/` using Vite + React 18 + TypeScript + Tailwind CSS.
- Initialize `apps/backend/` as a modular Python package with `pyproject.toml` (Poetry or Pip-tools / hatchling).
- Configure root `compose.yml` orchestrating `web`, `backend`, `worker`, `db`, and `redis`.
- **OneDrive Isolation Invariant:** In `compose.yml`, define named volumes (`postgres_data`, `storage_volume`) rather than host bind-mounts into the OneDrive root directory. This protects against host file locks (`EPERM`) and cloud upload churn.

### 2.2 Database & Persistence Foundations
- Spin up PostgreSQL 16 with `pgvector` enabled in Docker using named volume `postgres_data`.
- Initialize Alembic in `apps/backend/alembic/` configured for asynchronous execution via `asyncpg`.
- Author initial baseline migration (`0001_initial_schema.py`) implementing core tables from `docs/03-data/data-model.md`:
  - `users`, `collections`, `collection_permissions`, `documents`, `passages`, `embeddings` (with vector type), `analyses`, `analysis_jobs`, `deletion_ledger`.
- Verify database connectivity and migration execution on container startup.

### 2.3 Backend API Foundation (FastAPI)
- Initialize FastAPI application in `apps/backend/src/plagiarism/`.
- Implement global middleware: CORS (configurable via `.env`), structured JSON request logging with correlation IDs, error handlers converting exceptions to standard RFC 7807 error envelopes (`docs/02-api/api-design.md`).
- Implement `GET /api/v1/health` returning database and Redis connection statuses (`contracts/openapi.yaml`).
- Implement basic JWT authentication endpoints (`/api/v1/auth/login`, `/api/v1/auth/refresh`) and user context dependency.
- Integrate automated OpenAPI generation and verify schema conformance against `contracts/openapi.yaml`.

### 2.4 Background Worker Foundation (Redis + Python RQ)
- Configure Redis 7 container with append-only persistence.
- Implement RQ worker entrypoint (`apps/backend/src/plagiarism/jobs/worker.py`).
- Implement a lightweight probe job (`ping_job`) to verify that the API server can enqueue tasks into Redis and the worker pool successfully processes them, updating job status in `analysis_jobs`.

### 2.5 Frontend Foundation (React + TypeScript)
- Configure Tailwind CSS theme and typography plugins.
- Set up React Router with shell layouts (Navbar, Sidebar, Main Content, Footer).
- Run `openapi-typescript` against `contracts/openapi.yaml` to generate initial typed API client interfaces in `apps/web/src/types/generated/api.ts`.
- Build basic health status indicator page verifying end-to-end communication with the backend.

### 2.6 CI/CD & Automated Testing Pipelines
- Create `.github/workflows/ci.yml`:
  - Frontend: ESLint, TypeScript `tsc --noEmit`, Vitest unit test runner.
  - Backend: Ruff (lint & format), mypy, pytest with asyncpg test runner.
  - OpenAPI: Schema validation.

---

## 3. Dependency Inventory for Phase 1

### Backend Dependencies (`pyproject.toml`)
- `python = ">=3.11,<3.13"`
- `fastapi >= 0.110.0`
- `uvicorn[standard] >= 0.28.0`
- `pydantic >= 2.6.0`
- `pydantic-settings >= 2.2.0`
- `sqlalchemy[asyncio] >= 2.0.28`
- `asyncpg >= 0.29.0`
- `alembic >= 1.13.1`
- `pgvector >= 0.2.5`
- `redis >= 5.0.3`
- `rq >= 1.16.1`
- `python-jose[cryptography] >= 3.3.0`
- `passlib[bcrypt] >= 1.7.4`
- `python-multipart >= 0.0.9`
- `pytest`, `pytest-asyncio`, `httpx` (Dev / Test)

### Frontend Dependencies (`package.json`)
- `react >= 18.2.0`, `react-dom >= 18.2.0`
- `typescript >= 5.3.0`
- `vite >= 5.1.0`
- `tailwindcss >= 3.4.0`, `autoprefixer >= 10.4.0`, `postcss >= 8.4.0`
- `lucide-react >= 0.350.0`
- `openapi-typescript >= 6.7.0` (Dev)
- `vitest >= 1.3.0` (Dev)

---

## 4. Phase 1 Acceptance Gates

Phase 1 will be considered complete and ready for Phase 2 handoff when:
1. `docker compose up` starts all 5 containers cleanly with zero crashes.
2. `curl http://localhost:8000/api/v1/health` returns `200 OK` with `{"status": "healthy", "database": "connected", "redis": "connected"}`.
3. Database migrations apply automatically and create all tables defined in `data-model.md`.
4. A test task enqueued via FastAPI executes successfully in the RQ worker daemon, updating PostgreSQL job status.
5. React frontend renders without errors and makes successful typed calls to `/api/v1/health`.
6. GitHub Actions CI pipeline passes all linting, typing, and unit tests.
7. Zero Phase 2+ features (PyMuPDF extraction, Winnowing, model weights) are implemented prematurely.
