# Phase 7 — Privacy & Document Lifecycle

## 1. Document Lifecycle Management
The application implements an explicit, safe lifecycle across user documents:

```mermaid
flowchart TD
    Upload["1. Ingestion (Upload)"] --> Store["2. Private Storage (storage/documents/)"]
    Store --> Index["3. Passages & Vector BLOBs (storage/db/metadata.db)"]
    Index --> Match["4. Plagiarism Comparison (Analyses & Findings)"]
    Match --> Review["5. Human Review Decisions & Audit Trail"]
    Review --> Export["6. Multi-Format Report Export (PDF/HTML/JSON)"]
    Store -.-> Delete["7. Cascading Deletion (Purge files, vectors & findings)"]
```

## 2. Foreign Key Cascading Deletion
- Executing `DELETE /api/v1/documents/{document_id}` triggers cascading cleanup:
  - Deletes raw file from `storage/documents/`.
  - Deletes passage records in `document_passages`.
  - Deletes vector embedding records in `passage_vectors`.
  - Deletes associated findings and analyses referencing the document.
- Verified in Scenario V of `verify_phase7_e2e.py`.
