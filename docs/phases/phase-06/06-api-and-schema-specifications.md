# Phase 6 — API and Schema Specifications

## 1. REST Endpoints

### 1.1 Review Finding Decision
- **Route:** `PATCH /api/v1/analyses/{analysis_id}/findings/{finding_id}/review`
- **Request Body:**
```json
{
  "decision": "keep" | "exclude" | "quoted_cited" | "needs_review" | "unreviewed",
  "notes": "Optional reviewer justification..."
}
```
- **Response Model:** `ReviewFindingResponse`
```json
{
  "finding": {
    "finding_id": "string",
    "review_decision": "string",
    "reviewer_notes": "string",
    "reviewer_updated_at": "2026-10-14T22:30:00Z",
    ...
  },
  "analysis_id": "string",
  "original_evidence_coverage_percent": 62.50,
  "reviewer_adjusted_coverage_percent": 0.00,
  "reviewed_findings_count": 1,
  "total_findings_count": 1,
  "status_counts": {
    "keep": 0,
    "exclude": 1,
    "quoted_cited": 0,
    "needs_review": 0,
    "unreviewed": 0
  }
}
```

### 1.2 Export Multi-Format Report
- **Route:** `GET /api/v1/analyses/{analysis_id}/report?format=pdf|html|json&include_notes=true`
- **Query Parameters:**
  - `format`: `pdf` (default), `html`, `json`.
  - `include_notes`: `true` (default), `false`.
- **Response:**
  - `pdf`: Binary stream with `application/pdf`.
  - `html`: Rendered HTML text with `text/html; charset=utf-8`.
  - `json`: JSON structure with `application/json`.

## 2. Database Schema Extensions (SQLite)
The following columns were added to the local SQLite development adapter via automated zero-downtime migrations:

### `analyses` Table
- `reviewer_adjusted_coverage_percent REAL NULL`
- `reviewed_findings_count INTEGER DEFAULT 0`
- `reviewer_notes TEXT NULL`

### `analysis_findings` Table
- `review_decision TEXT DEFAULT 'unreviewed'`
- `reviewer_notes TEXT NULL`
- `reviewer_updated_at TEXT NULL`
