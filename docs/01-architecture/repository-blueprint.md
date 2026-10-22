# Repository Blueprint & Directory Ownership

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Target Project Root:** `C:\Users\vaibh\OneDrive\Documents\plagarism engine`  
> **Date:** October 2026  

---

## 1. Permanent Repository Target Layout

The permanent repository layout is locked as follows. Phase 0 creates architectural, contract, and documentation files. Phases 1 through 7 will progressively populate code, tests, and configuration directories without altering the overarching tree structure.

```
plagarism engine/
├── .editorconfig                          # Text formatting & indentation rules
├── .env.example                           # Safe environment configuration template
├── .gitignore                             # Git exclusion patterns
├── AGENTS.md                              # Mandatory Antigravity agent operational rules
├── README.md                              # Master project overview & roadmap status
│
├── .github/
│   └── workflows/                         # CI/CD pipelines (Lint, Test, Security, Build)
│
├── apps/
│   ├── web/                               # Frontend Single Page Application (React + Vite)
│   │   ├── public/                        # Static web assets (favicon, icons)
│   │   ├── src/
│   │   │   ├── app/                       # Application routers and global providers
│   │   │   ├── pages/                     # Top-level route views (Home, Compare, Results, Corpus)
│   │   │   ├── features/                  # Domain-driven feature modules
│   │   │   │   ├── auth/                  # Authentication, login, session management
│   │   │   │   ├── documents/             # Upload dropzones, document lists, deletion
│   │   │   │   ├── collections/           # Corpus management and permissions UI
│   │   │   │   ├── analyses/              # Analysis triggering and progress tracking
│   │   │   │   ├── reports/               # Interactive side-by-side diff viewer & export
│   │   │   │   └── reviews/               # Human review annotation panel
│   │   │   ├── components/                # Reusable UI primitives (Buttons, Modals, Badges)
│   │   │   ├── hooks/                     # Custom React hooks (polling, window size, auth)
│   │   │   ├── lib/                       # Utility libraries and API client wrappers
│   │   │   │   └── api/                   # Typed fetch/axios client
│   │   │   ├── types/
│   │   │   │   └── generated/             # TypeScript types generated from OpenAPI schema
│   │   │   └── styles/                    # Tailwind CSS globals and theme configurations
│   │   └── tests/                         # Frontend unit and component tests (Vitest, Playwright)
│   │
│   └── backend/                           # Python Monolithic Backend Application
│       ├── alembic/                       # Database migration scripts (PostgreSQL + pgvector)
│       │   └── versions/                  # Revision versions
│       ├── src/
│       │   └── plagiarism/                # Top-level backend package
│       │       ├── api/
│       │       │   └── v1/                # FastAPI router endpoints (/documents, /analyses, etc.)
│       │       ├── core/                  # Application configuration, settings, logging, security
│       │       ├── domain/                # Pydantic schemas and domain entities
│       │       ├── db/                    # SQLAlchemy async engine, base models, session makers
│       │       ├── services/
│       │       │   ├── ingestion/         # File validation, upload handling, MIME inspection
│       │       │   ├── extraction/        # PyMuPDF, python-docx, and TXT extractors
│       │       │   ├── preprocessing/     # Normalization, language detection, segmentation
│       │       │   ├── fingerprinting/    # Winnowing rolling hash algorithm & indexing
│       │       │   ├── retrieval/         # BM25, exact vector search, candidate fusion
│       │       │   ├── alignment/         # Token-level local sequence alignment
│       │       │   ├── scoring/           # Coverage calculations, exclusion filtering
│       │       │   ├── corpora/           # Reference collection ingestion & access control
│       │       │   └── reporting/         # PDF report generator (ReportLab / WeasyPrint)
│       │       ├── ml/                    # Multilingual embedding inference (multilingual-e5-base)
│       │       ├── jobs/                  # Redis Queue (RQ) worker definitions & handlers
│       │       ├── storage/               # File storage abstraction (local disk, volume unlinking)
│       │       └── observability/         # Prometheus metrics, structured logging handlers
│       └── tests/                         # Pytest test suite (unit, integration, functional)
│
├── contracts/                             # Authoritative API and Data Contracts
│   ├── openapi.yaml                       # OpenAPI 3.1 specification for API v1
│   ├── README.md                          # Contract usage & generation instructions
│   └── examples/                          # Canonical JSON request and response payloads
│
├── evaluation/                            # Benchmarking, Datasets, and Evaluation Suite
│   ├── configs/                           # Evaluation run configuration YAMLs
│   ├── datasets/
│   │   └── manifests/                     # Metadata manifests for pilot (360) and full (900) sets
│   ├── annotation/                        # Annotation schemas and guidelines for human annotators
│   ├── benchmarks/                        # Monolingual & cross-lingual benchmark runners
│   ├── scripts/                           # Accuracy, recall, IoU, and latency evaluation scripts
│   └── results/                           # Evaluation run outputs and confusion matrices
│
├── infra/                                 # Infrastructure and Deployment Configurations
│   ├── docker/
│   │   ├── Dockerfile.web                 # Multi-stage Docker build for React frontend
│   │   ├── Dockerfile.backend             # Multi-stage Docker build for FastAPI API server
│   │   └── Dockerfile.worker              # Docker build for Python background worker
│   ├── deployment/                        # Reverse proxy (Nginx / Caddy), SSL, environment templates
│   └── compose.yml                        # Docker Compose orchestration definition
│
├── docs/                                  # Comprehensive System Documentation Hierarchy
│   ├── 00-product/                        # Product charters, user journeys, requirements (SRS)
│   ├── 01-architecture/                   # System design, module contracts, blueprint, tech decisions
│   │   └── adrs/                          # Architecture Decision Records (ADR-0001 to ADR-0008)
│   ├── 02-api/                            # API design, REST guidelines, error catalogs
│   ├── 03-data/                           # Database models, offset mathematics, index lifecycle
│   ├── 04-security/                       # Threat modeling, privacy policies, data retention
│   ├── 05-evaluation/                     # Benchmark designs, dataset splits, model comparison
│   ├── 06-operations/                     # Deployment guide, capacity planning, observability
│   └── phases/                            # Phase tracking, audits, verification reports
│       └── phase-00/                      # Phase 0 deliverables & validation
│
└── scripts/                               # Maintenance, validation, and developer automation scripts
```

