# Phase 3 Architecture and Processing Pipeline

## 1. Architectural Philosophy

Phase 3 implements the lexical detection tier within the modular monolith architecture outlined in ADR-0001. The pipeline strictly operates on native Windows 11 hardware without virtualization, leveraging Python's CPU efficiency for deterministic algorithm calculations and SQLite for transactional persistence.

### Key Architectural Tenets:
1. **Explainable Evidence**: Plagiarism scores are strictly substantiated by inspectable string matches with exact character start/end coordinates. No "black box" numbers.
2. **Deterministic Reproducibility**: Given document $A$ and document $B$, running the pipeline multiple times across reboots yields identical fingerprints, identical matches, and identical coverage percentages.
3. **Strict Separation of Concerns**: Algorithm implementations (`services/lexical/`) have zero coupling to HTTP request handling or database logic. They accept plain text or tokens and return typed mathematical primitives.
4. **Boundary Isolation**: Lexical similarity calculates verbatim and near-verbatim string overlap. Dense vector semantic embeddings and cross-lingual translation are explicitly deferred to Phase 4.

---

## 2. Component Design & Module Architecture

```mermaid
graph TD
    Client[React Web Client / API Caller] -->|POST /analyses| Router[Analyses REST Router]
    Router -->|Submit Job| Executor[ThreadPoolExecutor]
    Router -->|Sync Processing| Service[LexicalAnalysisService]
    Executor -->|Worker Thread| Service

    subgraph "Lexical Algorithm Engine"
        Service --> Tokenizer[LexicalTokenizer]
        Service --> RollingHash[RollingHash64]
        Service --> Winnowing[WinnowingEngine]
        Service --> BM25[BM25Index]
        Service --> Aligner[PassageAligner]
        Service --> Coverage[CoverageCalculator]
    end

    subgraph "Persistence Tier"
        Service --> LocalDB[(SQLite local_db.py)]
        LocalDB --> DocTable[documents]
        LocalDB --> FPTable[document_fingerprints]
        LocalDB --> AnaTable[analyses]
        LocalDB --> FindTable[analysis_findings]
        LocalDB --> SrcTable[analysis_sources]
    end
```

---

## 3. End-to-End Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    participant UI as React UI (Client)
    participant API as FastAPI Router
    participant Svc as LexicalAnalysisService
    participant Algo as Lexical Engine (Winnowing/BM25)
    participant DB as SQLite Repository

    UI->>API: POST /api/v1/analyses (submission_id, mode, references)
    API->>DB: create_analysis (status="queued", progress=0%)
    API-->>UI: HTTP 202 Accepted (job_id, analysis_id)

    API->>Svc: run_analysis(analysis_id, ...)
    Svc->>DB: update_analysis_status ("processing", current_step="tokenizing")
    
    Svc->>Algo: Tokenize submission & references
    Algo-->>Svc: Token streams with (start_char, end_char)
    
    Svc->>Algo: Compute Winnowing fingerprints (k=25, w=16)
    Algo-->>Svc: Document fingerprints (hash, position)
    Svc->>DB: save_fingerprints()

    alt Corpus Mode
        Svc->>Algo: BM25 candidate retrieval across collection
        Algo-->>Svc: Top ranked reference document IDs
    end

    Svc->>Algo: Fine-grained passage alignment
    Algo-->>Svc: Raw matched spans with similarity ratios
    
    Svc->>Algo: Slicing verification against raw document text
    Algo-->>Svc: Verified findings with verbatim excerpts

    Svc->>Algo: Compute non-overlapping union coverage
    Algo-->>Svc: Overall lexical coverage % & source breakdowns

    Svc->>DB: save_analysis_results(findings, sources, coverage)
    Svc->>DB: update_analysis_status ("completed", progress=100%)

    UI->>API: GET /api/v1/analyses/{analysis_id}
    API->>DB: get_analysis() + get_findings() + get_sources()
    API-->>UI: HTTP 200 OK (Complete AnalysisResult)
```

---

## 4. Pipeline Execution States

Analyses transition through well-defined lifecycle states:
- `queued`: Record created in SQLite; job scheduled on worker executor.
- `processing`: Worker thread actively computing hashes, candidate rankings, or alignments.
  - Step: `loading_documents`
  - Step: `tokenizing_and_fingerprinting`
  - Step: `retrieving_candidates`
  - Step: `aligning_passages`
  - Step: `calculating_coverage`
  - Step: `persisting_results`
- `completed`: Pipeline finished successfully; results persisted.
- `failed`: An unhandled exception occurred; `error_message` is recorded in SQLite.
- `cancelled`: Explicit user termination via `POST /analyses/{id}/cancel`.
