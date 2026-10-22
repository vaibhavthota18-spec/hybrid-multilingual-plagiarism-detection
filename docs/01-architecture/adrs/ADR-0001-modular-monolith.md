# ADR-0001: Modular Monolith Architecture Pattern

- **Status:** Accepted
- **Deciders:** Principal Software Architect, Senior Backend Architect
- **Date:** October 2026
- **Technical Story:** Architecture definition for the core plagiarism platform

---

## Context
The system requires multiple specialized services: document validation, text extraction, language detection, Winnowing fingerprinting, vector embedding generation, inverted indexing, local sequence alignment, scoring, PDF rendering, and human review. 
A naive implementation might either bundle everything into an unstructured single-script codebase or prematurely decompose into 6+ microservices requiring distributed RPCs, service discovery, distributed tracing, and independent deployments.

## Decision
We adopt a **Modular Monolith** architecture for the backend application (`apps/backend`), packaged as a cohesive Python application with strict internal boundaries. Asynchronous, computationally intensive workloads (extraction, ML inference, alignment, reporting) are delegated to worker daemon processes running the same codebase via Redis Queue (RQ).

## Alternatives Considered
1. **Microservices Architecture:** Rejected due to premature operational overhead, network latency on heavy passage serialization, and complex multi-service transactional boundaries.
2. **Traditional Monolith (Unstructured):** Rejected due to high risk of circular imports, direct coupling between API routes and database tables, and unmanageable code sprawl.

## Rationale
- High developer velocity and simplified local setup with a single Docker Compose stack.
- In-process module calls eliminate network serialization overhead for high-volume text manipulation.
- Independent horizontal scaling is preserved by separating the FastAPI web container from RQ worker containers while sharing domain models.

## Consequences & Trade-offs
- **Positive:** Single repository for backend code, unified database schema and migrations via Alembic, shared Pydantic domain models.
- **Negative:** Requires rigorous discipline to prevent modules from bypassing published domain service interfaces. Enforced via automated import linter rules in CI.

## Validation Requirements
Automated linting in CI must verify that API route handlers import only from service interfaces and domain schemas, never private subpackage internals.