---

## 2. Directory Ownership, Scope & Dependency Rules

| Directory Path | Owning Subsystem | Target Phase | Allowed Dependencies | Strictly Prohibited Dependencies |
|---|---|---|---|---|
| `apps/web/` | Senior Frontend Architect | Phase 1 & Phase 6 | React, TypeScript, Tailwind, Lucide icons, OpenAPI generated client | Must NOT import Python modules, raw database drivers, or backend internal files |
| `apps/backend/` | Senior Backend Architect | Phase 1–4 | Python 3.11, FastAPI, SQLAlchemy, Alembic, PyTorch, PyMuPDF, python-docx, Redis/RQ | Must NOT contain bundled React assets or direct frontend build artifacts |
| `contracts/` | API Design Lead | Phase 0 (Baseline), Phase 1 (Sync) | OpenAPI 3.1 tooling, JSON Schema | Must NOT contain application runtime business logic |
| `evaluation/` | ML Evaluation Engineer | Phase 5 | Python test runners, pandas, scikit-learn, metric evaluators | Must NOT depend on production cloud state; must use reproducible datasets |
| `infra/` | DevOps Engineer | Phase 1 & Phase 7 | Docker, Docker Compose, Linux system packages | Must NOT contain hardcoded production secrets or private user data |
| `docs/` | Technical Documentation Engineer | Phase 0 (Continuous) | Markdown, Mermaid | Must NOT contain executable binaries |
| `scripts/` | Tooling & QA Lead | Phase 0–7 | PowerShell, Bash, Python utility libraries | Must NOT bypass API security boundaries |

---

## 3. Phase 0 Implementation Safeguards

- **No Empty Placeholders:** Empty directories or fake code files are NOT generated in Phase 0.
- **No Early Framework Initialization:** `npm create vite` or `pip install fastapi` must not be executed during Phase 0; framework bootstrapping is the explicit charter of Phase 1.
- **No Mock Implementations:** Fake functions or mock endpoints must not be written to masquerade as functional code.
