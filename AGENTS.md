# Antigravity Agent Guidelines & Rules of Engagement

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Master Specification:** Finalized Version 3.0  
> **Roadmap:** Version 4.0 (Eight Phases: Phase 0 through Phase 7)  
> **Scope Target:** Academic and research document similarity analysis across English, Hindi, and Telugu.

---

## 1. Prime Directives for AI Agents

All AI programming agents (including Google Antigravity, subagents, and automated assistants) working in this repository MUST strictly abide by the following operational directives. These rules take precedence over general coding heuristics.

### Rule 1: Always Inspect Before Modification
Before proposing or writing any code or documentation, agents must inspect the current filesystem and repository state. Verify directory contents, check Git status, and avoid duplicate files or conflicting structures.

### Rule 2: Follow the Phase-Gated Roadmap
This project is developed strictly across eight sequential phases:
- **Phase 0:** Requirements Analysis, System Architecture, and Complete Project Blueprint
- **Phase 1:** Engineering Foundation (Skeleton, Docker, Database, Basic Worker, CI)
- **Phase 2:** Document Ingestion and Corpus Processing
- **Phase 3:** Lexical Detection Pipeline (Winnowing, BM25, Local Alignment)
- **Phase 4:** Semantic and Hybrid Detection (Embeddings, Vector Search, Fusion)
- **Phase 5:** Multilingual Evaluation & Benchmarking (EN, HI, TE)
- **Phase 6:** Product UX, Human Review & PDF Reporting
- **Phase 7:** Production Hardening, Security & Deployment

**Never implement features assigned to a later phase.** Do not initialize application frameworks during Phase 0. Do not create fake or placeholder implementations.

### Rule 3: Respect Approved Architecture and Single Source of Truth
The architecture documented in `docs/` is binding. 
- Functional requirements are canonical in `docs/00-product/requirements.md`.
- Data entities and relations are canonical in `docs/03-data/data-model.md`.
- API endpoints and schemas are canonical in `contracts/openapi.yaml`.
- Scoring formulas and offset rules are canonical in `docs/03-data/offsets-and-scoring.md`.

Never silently redefine core behavior, alter entity attributes, change API formats, or invent custom field names without creating an Architecture Decision Record (ADR) and reconciling all affected specifications.

### Rule 4: Mandatory Architecture Decision Records (ADRs)
If an engineering problem requires modifying an established design decision or introducing a new technology, agents must:
1. Explain the rationale and alternatives.
2. Draft an ADR in `docs/01-architecture/adrs/`.
3. Update dependent documentation and contracts.
4. Update the requirements traceability matrix in `docs/phases/phase-00/requirements-traceability.md`.

### Rule 5: Strict Text Offset and Encoding Hygiene
- All text extraction, segmentation, indexing, database storage, and API contracts must use **zero-based, half-open Unicode code-point offsets** (`[start, end)`) referenced to the canonical extracted document text.
- Normalization pipelines that strip whitespace or alter character counts must maintain an explicit index projection mapping back to original code-point spans.
- Frontend components handling JavaScript strings (UTF-16 code units) must explicitly convert offsets using the documented Unicode helper routines in `docs/01-architecture/module-contracts.md`.
- Never mix byte offsets, UTF-16 units, and Unicode code points without explicit conversion.

### Rule 6: Dual Coverage Scoring & Ethical Attribution
- The platform reports two distinct coverage metrics: **Lexical Coverage** (exact and near-exact verbatim matches) and **Potential Semantic Coverage** (paraphrases or cross-lingual equivalents).
- Overlapping spans matching multiple reference sources must be geometrically unified (merged) so no submitted text offset is counted more than once in the aggregate score.
- Text similarity is **not automatically plagiarism**. System outputs are evidentiary findings for human review, never automated misconduct accusations.

### Rule 7: Zero Data Leakage & Privacy-First Storage
- User submissions are **private by default**.
- Never allow a user in Mode A, B, or C to search or access document contents or metadata belonging to another user without explicit, verified collection permissions.
- Submitted files, extracted texts, embeddings, and reports must be subject to hard deletion when requested by the owner (`DELETE /api/v1/documents/{id}`).
- Never commit private documents, production database credentials, secrets, or real model weights to the Git repository.

### Rule 8: Zero Fabrication in Evaluation and Testing
- Never fabricate benchmark results, accuracy scores, latency metrics, or test passes.
- When benchmarks or evaluation scripts have not been executed on real data, state clearly that metrics are targets or unmeasured.
- Development and tuning must never be performed on the held-out test split (`test_held_out`).
- Cross-language claims (especially for Telugu) must remain marked provisional until empirically validated.

### Rule 9: Database Changes Require Migrations
- All schema alterations after Phase 1 must be managed through formal Alembic migration scripts.
- Never perform raw, unversioned schema alterations on production or test databases.

### Rule 10: Produce Verification Evidence for Every Phase
- Every phase must conclude with a formal validation report and completion gate.
- Agents must run automated tests, linting, and structural validation, recording actual commands and terminal outputs.
- Never mark a phase complete without verifiable evidence.

### Rule 11: Host Workspace Synchronization Safeguards (OneDrive Isolation)
- Because the repository root resides in a OneDrive-synchronized folder (`C:\Users\vaibh\OneDrive\Documents\plagarism engine`), agents must strictly ensure that runtime databases, model weights, build artifacts, and private upload files are isolated from background cloud synchronization.
- Docker Compose configurations must use **named volumes** (`postgres_data`, `storage_volume`) rather than host folder binds.
- Local scratch and test scripts must place temporary output files inside ignored directories (`scratch/`, `storage/temp/`, or `%TEMP%`) to prevent file locks (`EPERM`/`EBUSY`) and cloud sync collisions.

---

## 2. Directory Ownership and Modularity Rules

Agents must strictly preserve the permanent repository directory boundaries:
- `apps/web/`: Frontend React application. Must NOT import Python code or direct database drivers. Accesses backend exclusively via typed API clients matching `contracts/openapi.yaml`.
- `apps/backend/`: FastAPI backend and background workers. Must NOT contain frontend assets or bundle React code.
- `contracts/`: Authoritative API contracts (OpenAPI 3.1) and JSON schemas.
- `evaluation/`: Benchmark configurations, test datasets, annotation schemas, and evaluation scripts.
- `infra/`: Docker, Docker Compose, reverse proxy, and deployment definitions.
- `docs/`: System documentation, architecture records, and phase tracking.

---

## 3. Communication Protocol

- Keep progress reports concise, factual, and backed by verifiable terminal output.
- When errors or unexpected findings arise, explain the root cause and propose concrete fixes before modifying files.
- Cite specific files using markdown links with the `file://` scheme and appropriate line ranges where applicable.
