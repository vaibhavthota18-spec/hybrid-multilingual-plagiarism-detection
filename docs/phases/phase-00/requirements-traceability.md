# Requirements Traceability Matrix (RTM)

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Baseline SRS:** `docs/00-product/requirements.md`  
> **Date:** October 2026  

---

## 1. Traceability Methodology

The Requirements Traceability Matrix guarantees complete forward and backward traceability from high-level product requirements to architectural design artifacts, owning components, assigned implementation phases, acceptance gates, and verification methodologies. Every functional requirement (FR) and non-functional requirement (NFR) is accounted for with zero omissions.

---

## 2. Functional Requirements Traceability

| Requirement ID | Requirement Title | Design Specification | Owning Subsystem | Target Phase | Verification Method |
|---|---|---|---|---|---|
| `FR-DOC-001` | Multi-Format Document Upload | `docs/02-api/api-design.md`, `contracts/openapi.yaml` | `ingestion` | Phase 2 | Automated multipart upload integration tests |
| `FR-DOC-002` | Text Extraction & Unicode Normalization | `docs/01-architecture/component-design.md` | `extraction` | Phase 2 | PyMuPDF/python-docx gold-standard comparison tests |
| `FR-DOC-003` | Canonical Zero-Based Code-Point Offsets | `docs/01-architecture/module-contracts.md` | `preprocessing` | Phase 2 | Property-based multi-script substring slicing tests |
| `FR-DOC-004` | Language Identification | `docs/01-architecture/component-design.md` | `preprocessing` | Phase 2 | Trilingual classification accuracy benchmark ($\ge 98\%$) |
| `FR-DOC-005` | Multi-Tier Document Storage & Hard Deletion | `docs/04-security/privacy-access-retention.md`, ADR-0006 | `storage` | Phase 2 | Database cascade, filesystem unlink, and backup replay tests |
| `FR-MODE-001` | Direct Comparison Mode (Mode A) | `docs/01-architecture/processing-and-sequences.md` | `scoring` | Phase 3 & 4 | Pairwise comparison integration test suite |
| `FR-MODE-002` | One-to-Many Comparison Mode (Mode B) | `docs/01-architecture/processing-and-sequences.md` | `scoring` | Phase 3 & 4 | Multi-source batch comparison & attribution test |
| `FR-MODE-003` | Corpus Search Mode (Mode C) | `docs/01-architecture/processing-and-sequences.md` | `corpora` | Phase 2 & 4 | Query test against 500-doc indexed reference corpus |
| `FR-DET-001` | Winnowing Rolling-Hash Fingerprinting | `docs/01-architecture/component-design.md` | `fingerprinting` | Phase 3 | Deterministic hash collision and verbatim recall test |
| `FR-DET-002` | Inverted Index & BM25 Retrieval | `docs/03-data/indexes-and-lifecycle.md` | `retrieval` | Phase 3 | BM25 Recall@20 benchmark on lexical queries |
| `FR-DET-003` | Multilingual Semantic Embeddings | `docs/05-evaluation/model-selection.md`, ADR-0005 | `ml.embeddings` | Phase 4 | Model inference unit test: unit norm and dimensionality |
| `FR-DET-004` | Vector Retrieval via pgvector | `docs/03-data/data-model.md`, ADR-0004 | `retrieval` | Phase 4 | pgvector inner product query benchmark |
| `FR-DET-005` | Candidate Fusion & Deduplication | `docs/01-architecture/component-design.md`, ADR-0003 | `retrieval` | Phase 4 | Hybrid union candidate recall evaluation |
| `FR-DET-006` | Token-Level Local Alignment & Span Reporting | `docs/01-architecture/module-contracts.md` | `alignment` | Phase 3 | Smith-Waterman mean span IoU evaluation ($\ge 0.80$) |
| `FR-DET-007` | Overlap Deduplication & Dual Coverage | `docs/03-data/offsets-and-scoring.md` | `scoring` | Phase 3 & 4 | Interval union mathematical boundary tests |
| `FR-REP-001` | Interactive Side-by-Side Finding Viewer | `docs/00-product/user-journeys.md` | `web.reports` | Phase 6 | Playwright automated browser highlight sync tests |
| `FR-REP-002` | Citation & Quotation Filtering | `docs/03-data/offsets-and-scoring.md` | `scoring` | Phase 6 | Score recalculation test with citation toggles |
| `FR-REP-003` | Human-in-the-Loop Review & Notes | `docs/02-api/api-design.md`, `contracts/openapi.yaml` | `api.v1.reviews` | Phase 6 | Review label submission and net score update test |
| `FR-REP-004` | Downloadable PDF Audit Report | `docs/01-architecture/processing-and-sequences.md` | `reporting` | Phase 6 | PDF generation and Indic font glyph verification test |
| `FR-COL-001` | Collection Creation & Access Control | `docs/02-api/authorization-and-errors.md` | `corpora` | Phase 2 | RBAC collection permission matrix test |
| `FR-COL-002` | Reference Corpus Ingestion Pipeline | `docs/01-architecture/processing-and-sequences.md` | `corpora` | Phase 2 & 4 | Corpus ingestion worker integration test |

