# Phase 1: Security Foundation and Hardening Report

**System:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Phase:** 1 of 7  
**Status:** Approved  
**Date:** October 2026  
**Document Version:** 1.0.0  

---

## 1. Authentication & Cryptographic Token Architecture

Security is implemented following defense-in-depth principles:

### 1.1 JWT Bearer Token Specification
* **Standard:** RFC 7519 JSON Web Token (JWT).
* **Cryptographic Algorithm:** Pinned strictly to `HS256` (HMAC with SHA-256).
* **Algorithm Tampering Protection:** The decoder strictly whitelists `algorithms=["HS256"]`, permanently preventing `alg: none` or key confusion attacks (`RS256` public key verified with HMAC secret).
* **Claims Structure:**
  * `sub`: Subject UUID (`user_id`).
  * `email`: User corporate / academic email address.
  * `role`: User authorization role (`STUDENT`, `FACULTY`, `RESEARCHER`, `ADMIN`).
  * `exp`: UTC expiration timestamp (default 60 minutes).
  * `iat`: Issued-at timestamp.
* **Token Expiration & Revocation:** Expired tokens are rejected with HTTP 401 Unauthorized (`AUTH_UNAUTHORIZED`).

---

## 2. Role-Based Access Control (RBAC)

Authorization is enforced at the router and dependency injection level via `require_role()`:

| Role | Permissions & Access Scope |
| :--- | :--- |
| **`STUDENT`** | Can upload personal submission documents; can initiate Direct or One-to-Many comparisons against authorized collections; cannot inspect raw institutional corpus or review scores. |
| **`FACULTY`** | Can access student submissions within assigned courses; can review match findings, adjust thresholds, and generate official reports. |
| **`RESEARCHER`** | Can perform corpus analysis across authorized research collections; cannot access student identity records. |
| **`ADMIN`** | Full institutional access; collection management; user provisioning; system configuration; access to `/admin-probe`. |

---

## 3. Container Hardening & Unprivileged Execution

In compliance with production container security standards:
* **Unprivileged User:** Both `Dockerfile.backend` and `Dockerfile.worker` create a non-root system group and user (`appuser:1000`) and switch using `USER appuser`.
* **Read-Only Root Filesystem Ready:** Storage directories (`/app/storage/uploads`, `/app/storage/reports`) are explicitly pre-created and assigned ownership to `appuser`.
* **Package Cache Purge:** `apt-get` lists and pip caches are cleaned during the Docker build stage to minimize image footprint and attack surface.

---

## 4. Privacy, Redaction & Production Guardrails

### 4.1 Structured JSON Logging Redaction
Log events are serialized to JSON lines using `JSONLogFormatter`. Extra attributes matching sensitive keywords (`password`, `token`, `secret`, `authorization`, `jwt_secret`, `hashed_password`) are automatically replaced with `[REDACTED]`.

### 4.2 Production Safety Assertions
Pydantic settings enforce the following validations at boot:
* If `ENVIRONMENT == "production"`:
  * `DEBUG` must be `False` (prevents exposure of interactive debugger or raw stack traces).
  * `JWT_SECRET_KEY` must be at least 32 characters in length (prevents brute-force dictionary attacks).
  * Test token generation endpoints (`/api/v1/auth/test-token`) are rejected with HTTP 403 Forbidden.
