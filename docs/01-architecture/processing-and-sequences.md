# Processing Workflows & Sequence Diagrams

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Overview

This document formalizes the execution sequences across all operational flows. Every diagram specifies interactions between the Client Browser, API Orchestrator, Redis Message Queue, Background Worker Pool, File Storage, and PostgreSQL/pgvector database.

---

## 2. Sequence 1: Mode A — Direct Document Comparison

Mode A performs real-time pairwise comparison between one submitted document and one reference document without requiring pre-indexed persistent collections.

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Client Browser
    participant API as FastAPI Orchestrator
    participant Storage as File Storage
    participant DB as PostgreSQL + pgvector
    participant Redis as Redis Queue
    participant Worker as Background Worker

    User->>API: POST /api/v1/analyses (mode="direct", sub_file, ref_file)
    API->>Storage: Validate & save raw files (sub.pdf, ref.docx)
    API->>DB: INSERT into documents (sub, ref)
    API->>DB: INSERT into analysis_jobs (status="queued", mode="direct")
    API->>Redis: Enqueue job (job_id, analysis_id)
    API-->>User: HTTP 202 Accepted {job_id, analysis_id, status: "queued"}

    Redis->>Worker: Dequeue job payload
    Worker->>DB: UPDATE analysis_jobs SET status="processing", started_at=NOW()

    par Document Extraction
        Worker->>Storage: Read sub.pdf
        Worker->>Worker: PyMuPDF extract, normalize Unicode, segment passages
        Worker->>Storage: Read ref.docx
        Worker->>Worker: python-docx extract, normalize Unicode, segment passages
    end

    Worker->>Worker: Compute Winnowing fingerprints for sub & ref passages
    Worker->>Worker: Identify exact hash intersections (Lexical Candidates)
    Worker->>Worker: Generate multilingual-e5 embeddings for sub & ref passages
    Worker->>Worker: Compute pairwise cosine similarities (Semantic Candidates)

    Worker->>Worker: Merge & deduplicate candidate passage pairs
    Worker->>Worker: Execute Token-Level Local Alignment on candidates
    Worker->>Worker: Deduplicate overlapping spans & calculate Dual Coverage (Lexical & Semantic)

    Worker->>DB: INSERT findings, UPDATE analyses, UPDATE analysis_jobs (status="completed")
    
    loop Client Polling / WebSocket
        User->>API: GET /api/v1/analyses/{analysis_id}/status
        API->>DB: SELECT status FROM analysis_jobs
        API-->>User: {status: "completed"}
    end

    User->>API: GET /api/v1/analyses/{analysis_id}
    API->>DB: SELECT analysis, findings, sources
    API-->>User: HTTP 200 OK (Full Analysis Results & Highlight Offsets)
```

---

## 3. Sequence 2: Mode B — One-to-Many Comparison

Mode B compares one submitted document against a user-supplied batch of up to 10 reference files simultaneously.

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Client Browser
    participant API as FastAPI Orchestrator
    participant Storage as File Storage
    participant DB as PostgreSQL
    participant Redis as Redis Queue
    participant Worker as Background Worker

    User->>API: POST /api/v1/analyses (mode="one_to_many", sub_file, ref_files[])
    API->>Storage: Save sub file & batch of reference files
    API->>DB: Create documents & analysis_job record
    API->>Redis: Enqueue batch job
    API-->>User: HTTP 202 Accepted {job_id, status: "queued"}

    Redis->>Worker: Pop job
    Worker->>DB: Set status="processing"

    Worker->>Worker: Extract & segment submission document
    Worker->>Worker: Extract, segment & index all reference files (Ephemeral Index)
    
    Worker->>Worker: Multi-source candidate retrieval (Winnowing + Dense Vectors)
    Worker->>Worker: Local alignment against retrieved source passages
    Worker->>Worker: Attribute findings to individual source IDs
    Worker->>Worker: Unified geometric interval deduplication across all sources
    
    Worker->>DB: Persist findings & aggregate scores
    Worker->>DB: Set status="completed"
    User->>API: Fetch results -> Returns per-source & aggregate coverage
```

---

## 4. Sequence 3: Mode C — Indexed Corpus Search

