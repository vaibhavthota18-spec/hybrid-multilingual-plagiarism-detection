# Phase 7 — Architecture Preservation & Isolation

## 1. Dual-Architecture Coexistence Model
To satisfy the user's non-negotiable requirement for zero Docker/WSL2 and zero external server installations, the codebase strictly maintains two isolated execution tiers:

```mermaid
flowchart TD
    subgraph Core["Domain Core & Detection Logic (Shared)"]
        Extractors["Document Extraction & Normalization"]
        Lexical["Winnowing & BM25 Algorithms"]
        Semantic["Multilingual E5 Small Inference"]
        Review["Reviewer Interval Union Recalculation"]
        Reports["PDF/HTML/JSON Report Engine"]
    end

    subgraph LocalTier["Tier 1: Native Windows Localhost (Active & Verified)"]
        SQLiteDB["SQLite Metadata Repository (WAL Mode)"]
        BlobVector["SQLite Float32 BLOB Vector Store"]
        ThreadPool["Bounded Python ThreadPoolExecutor"]
        LocalFiles["Private Host Filesystem Storage"]
        DevAuth["Isolated Development Principal Guard"]
    end

    subgraph ProdTier["Tier 2: Production Infrastructure (Preserved Specifications)"]
        PostgresDB["PostgreSQL 16 Enterprise Relational Schema"]
        PgVector["pgvector HNSW Dense Indexing"]
        RedisRQ["Redis 7 + RQ Distributed Task Queues"]
        S3Storage["S3 / MinIO Object Storage with SSE-S3"]
        JWTAuth["Asymmetric RS256 Institutional JWT"]
    end

    Core --> LocalTier
    Core -.-> ProdTier
```

## 2. Preservation Audit
- **Alembic Migrations:** Preserved in `infra/migrations/` and `apps/backend/alembic/`.
- **Docker Compose:** Preserved in `compose.yml` for future production containerization.
- **Contract Integrity:** Preserved in `contracts/openapi.yaml`.
- **Database Schema Equivalence:** The local SQLite tables mirrors the primary entities, columns, and foreign keys of the production PostgreSQL schema.
