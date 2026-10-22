# Authorization Matrix & Error Catalog

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **API Version:** v1 (`/api/v1`)  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Role-Based Access Control (RBAC)

The platform enforces strict role boundaries. Every authenticated request context carries the user's role and tenant bindings:

| User Role | Description | Allowed Actions |
|---|---|---|
| **Guest** | Unauthenticated visitor | Execute Mode A direct comparison (rate-limited); view sample demo reports. |
| **Student** | Standard authenticated user | Upload documents; run Mode A and Mode B analyses; access personal document history; delete own documents; access public/permitted collections. |
| **Researcher** | Advanced scholarly user | All Student privileges + run batch analyses (Mode B); export signed PDF reports; create and manage private reference collections. |
| **Educator / Evaluator** | Academic instructor | All Researcher privileges + query departmental Mode C corpora; review student submissions; view side-by-side sources; apply citation exclusions. |
| **Reviewer** | Accredited academic reviewer | All Educator privileges + submit formal human review annotations (`VALID_CITATION`, `SUSPECTED_PLAGIARISM`, etc.); certify audit reports. |
| **Institutional Admin** | Organization administrator | Manage departmental collections; assign user roles; manage collection permissions; view audit logs; configure retention policies. |

---

## 2. Collection Permission Hierarchy

Reference collections (Mode C) enforce fine-grained access levels stored in the `collection_permissions` table:

```
ADMIN > WRITE > READ
```

- **`READ`:** User can select the collection for Mode C similarity queries. User CANNOT view raw source document full texts unless granted explicit reading privileges.
- **`WRITE`:** User can add reference documents to the collection and trigger passage indexing.
- **`ADMIN`:** User can delete the collection, add/remove member permissions, and alter collection metadata.

### Cross-Tenant Data Isolation Guardrail
When executing Mode C vector and BM25 searches, the backend injects an unconditional SQL predicate:
```sql
WHERE collection_id IN (
    SELECT collection_id 
    FROM collection_permissions 
    WHERE user_id = :current_user_id AND permission_level IN ('READ', 'WRITE', 'ADMIN')
)
```
Any attempt to query unpermitted collection IDs returns **HTTP 403 Forbidden** (`AUTH_INSUFFICIENT_COLLECTION_PERMISSIONS`).

---

## 3. Comprehensive Error Catalog

The system categorizes all application errors into stable, standardized error codes:

| Error Code | HTTP Status | Meaning & Cause | Safe User-Visible Message |
|---|---|---|---|
| `AUTH_INVALID_CREDENTIALS` | 401 | Invalid email or password provided. | "Invalid email or password. Please verify your credentials." |
| `AUTH_TOKEN_EXPIRED` | 401 | Access JWT has expired. | "Your session has expired. Please refresh your session or log in again." |
| `AUTH_INSUFFICIENT_COLLECTION_PERMISSIONS` | 403 | User does not have READ/WRITE access to the requested collection. | "You do not have permission to access or search this reference collection." |
| `AUTH_RESOURCE_FORBIDDEN` | 403 | Attempt to access another user's private document or analysis. | "You do not have permission to view or modify this resource." |
| `VALIDATION_FAILED` | 422 | Request body failed Pydantic schema validation. | "Invalid request parameters. Please verify input fields." |
| `FILE_TOO_LARGE` | 413 | Uploaded file exceeds 30 MB size cap. | "The uploaded file exceeds the 30 MB limit. Please compress or split the document." |
| `INVALID_FILE_FORMAT` | 400 | File MIME type or magic bytes do not match PDF/DOCX/TXT. | "Unsupported file format. Please upload a valid PDF, DOCX, or TXT file." |
| `EXTRACTION_EMPTY_TEXT` | 400 | File has valid structure but contains 0 characters of text (e.g., scanned image PDF). | "No extractable text was found in this document. Please ensure the document contains selectable text." |
| `EXTRACTION_PASSWORD_PROTECTED` | 400 | PDF is encrypted with an owner or user password. | "This document is password-protected. Please remove encryption before uploading." |
| `RESOURCE_NOT_FOUND` | 404 | Target document, analysis, collection, or finding does not exist. | "The requested resource could not be found." |
| `RESOURCE_CONFLICT` | 409 | Duplicate document upload with identical checksum, or duplicate collection name. | "A resource with these details already exists." |
| `JOB_TIMEOUT_EXCEEDED` | 504 | Analysis worker processing exceeded the 600-second execution cap. | "Analysis timed out. Try splitting large documents or reducing the reference batch size." |
| `RATE_LIMIT_EXCEEDED` | 429 | User or IP exceeded designated request quota. | "Rate limit exceeded. Please wait before submitting more requests." |
| `INTERNAL_PROCESSING_ERROR` | 500 | Unhandled exception occurred in worker or API server. | "An unexpected error occurred while processing your request. Our team has been notified." |