---

## 3. Non-Functional Requirements Traceability

| Requirement ID | Requirement Title | Design Specification | Owning Subsystem | Target Phase | Verification Method |
|---|---|---|---|---|---|
| `NFR-SEC-001` | Secure Upload Validation & File Isolation | `docs/04-security/threat-model.md` | `ingestion` | Phase 2 & 7 | Penetration tests: polyglot, path traversal, oversized files |
| `NFR-SEC-002` | Multi-Tenant Isolation & Least Privilege | `docs/04-security/threat-model.md` | `core.security` | Phase 2 & 7 | Automated cross-tenant query assertion test |
| `NFR-PRIV-001`| Private-by-Default Submissions & Erasure | `docs/04-security/privacy-access-retention.md`, ADR-0006 | `storage` | Phase 2 & 7 | Deletion audit asserting zero leftover rows or files |
| `NFR-PERF-001`| 10-Page Warmed Latency Target (p95 $\le 180$s) | `docs/05-evaluation/metrics-and-acceptance.md` | `jobs.worker` | Phase 5 & 7 | End-to-end benchmark latency profiling on 8-core CPU |
| `NFR-PERF-002`| Mode A Direct Response Latency ($\le 10$s) | `docs/00-product/requirements.md` | `jobs.worker` | Phase 3 & 4 | Direct comparison latency benchmark across 50 pairs |
| `NFR-SCAL-001`| Asynchronous Queue Decoupling | `docs/01-architecture/adrs/ADR-0007-background-jobs.md` | `jobs` | Phase 1 & 2 | API load test verifying HTTP 202 response $<200$ ms |
| `NFR-REL-001` | Resilient Job State Transitions | `docs/01-architecture/processing-and-sequences.md` | `jobs` | Phase 1 & 7 | Chaos test injecting worker termination and verifying state |
| `NFR-REL-002` | Extraction Fault Tolerance | `docs/00-product/requirements.md` | `extraction` | Phase 2 | Batch ingestion test with intentionally corrupted files |
| `NFR-A11Y-001`| Web Accessibility (WCAG 2.1 AA) | `docs/00-product/requirements.md` | `web.components` | Phase 6 | Automated axe-core accessibility audit |
| `NFR-OBS-001` | Structured JSON Logging & Privacy Filter | `docs/06-operations/environment-and-observability.md` | `observability` | Phase 1 & 7 | Log assertion test checking JSON format & zero text leaks |
| `NFR-DEP-001` | Single-Command Container Orchestration | `docs/06-operations/deployment-plan.md` | `infra` | Phase 1 & 7 | Clean-room Docker Compose deployment in CI runner |

---

## 4. Phase Assignment Summary

- **Phase 0:** Requirements Analysis, System Architecture, Project Blueprint (100% Complete)
- **Phase 1 (Engineering Foundation):** `NFR-SCAL-001`, `NFR-REL-001`, `NFR-OBS-001`, `NFR-DEP-001`
- **Phase 2 (Document Ingestion & Corpora):** `FR-DOC-001`, `FR-DOC-002`, `FR-DOC-003`, `FR-DOC-004`, `FR-DOC-005`, `FR-COL-001`, `FR-COL-002`, `NFR-SEC-001`, `NFR-SEC-002`, `NFR-PRIV-001`, `NFR-REL-002`
- **Phase 3 (Lexical Detection Pipeline):** `FR-DET-001`, `FR-DET-002`, `FR-DET-006`, `FR-MODE-001`, `NFR-PERF-002`
- **Phase 4 (Semantic & Hybrid Detection):** `FR-DET-003`, `FR-DET-004`, `FR-DET-005`, `FR-DET-007`, `FR-MODE-002`, `FR-MODE-003`
- **Phase 5 (Multilingual Evaluation):** `NFR-PERF-001` & Evaluation Suites (EXP-01 through EXP-12)
- **Phase 6 (Product UX & Reporting):** `FR-REP-001`, `FR-REP-002`, `FR-REP-003`, `FR-REP-004`, `NFR-A11Y-001`
- **Phase 7 (Hardening & Deployment):** Hardening all NFRs (Security, Observability, Containerization)
