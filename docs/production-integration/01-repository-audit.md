# 01 — Repository Audit & Baseline Verification

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Environment:** Windows 11 Localhost & Linux Container Architecture  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary

This audit establishes the baseline architectural state of the repository before executing the final production infrastructure migration. All functional capabilities developed during Phases 0 through 7—including lexical winnowing ($k=25, w=16$), BM25 candidate retrieval, multilingual semantic sentence embeddings (`intfloat/multilingual-e5-small`), hybrid interval-union coverage calculation, human reviewer decision audit workflows, and multi-format report exports (PDF, HTML, JSON)—were audited and verified to be 100% operational.

---

## 2. Repository Layout & Component Inspection

| Component | Path | Language / Tech | Responsibilities |
|---|---|---|---|
| **API Backend** | `apps/backend/` | Python 3.12, FastAPI, Pydantic | REST API, OpenAPI 3.1 contracts, auth, document ingestion, similarity engine, report generation |
| **Frontend SPA** | `apps/web/` | React 18, TypeScript, Vite, Tailwind CSS | Minimalist iLovePDF-inspired 5-step plagiarism detection workflow, report downloads, evidence review |
| **Contracts** | `contracts/` | OpenAPI 3.1 YAML | Strictly enforced REST API contracts and schema models |
| **Database Migrations**| `apps/backend/alembic/` | Alembic, SQLAlchemy | Versioned database schema definitions including pgvector extension |
| **Storage Subsystem** | `storage/` | Private filesystem / SQLite | Local private uploaded documents (`storage/private/`), SQLite database (`storage/local_metadata.db`) |
| **Infrastructure** | `infra/` & Root | Docker, Docker Compose, Nginx | Multi-stage Dockerfiles, Compose orchestration, Nginx reverse proxy |
| **Automation Scripts** | `scripts/` | Python, PowerShell | E2E verification, evaluation benchmarks, backup/restore, SQLite-to-PostgreSQL migration |

---

## 3. Algorithmic Invariants Preserved

During the transition from SQLite development mode to production containerization and PostgreSQL + pgvector, the following algorithmic invariants were strictly preserved with zero alterations:
1. **Lexical Winnowing:** Character k-gram size $k = 25$, window size $w = 16$.
2. **BM25 Lexical Retrieval:** Top-K passage candidate retrieval with exact match filtering ($\ge 10$ tokens).
3. **Multilingual Dense Embeddings:** Dense vector model `intfloat/multilingual-e5-small` with 384 dimensions. Cosine similarity threshold for paraphrases: 0.82; cross-language threshold: 0.80.
4. **Interval Union Coverage:** Exact byte-offset interval unions preventing double-counting of overlapping lexical and semantic matches.
5. **Human Review Decisions:** Audit ledger recording keep, exclude, and quoted/cited decisions with recalculation of net adjusted coverage.

---

## 4. Test Suite Baseline Results

| Suite | Tests Executed | Passed | Failed | Execution Time | Result |
|---|---|---|---|---|---|
| **Backend (pytest)** | 108 | 108 | 0 | 72.97s | **100% PASS** |
| **Frontend (vitest)** | 20 | 20 | 0 | 19.21s | **100% PASS** |
| **Vite Production Build** | Full Bundle | Success | 0 errors | 8.63s | **100% PASS** |

Both test suites pass completely without failures or regressions.
