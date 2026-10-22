# REST API Design & Architecture Standards

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **API Version:** v1 (`/api/v1`)  
> **Specification Format:** OpenAPI 3.1  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. API Architecture Principles

The API layer is exposed by the FastAPI application and designed according to pragmatic RESTful principles, strict type validation, and unambiguous error semantics.

### 1.1 URI Versioning
All public and internal endpoints are namespaced under `/api/v1/`:
- Document endpoints: `/api/v1/documents`
- Reference Collections: `/api/v1/collections`
- Similarity Analyses: `/api/v1/analyses`
- Review Actions: `/api/v1/reviews`
- System & Health: `/api/v1/health`

Backwards-incompatible changes will trigger a version increment to `/api/v2/`.

### 1.2 Authentication & Session Flow
- **Protocol:** JSON Web Tokens (JWT) adhering to RFC 7519.
- **Header:** `Authorization: Bearer <access_token>`
- **Token Lifecycles:**
  - Access Token: 60-minute expiration, contains `sub` (User UUID), `role`, and token permissions.
  - Refresh Token: 7-day expiration, stored in an `HttpOnly`, `SameSite=Strict`, `Secure` cookie.
- **Unauthenticated Sessions:** Unauthenticated guests executing Mode A comparisons receive an ephemeral session token mapped to a temporary tenant identifier.

---

## 2. Multipart Upload & Document Ingestion Behavior

- **Content-Type:** `multipart/form-data`
- **File Constraints:**
  - Maximum File Size: 30 MB (`31,457,280` bytes). Requests exceeding this limit receive HTTP 413 Payload Too Large.
  - Allowed MIME Types: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/plain`.
  - Filename Sanitization: Client filenames are stripped of path separators (`/`, `\`), null bytes, and non-printable characters. Server storage uses a generated random UUID.
- **Synchronous Upload Response:** File uploads return immediately with HTTP 201 Created and the created `DocumentMetadata` record. Text extraction and indexing are dispatched asynchronously.

---

## 3. Asynchronous Job Execution & Polling Contract

Because similarity analysis is CPU-intensive, long-running workflows use an asynchronous polling model:

1. **Job Dispatch:** The client issues `POST /api/v1/analyses` with comparison mode and document references.
2. **Immediate Acknowledgment:** The API responds with **HTTP 202 Accepted**, returning:
   ```json
   {
     "job_id": "8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
     "analysis_id": "3a7c9e12-b5f4-4a21-96d8-11e2f4a5c678",
     "status": "queued",
     "created_at": "2026-10-13T14:30:00Z",
     "estimated_duration_seconds": 15
   }
   ```
3. **Status Polling:** The client periodically polls `GET /api/v1/analyses/{analysis_id}/status`:
   - Polling interval: 2 seconds for the first 20 seconds, back off to 5 seconds thereafter.
   - States: `queued` $\rightarrow$ `processing` $\rightarrow$ `completed` | `failed` | `cancelled`.
4. **Result Retrieval:** Once status is `completed`, the client fetches full results via `GET /api/v1/analyses/{analysis_id}`.
5. **Job Cancellation:** The client can abort an active job via `POST /api/v1/analyses/{analysis_id}/cancel`.

---

## 4. Standardized Error Payload (RFC 7807 Inspired)

All error responses (HTTP 4xx and 5xx) return a consistent, machine-readable JSON structure:

```json
{
  "error": {
    "code": "EXTRACTION_EMPTY_TEXT",
    "message": "The uploaded PDF document contains no extractable text layer.",
    "status": 400,
    "timestamp": "2026-10-13T14:35:10Z",
    "request_id": "req-9a8b7c6d-5e4f",
    "details": [
      {
        "field": "file",
        "issue": "PyMuPDF extracted 0 characters across 4 pages. Scanned document suspected."
      }
    ]
  }
}
```

---

## 5. Pagination, Filtering & Sorting

Endpoints returning collections of records (e.g., `GET /api/v1/documents`, `GET /api/v1/collections`) implement uniform query parameters:
- `limit`: Number of items per page (default: 20, max: 100).
- `offset`: Zero-based pagination offset (default: 0).
- `sort_by`: Field name to sort on (e.g., `created_at`, `title`).
- `order`: Sort order (`asc` | `desc`, default: `desc`).

Response envelopes include pagination metadata:
```json
{
  "items": [...],
  "pagination": {
    "total_count": 142,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

---

## 6. Report Download Endpoint Behavior

- **Endpoint:** `GET /api/v1/analyses/{analysis_id}/report`
- **Query Parameters:**
  - `include_notes` (boolean, default: `true`): Include reviewer annotations.
  - `language` (string, default: `"en"`): Language for report headings (`en`, `hi`, `te`).
- **Response Headers:**
  - `Content-Type: application/pdf`
  - `Content-Disposition: attachment; filename="similarity-report-{analysis_id}.pdf"`
  - `Content-Length: <byte_count>`

---

## 7. Rate Limiting & Idempotency

- **Rate Limits:**
  - Unauthenticated IPs: Max 10 comparison requests per hour; 60 read requests per minute.
  - Authenticated Users: Max 100 comparison requests per hour; 300 read requests per minute.
  - Exceeding limits returns HTTP 429 Too Many Requests with a `Retry-After: <seconds>` header.
- **Idempotency:**
  - Analysis creation requests accept an optional `Idempotency-Key: <UUID>` header. Repeated submissions with the same key return the existing job rather than enqueuing duplicate worker tasks.