Mode C queries an uploaded document against an authorized, pre-indexed persistent reference collection in PostgreSQL and `pgvector`.

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Client Browser
    participant API as FastAPI Orchestrator
    participant DB as PostgreSQL + pgvector
    participant Redis as Redis Queue
    participant Worker as Background Worker

    User->>API: POST /api/v1/analyses (mode="corpus", collection_id, sub_file)
    API->>DB: Verify user has READ permission on collection_id
    alt Unauthorized Collection
        API-->>User: HTTP 403 Forbidden (AUTH_INSUFFICIENT_COLLECTION_PERMISSIONS)
    else Authorized
        API->>DB: Create job record (mode="corpus", collection_id)
        API->>Redis: Enqueue job
        API-->>User: HTTP 202 Accepted {job_id, status: "queued"}
    end

    Redis->>Worker: Pop job
    Worker->>DB: Set status="processing"
    Worker->>Worker: Extract text, normalize Unicode, segment submission passages
    Worker->>Worker: Compute submission Winnowing hashes & E5 query embeddings

    par Stage 1: Candidate Retrieval
        Worker->>DB: Query Winnowing inverted index scoped to collection_id
        Worker->>DB: SELECT top-50 vector nearest neighbors via pgvector (<#>) scoped to collection_id
    end

    Worker->>Worker: Merge & rank candidate passages (Lexical + Semantic)
    Worker->>Worker: Stage 2: Token-level local alignment on top candidates
    Worker->>Worker: Categorize matches & compute aggregate non-overlapping coverage
    Worker->>DB: Persist findings, attribution links, set status="completed"
```

---

## 5. Sequence 4: Reference Document Ingestion & Corpus Indexing

Authorized users or administrators add reference materials to a persistent collection.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Admin / Ingestion Pipeline
    participant API as FastAPI Orchestrator
    participant Storage as File Storage
    participant DB as PostgreSQL + pgvector
    participant Redis as Redis Queue
    participant Worker as Background Worker

    Admin->>API: POST /api/v1/collections/{collection_id}/documents (file, metadata)
    API->>DB: Verify WRITE permission on collection_id
    API->>Storage: Store reference file
    API->>DB: INSERT into documents (status="pending_index")
    API->>Redis: Enqueue ingestion job
    API-->>Admin: HTTP 202 Accepted {document_id, status: "pending_index"}

    Redis->>Worker: Dequeue ingestion job
    Worker->>Storage: Read document
    Worker->>Worker: Extract text, record page/paragraph metadata
    Worker->>Worker: Segment text into passages (100–300 words)
    Worker->>DB: INSERT into passages (with exact Unicode code-point offsets)
    Worker->>Worker: Generate Winnowing fingerprints
    Worker->>DB: INSERT into fingerprints
    Worker->>Worker: Generate multilingual-e5 embeddings with "passage: " prefix
    Worker->>DB: INSERT into embeddings (vector(768))
    Worker->>DB: UPDATE documents SET index_status="INDEXED"
```

---

## 6. Sequence 5: Background Job State Lifecycle & Resilience

```mermaid
stateDiagram-v2
    [*] --> queued: Enqueued via API
    queued --> processing: Worker picks up task
    processing --> completed: All steps succeed
    processing --> failed: Exception / Unhandled Error / Timeout
    queued --> cancelled: User explicitly cancels job
    processing --> cancelled: Cancellation signal received by worker
    failed --> queued: Retry on transient failure (max 2 retries)
    failed --> [*]: Permanent failure recorded in DB
    completed --> [*]: Findings available for inspection
    cancelled --> [*]: Resources released
```

---

## 7. Sequence 6: Analysis Report Generation (PDF Export)

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Reviewer
    participant API as FastAPI Orchestrator
    participant DB as PostgreSQL
    participant Storage as File Storage
    participant Worker as Reporting Worker

    User->>API: POST /api/v1/analyses/{id}/report (options: include_notes, language)
    API->>DB: SELECT analysis, findings, reviews, exclusions WHERE id = :id
    API->>Worker: Dispatch report generation task
    Worker->>Worker: Render layout template (metadata, charts, side-by-side diffs)
    Worker->>Worker: Apply Indic typography fonts (Noto Sans / Devanagari / Telugu)
    Worker->>Storage: Write immutable PDF artifact (storage/reports/rep_XYZ.pdf)
    Worker->>DB: UPDATE analyses SET report_path = "storage/reports/rep_XYZ.pdf"
    Worker-->>API: Report ready
    API-->>User: HTTP 200 OK (Stream PDF file attachment)
```

---

## 8. Sequence 7: Reliable Multi-Tier Document Deletion Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as Document Owner
    participant API as FastAPI Orchestrator
    participant DB as PostgreSQL + pgvector
    participant Ledger as Durable Deletion Ledger
    participant Redis as Redis Queue & Cache
    participant Storage as File Storage

    User->>API: DELETE /api/v1/documents/{document_id}
    API->>DB: 1. Verify user owns document_id
    API->>DB: 2. UPDATE documents SET status='DELETING' (Immediate Access Restriction)
    API->>Ledger: 3. Append deletion tombstone {document_id, status: 'PENDING'}
    API->>Redis: 4. Set fencing token 'fence:doc:{id}' & cancel queued tasks
    
    note over Redis,DB: In-flight workers detect fencing token and abort gracefully
    
    API->>DB: 5. BEGIN TRANSACTION (Cascade delete findings, embeddings, fingerprints, passages, documents)
    API->>DB: COMMIT TRANSACTION
    API->>Storage: 6. Idempotent unlink (raw upload, normalized cache, generated PDFs)
    API->>Redis: 7. Invalidate analysis job status & candidate passage caches
    API->>Ledger: 8. UPDATE ledger SET status='COMPLETED'
    API-->>User: HTTP 204 No Content

    note over DB,Ledger: Post-DR Restore: Startup hook reconciles restored DB against Ledger
```
