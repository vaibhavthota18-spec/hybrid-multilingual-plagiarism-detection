# API Contracts & Schema Governance

> **Specification:** OpenAPI 3.1.0  
> **Target File:** `contracts/openapi.yaml`  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Role of OpenAPI in Phase 0 vs. Implementation Phases

### Phase 0 Status: Architectural Design Contract
During Phase 0, `contracts/openapi.yaml` serves as the authoritative, human-reviewed **design contract** defining the intended endpoints, HTTP verbs, URL structures, parameter constraints, job states, and data schemas. 

> **Important Notice:** The existence of `contracts/openapi.yaml` in Phase 0 documents the planned interface architecture. It does NOT imply that backend endpoints are already implemented or active on port 8000.

### Phase 1+ Implementation Governance
In Phase 1 and subsequent phases:
1. The FastAPI backend application (`apps/backend`) will implement these endpoints using Pydantic v2 domain schemas.
2. FastAPI dynamically emits its runtime OpenAPI schema at `/api/v1/openapi.json`.
3. CI workflows will run schema diff validations comparing the runtime schema against `contracts/openapi.yaml` to detect unintentional contract breaking changes.
4. The React frontend (`apps/web`) will generate TypeScript interfaces directly from the schema using:
   ```bash
   npx openapi-typescript ../../contracts/openapi.yaml -o ./src/types/generated/api.ts
   ```

---

## 2. Key Contract Invariants

1. **Canonical Unicode Code-Point Offsets:** All finding and passage offsets (`submission_start_offset`, `submission_end_offset`, etc.) are zero-based, half-open Unicode code points (`[start, end)`). The frontend must convert these to JavaScript UTF-16 units for DOM manipulation.
2. **Standardized Job States:** Asynchronous analysis jobs adhere strictly to the five standard states:
   - `queued`
   - `processing`
   - `completed`
   - `failed`
   - `cancelled`
3. **Comparison Modes:** The contract strictly supports three modes:
   - `direct` (one submission vs. one reference)
   - `one_to_many` (one submission vs. multiple references)
   - `corpus` (one submission vs. indexed collection)
4. **Dual Coverage Outputs:** Analysis results expose two separate coverage metrics:
   - `overall_lexical_coverage_percent`
   - `overall_semantic_coverage_percent`
   Never combine these into a single conflated percentage without transparent formula attribution.

---

## 3. Contract Validation Scope & Tooling Disclosures

### 3.1 What Custom Validation (`scripts/validate_openapi.ps1`) Proves
The dedicated PowerShell contract validator tests 13 architectural structural assertions:
1. **OpenAPI 3.1.0 Conformance:** Valid root schema declaring `openapi: 3.1.0`.
2. **Reference Resolution:** 100% internal `$ref` target resolution (all 20 schema, response, and parameter targets resolve without broken links).
3. **Path Parameter Integrity:** All path template variables (`{document_id}`, `{collection_id}`, `{analysis_id}`, `{finding_id}`) match operation parameter declarations with `in: path` and `required: true`.
4. **Operation Completeness:** All 16 planned REST operations declare valid `operationId`s and expected 2xx response codes.
5. **Domain Enum Invariants:** Mode enums (`direct`, `one_to_many`, `corpus`), job state enums (`queued`, `processing`, `completed`, `failed`, `cancelled`), match categories, and review labels adhere strictly to domain requirements.
6. **Binary Attachment Semantics:** PDF report download endpoint specifies `application/pdf` with `format: binary`.
7. **Security Architecture:** `BearerAuth` HTTP Bearer JWT security scheme is formally defined.

### 3.2 Standards-Based Validation & Host Tooling Limitations
- Full JSON Schema Draft 2020-12 dialect evaluation and Spectral linting require `@stoplight/spectral-cli` or Python `openapi-spec-validator`.
- Because external Node.js global binaries and Python CLIs are not in the current host environment PATH, complete external standards-based validation cannot be executed natively on this host machine.
- We do not claim external CLI execution; instead, formal Spectral and Redocly CLI linters are embedded in the containerized Phase 1 CI pipeline where runtime dependencies are pinned and reproducible.
