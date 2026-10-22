# ADR-0002: Contract-First API Design & OpenAPI 3.1 Governance

- **Status:** Accepted
- **Deciders:** Principal Software Architect, Senior Frontend Architect, Senior Backend Architect
- **Date:** October 2026
- **Technical Story:** Cross-boundary communication and schema governance

---

## Context
The platform consists of a React Single Page Application and a Python FastAPI backend. In multi-phase development, frontend and backend teams risk drift if API schemas, offset formats, and job state enumerations are not strictly governed by a single contract.

## Decision
1. **Phase 0 Baseline:** We author an authoritative, human-reviewed `contracts/openapi.yaml` adhering strictly to the **OpenAPI 3.1** specification.
2. **Phase 1+ Implementation:** The FastAPI backend generates its runtime OpenAPI schema, which is continuously verified against `contracts/openapi.yaml` in CI.
3. **Frontend Typing:** The React frontend generates TypeScript types and API client wrappers directly from the OpenAPI schema using `openapi-typescript`.

## Alternatives Considered
1. **Ad-Hoc Manual Interfaces:** TypeScript interfaces written by hand from backend documentation. Rejected due to guaranteed drift and high defect rates.
2. **gRPC / Protocol Buffers:** Rejected because the web browser requires HTTP/REST and JSON payloads, which simplifies debugging, caching, and document multipart uploads.

## Rationale
- OpenAPI 3.1 supports full JSON Schema 2020-12, enabling rich validation rules (regex patterns, integer ranges, nullability).
- Eliminates manual client code authoring and ensures frontend compile-time type safety.

## Consequences & Trade-offs
- **Positive:** Single source of truth for endpoints, parameters, and error schemas. Immediate compilation failures in the frontend when backend schemas change.
- **Negative:** Schema modifications require updating contract definitions and regenerating types before frontend builds succeed.

## Validation Requirements
Automated OpenAPI linting in CI using Spectral; schema diffing checks asserting zero backwards-incompatible API changes without version bumping.
