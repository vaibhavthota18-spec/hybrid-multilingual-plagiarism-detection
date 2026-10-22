# Phase 4 Database & API Report: Schema Extensions & Endpoints

## 1. Relational Schema Migration

The SQLite metadata database (`storage/local_metadata.db`) was migrated with the following Phase 4 schema extensions:

### A. New Table: `passage_embeddings`
Stores dense vectors as raw IEEE 754 float32 byte buffers (`BLOB`) with cascade deletion on document deletion:
```sql
CREATE TABLE IF NOT EXISTS passage_embeddings (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    passage_id TEXT NOT NULL,
    sequence_index INTEGER NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    model_id TEXT NOT NULL,
    model_revision TEXT NOT NULL,
    embedding BLOB NOT NULL,
    embedding_dim INTEGER NOT NULL,
    text_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);
```

### B. Analysis Table Alterations
- Added `detection_mode TEXT DEFAULT 'hybrid'` to `analyses`.
- Added `hybrid_evidence_coverage_percent REAL DEFAULT 0.0` to `analyses`.
- Added `language_pair TEXT` and `model_name TEXT` to `analysis_findings`.

---

## 2. API Contract & Endpoint Updates

All endpoints adhere to OpenAPI 3.1 specification (`contracts/openapi.yaml`).

### A. `GET /api/v1/analyses/models/info`
Returns active AI model metadata, dimensions, thresholds, and runtime hardware:
```json
{
  "model_name": "intfloat/multilingual-e5-small",
  "revision": "614241f622f53c4eeff9890bdc4f31cfecc418b3",
  "embedding_dimension": 384,
  "max_sequence_length": 512,
  "runtime_device": "cpu",
  "is_gpu": false,
  "query_prefix": "query: ",
  "passage_prefix": "passage: ",
  "normalization": "L2",
  "paraphrase_threshold": 0.82,
  "translation_threshold": 0.80
}
```

### B. `POST /api/v1/analyses`
Updated `CreateAnalysisRequest` schema with optional `detection_mode`:
```json
{
  "submission_document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "reference_document_id": "7ca85f64-5717-4562-b3fc-2c963f66afa7",
  "mode": "direct",
  "detection_mode": "hybrid"
}
```
Accepts: `"hybrid"`, `"lexical"`, or `"semantic"`.

### C. `GET /api/v1/analyses/{analysis_id}`
Returns complete analysis report including Phase 4 metrics:
- `detection_mode`
- `overall_lexical_coverage_percent`
- `overall_semantic_coverage_percent`
- `hybrid_evidence_coverage_percent`
- `net_adjusted_score_percent`
- `model_metadata`
- `findings[]`: each finding contains `language_pair`, `model_name`, `lexical_similarity`, and `semantic_similarity`.
