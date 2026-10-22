# Phase 1: API and Contract Conformance Report

**System:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Phase:** 1 of 7  
**Status:** Approved & Verified  
**Date:** October 2026  
**Document Version:** 1.0.0  

---

## 1. Specification Baseline: OpenAPI 3.1.0

The API foundation strictly mirrors `contracts/openapi.yaml`. In accordance with Phase 1 boundaries, only the core infrastructure, health monitoring, and authentication baseline endpoints are active. All comparison, ingestion, and reporting routes declared in the OpenAPI contract remain structurally mapped in contracts for future phases.

---

## 2. Implemented Endpoints

### 2.1 System Health Probe (`/api/v1/health` and `/health`)
* **Operation ID:** `getHealthStatus`
* **HTTP Method:** `GET`
* **Security:** Unauthenticated (publicly accessible for container orchestrators and status monitors).
* **Summary:** System Health and Readiness Probe.
* **Schema Conformance:** Returns `HealthStatus` object:
  ```json
  {
    "status": "healthy",
    "timestamp": "2026-10-14T10:00:00.000000+00:00",
    "database": "connected",
    "redis": "connected",
    "worker_pool": "operational",
    "version": "1.0.0"
  }
  ```
* **Degraded Behavior:** When PostgreSQL or Redis is unreachable, the endpoint returns HTTP 200 with `status: "degraded"` and identifies the disconnected subsystem without crashing or timing out.

### 2.2 Authentication & Identity Endpoints (`/api/v1/auth/*`)
* **`GET /api/v1/auth/me`:** Validates incoming Bearer token and returns authenticated `UserPrincipal` (`user_id`, `email`, `role`).
* **`GET /api/v1/auth/admin-probe`:** Demonstrates RBAC enforcement by requiring `ADMIN` role. Returns HTTP 403 Forbidden for students or researchers.
* **`POST /api/v1/auth/test-token`:** Development/testing helper generating valid test JWTs. Permanently disabled in production via `is_production` guardrail.

---

## 3. RFC 7807 Error Envelope Serialization

All error responses strictly adhere to the `ErrorEnvelope` schema defined in `contracts/openapi.yaml`:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Document record 00000000-0000-0000-0000-000000000001 was not found",
    "status": 404,
    "timestamp": "2026-10-14T10:00:00.000000+00:00",
    "request_id": "web-1728900000000-abcdefg",
    "details": [
      {
        "field": "document_id",
        "issue": "UUID not found in database",
        "location": "path"
      }
    ]
  }
}
```

### Supported Standard Error Codes:
* `AUTH_UNAUTHORIZED` (HTTP 401)
* `AUTH_FORBIDDEN` (HTTP 403)
* `NOT_FOUND` (HTTP 404)
* `CONFLICT` (HTTP 409)
* `VALIDATION_ERROR` (HTTP 422)
* `INTERNAL_SERVER_ERROR` (HTTP 500)

---

## 4. Request Correlation & Distributed Tracing

Every incoming HTTP request passes through `correlation_and_metrics_middleware`:
1. Inspects the incoming `X-Request-ID` header.
2. If omitted, generates a cryptographically secure UUID4.
3. Binds the identifier to `request.state.request_id` and structured log lines.
4. Echoes `X-Request-ID` and measured latency `X-Response-Time-Ms` in the HTTP response headers.

---

## 5. Contract Verification Results

The automated contract validation script (`scripts/validate_contract.ps1`) verified 10 out of 10 checks with 0 failures:
* `openapi: 3.1.0` declaration: **PASS**
* `/health` path and `getHealthStatus` operation: **PASS**
* `HealthStatus` schema definition: **PASS**
* `ErrorEnvelope` schema definition: **PASS**
* `/documents` path definition: **PASS**
* `/analyses` path definition: **PASS**
* `/analyses/{analysis_id}/report` PDF path definition: **PASS**
* `/analyses/{analysis_id}/findings/{finding_id}/reviews` path definition: **PASS**
* `BearerAuth` security scheme: **PASS**
