# System Context & Architecture Boundaries

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. System Context Overview

The **Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System** operates as an autonomous, self-contained web platform designed for academic and research document originality analysis. The system provides clear separation between user interactions, application orchestration, background computation, and persistence layers.

---

## 2. System Context Diagram (C4 Level 1)

```mermaid
flowchart TD
    subgraph Users ["Human Actors"]
        Student["Student / Author<br>(Direct Comparison & Self-Check)"]
        Researcher["Academic Researcher<br>(Batch & Manuscript Attribution)"]
        Educator["Educator / Evaluator<br>(Assignment & Corpus Review)"]
        Reviewer["Academic Reviewer<br>(Human Review & Finding Verification)"]
        Admin["Institutional Admin<br>(Corpus & Access Governance)"]
    end

    subgraph SystemBoundary ["Hybrid Multilingual Plagiarism Platform Boundary"]
        WebUI["Web Application Frontend<br>(React, TypeScript, Tailwind, Vite)"]
        APIServer["API Orchestrator<br>(FastAPI, Auth, Ingestion, Scoring)"]
        WorkerService["Background Worker Pool<br>(Python, PyMuPDF, ML Inference, Alignment)"]
        RelationalStore["Primary Database & Vector Store<br>(PostgreSQL 16 + pgvector)"]
        QueueBroker["Message & Job Broker<br>(Redis 7)"]
        FileStore["Private Document Storage<br>(Tenant-Isolated Local / Encrypted Volume)"]
    end

    subgraph ExternalSystems ["External Infrastructure & Dependencies"]
        ModelRegistry["Hugging Face Model Registry<br>(Initial Download of multilingual-e5-base)"]
        ClientBrowser["Client Browser Runtime<br>(PDF Rendering, Highlight Sync)"]
    end

    %% User Interactions
    Student -->|Uploads files, reviews report| WebUI
    Researcher -->|Submits batch comparisons| WebUI
    Educator -->|Queries corpus, inspects findings| WebUI
    Reviewer -->|Submits human reviews & notes| WebUI
    Admin -->|Manages reference collections| WebUI

    %% Web UI to API
    WebUI -->|REST / OpenAPI 3.1 over HTTPS| APIServer
    WebUI -.->|Renders in browser| ClientBrowser

    %% Internal Orchestration
    APIServer -->|Persists metadata, auth, job state| RelationalStore
    APIServer -->|Enqueues async processing jobs| QueueBroker
    APIServer -->|Streams uploaded files| FileStore

    %% Worker Operations
    QueueBroker -->|Pulls jobs| WorkerService
    WorkerService -->|Reads original documents| FileStore
    WorkerService -->|Queries & updates vectors, findings| RelationalStore
    WorkerService -->|Writes generated PDF reports| FileStore

    %% External Model Dependencies
    WorkerService -.->|Initial model pull on startup| ModelRegistry
```

---

## 3. Actors & Personas

| Actor | Role & Boundary Responsibilities |
|---|---|
| **Student / Author** | Uploads individual drafts for Mode A or Mode B comparisons; receives immediate originality feedback; does not have administrative rights to alter institutional collections. |
| **Academic Researcher** | Performs multi-document comparisons (Mode B); reviews detailed lexical and semantic coverage scores; exports verified PDF dossiers. |
| **Educator / Evaluator** | Executes Mode C searches against institutional reference corpora; analyzes flagged student submissions; accesses human review tools. |
| **Academic Reviewer** | Verified subject-matter expert who inspects flagged passages, applies labels (`VALID_CITATION`, `SUSPECTED_PLAGIARISM`, etc.), and verifies context. |
| **Institutional Admin** | Manages departmental reference collections, controls user permissions, monitors storage quotas, and enforces document retention policies. |

---

## 4. External Dependencies & Operational Boundaries

1. **Model Hub (`intfloat/multilingual-e5-base`):** Pre-trained transformer weights are pulled from Hugging Face Hub during container build or initial setup and stored locally in a mounted cache volume. **No live internet access is required during runtime inference.**
2. **Client Browser Runtime:** The frontend executes inside modern standard browsers (Chrome, Firefox, Safari, Edge). It renders side-by-side textual diffs and converts Unicode code points to UTF-16 DOM character ranges for visual highlighting.
3. **Storage Subsystem:** Documents are stored in an encrypted, isolated directory structure outside the public web server root. In local deployments, this is a dedicated filesystem volume (`./storage`); in cloud environments, an S3-compatible bucket with strict tenant policies.
