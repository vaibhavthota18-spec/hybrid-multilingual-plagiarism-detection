# 12 — Production Deployment Configuration & Environment Variables

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Files:** `.env.production.example`, `render.yaml`, `compose.yaml`  
**Status:** COMPLETE  

---

## 1. Master Production Environment Configuration

The following environment variables configure the production runtime across all nodes:

```bash
# Core Mode
APP_RUNTIME_MODE=production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://plagiarism_user:<SECURE_PASSWORD>@<DB_HOST>:5432/plagiarism_platform
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=5

# Redis Queue
REDIS_URL=redis://default:<REDIS_PASSWORD>@<REDIS_HOST>:6379
WORKER_QUEUE_NAME=default
JOB_TIMEOUT_SECONDS=600

# Private Storage
STORAGE_BACKEND=local
STORAGE_ROOT_DIR=/app/storage
LOCAL_PRIVATE_STORAGE_ROOT=/app/storage/private
MAX_UPLOAD_SIZE_BYTES=31457280

# Security & CORS
JWT_SECRET_KEY=<SECURE_RANDOM_SECRET_KEY_MIN_64_CHARS>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=["https://plagiarism-web.onrender.com"]

# AI Model
SEMANTIC_MODEL_NAME=intfloat/multilingual-e5-small
SEMANTIC_MODEL_REVISION=614241f622f53c4eeff9890bdc4f31cfecc418b3
SEMANTIC_EMBEDDING_DIM=384
SEMANTIC_MAX_SEQ_LENGTH=512
SEMANTIC_DEVICE=cpu
SEMANTIC_PARAPHRASE_THRESHOLD=0.82
SEMANTIC_TRANSLATION_THRESHOLD=0.80

# Chromium Headless PDF Generation
CHROMIUM_PATH=/usr/bin/chromium
```

---

## 2. Production Startup Sequence

1. **Database Readiness:** Container runs `pg_isready` check until PostgreSQL accepts connections.
2. **Schema Migration:** Alembic runs `alembic upgrade head`, applying `0001_initial_schema` and `0002_pgvector_384_dimensions`.
3. **Queue Activation:** Redis responds with `PONG`.
4. **Worker Initialization:** `plagiarism_worker` connects to Redis and begins listening on `default` queue.
5. **API Boot:** Uvicorn starts FastAPI workers with unprivileged `appuser`.
6. **Frontend Proxy:** Nginx starts on port 80, routing `/` to React SPA and `/api/` to backend.
