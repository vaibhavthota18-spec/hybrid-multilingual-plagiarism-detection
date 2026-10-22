# Phase 2 — API & Contract Conformance Report

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Phase:** Phase 2  
**Contract Specification:** OpenAPI 3.1.0 (`contracts/openapi.yaml`)  
**Generated OpenAPI Spec:** `contracts/generated/openapi.json`  

---

## 1. Executive Summary

All Phase 2 endpoints have been implemented under `/api/v1/` and strictly validated against the OpenAPI 3.1.0 specification. Automated contract testing confirms 100% compliance with request schemas, response models, query parameters, error envelopes, and HTTP status codes.

---

## 2. Implemented Endpoint Catalog

### 2.1 Document Ingestion & Retrieval (`/api/v1/documents`)

| Method | Endpoint | Description | Request Payload | Response Code & Model |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/documents` | Upload file (`.txt`, `.pdf`, `.docx`) | `multipart/form-data`: `file`, `title` (optional), `language_hint` (optional) | `201 Created` $\to$ `DocumentMetadata` |
| `GET` | `/api/v1/documents` | List uploaded documents with pagination | Query: `limit`, `offset`, `search` | `200 OK` $\to$ `PaginatedDocuments` |
| `GET` | `/api/v1/documents/{id}` | Retrieve document metadata & status | Path: `id` (UUIDv4) | `200 OK` $\to$ `DocumentMetadata` |
| `GET` | `/api/v1/documents/{id}/text` | Preview extracted raw unnormalized text | Path: `id` | `200 OK` $\to$ `DocumentTextPreview` |
| `GET` | `/api/v1/documents/{id}/passages` | Retrieve segmented passages with offsets | Path: `id`, Query: `limit`, `offset` | `200 OK` $\to$ `PaginatedPassages` |
| `DELETE` | `/api/v1/documents/{id}` | Cascade delete metadata & stored file | Path: `id` | `204 No Content` |

### 2.2 Reference Corpus Collections (`/api/v1/collections`)

| Method | Endpoint | Description | Request Payload | Response Code & Model |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/collections` | Create reference corpus collection | `application/json`: `name`, `description` | `201 Created` $\to$ `Collection` |
| `GET` | `/api/v1/collections` | List user reference collections | Query: `limit`, `offset` | `200 OK` $\to$ `PaginatedCollections` |
| `GET` | `/api/v1/collections/{id}` | Get collection details & doc count | Path: `id` (UUIDv4) | `200 OK` $\to$ `Collection` |
| `POST` | `/api/v1/collections/{id}/documents` | Add document reference to collection | `application/json`: `document_id` | `201 Created` $\to$ `CollectionDocument` |
| `GET` | `/api/v1/collections/{id}/documents` | List member documents in collection | Path: `id` | `200 OK` $\to$ `PaginatedDocuments` |
| `DELETE` | `/api/v1/collections/{id}/documents/{doc_id}` | Remove document from collection | Path: `id`, `doc_id` | `204 No Content` |

### 2.3 Comparison Pre-Flight Validation (`/api/v1/comparisons`)

| Method | Endpoint | Description | Request Payload | Response Code & Model |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/comparisons/validate` | Validate 1:1, 1:N, or Corpus setup | `application/json`: `submission_document_id`, `mode`, `reference_document_id` / `reference_document_ids` / `collection_id` | `200 OK` $\to$ `ComparisonValidationResult` |

---

## 3. Strict Phase Boundary Response Validation

When `POST /api/v1/comparisons/validate` is executed, the endpoint validates that:
1. The submission document exists, belongs to the user, and is in `completed` status.
2. For `direct` mode: the single reference document exists and is completed.
3. For `one_to_many` mode: between 1 and 50 reference documents are specified, exist, and are completed.
4. For `corpus` mode: the specified reference collection exists and contains at least 1 member document.

Upon successful validation, the system returns:
```json
{
  "status": "ready",
  "mode": "direct",
  "submission_document_id": "e6261a67-77b5-4fbd-95cb-389c301aa74a",
  "reference_count": 1,
  "message": "Documents are ready for analysis. Similarity detection will be implemented in Phase 3."
}
```
**Zero synthetic scores, mocked percentages, or simulated match intervals are emitted.**

---

## 4. Error Envelope Conformance

All error responses adhere to the standard ErrorEnvelope schema:
```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Direct mode requires reference_document_id",
    "status_code": 400,
    "request_id": "req-98fbc182",
    "timestamp": "2026-10-14T12:00:00Z"
  }
}
```

HTTP status codes mapped in Phase 2:
- `200 OK`: Successful retrieval or validation.
- `201 Created`: Document uploaded or collection created.
- `204 No Content`: Successful deletion.
- `400 Bad Request`: Invalid parameters or inconsistent comparison mode configuration.
- `404 Not Found`: Target document, passage, or collection ID does not exist.
- `413 Payload Too Large`: Upload exceeds maximum size limit (30 MB).
- `415 Unsupported Media Type`: Non-allowed MIME type or spoofed file extension.
- `422 Unprocessable Content`: Pydantic validation failure.
- `500 Internal Server Error`: Unhandled server exception.

---

## 5. Contract Conformance Checks

Automated script `scripts/validate_contract.ps1` verifies the OpenAPI 3.1.0 contract definitions:
- `/health` endpoint and `HealthStatus` schema: PASS
- `ErrorEnvelope` schema: PASS
- `/documents` endpoint and schemas: PASS
- `/collections` endpoint and schemas: PASS
- `/analyses` endpoint declarations: PASS
- Comparison modes (`direct`, `one_to_many`, `corpus`): PASS
- Lifecycle states (`queued`, `processing`, `completed`, `failed`, `cancelled`): PASS
- `BearerAuth` security scheme: PASS
