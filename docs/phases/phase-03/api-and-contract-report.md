# REST API Endpoints and OpenAPI 3.1 Contract Compliance

## 1. OpenAPI 3.1 Compliance Overview

All Phase 3 analysis endpoints adhere strictly to the OpenAPI 3.1.0 contract defined in `contracts/openapi.yaml` and exported to `contracts/generated/openapi.json`.

All endpoints are mounted under `/api/v1/analyses`:

| Method | Endpoint | Status | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/analyses` | `202 Accepted` | Create & enqueue similarity analysis job |
| `GET` | `/api/v1/analyses` | `200 OK` | Paginated listing of user analyses |
| `GET` | `/api/v1/analyses/{analysis_id}` | `200 OK` | Detailed analysis inspection model |
| `GET` | `/api/v1/analyses/{analysis_id}/status` | `200 OK` | Polling endpoint for job status & progress |
| `POST` | `/api/v1/analyses/{analysis_id}/cancel` | `200 OK` | Cancel an in-flight analysis job |
| `GET` | `/api/v1/analyses/{analysis_id}/findings` | `200 OK` | Granular list of similarity findings |
| `DELETE` | `/api/v1/analyses/{analysis_id}` | `204 No Content` | Cascade delete analysis and findings |
| `GET` | `/api/v1/analyses/{analysis_id}/report` | `200 OK` | Formatted audit report |

---

## 2. Request & Response Payloads

### POST /api/v1/analyses (Create Analysis)
```json
{
  "submission_document_id": "4098c9d5-7a1d-48b2-adc1-5f4fc8422ced",
  "mode": "direct",
  "reference_document_id": "dfad71e2-cfd5-4e31-b396-90ab29ce8293",
  "exclude_citations": false,
  "exclude_references": false
}
```

Response (`HTTP 202 Accepted`):
```json
{
  "job_id": "97e68bc3-3b1a-4de1-9721-a39c04981442",
  "analysis_id": "b182cb20-6d45-4afb-967c-d67bce1843ad",
  "status": "queued",
  "current_step": "enqueued",
  "progress_percent": 0,
  "error_code": null,
  "error_message": null,
  "created_at": "2026-10-14T12:00:00Z",
  "completed_at": null
}
```

---

### GET /api/v1/analyses/{analysis_id} (Inspection Model)
Response (`HTTP 200 OK`):
```json
{
  "analysis_id": "b182cb20-6d45-4afb-967c-d67bce1843ad",
  "submission_document_id": "4098c9d5-7a1d-48b2-adc1-5f4fc8422ced",
  "submission_filename": "quantum_thesis.pdf",
  "mode": "direct",
  "status": "completed",
  "overall_lexical_coverage_percent": 75.4,
  "overall_semantic_coverage_percent": 0.0,
  "net_adjusted_score_percent": 75.4,
  "matched_source_count": 1,
  "total_findings_count": 2,
  "created_at": "2026-10-14T12:00:00Z",
  "completed_at": "2026-10-14T12:00:01Z",
  "sources": [
    {
      "reference_document_id": "dfad71e2-cfd5-4e31-b396-90ab29ce8293",
      "source_title": "quantum_reference.txt",
      "matched_passage_count": 2,
      "lexical_coverage_percent": 75.4,
      "semantic_coverage_percent": 0.0
    }
  ],
  "findings": [
    {
      "finding_id": "find-001",
      "category": "exact_copy",
      "confidence": "high",
      "submission_start_offset": 0,
      "submission_end_offset": 142,
      "submission_excerpt": "Quantum computing harnesses the phenomena of quantum mechanics...",
      "reference_document_id": "dfad71e2-cfd5-4e31-b396-90ab29ce8293",
      "reference_source_title": "quantum_reference.txt",
      "reference_start_offset": 0,
      "reference_end_offset": 142,
      "reference_excerpt": "Quantum computing harnesses the phenomena of quantum mechanics...",
      "reference_page_number": 1,
      "lexical_similarity": 1.0,
      "semantic_similarity": 0.0,
      "is_quoted": false,
      "is_excluded": false
    }
  ]
}
```
