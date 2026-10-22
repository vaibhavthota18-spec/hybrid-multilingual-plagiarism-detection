# Technology Decisions & Architectural Rationale

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Overview

This document provides technical justifications, trade-off analyses, and alternatives considered for every major technology selection in the platform.

---

## 2. Comprehensive Technology Stack Evaluation

### 2.1 Frontend Framework: React with TypeScript & Tailwind CSS
- **Selection:** React 18+, TypeScript 5+, Tailwind CSS 3+, Vite.
- **Alternatives Considered:**
  - *Next.js (SSR/Fullstack):* Rejected. Server-side rendering is unnecessary for an authenticated document analysis utility and introduces complex Node.js backend dependencies that duplicate FastAPI.
  - *Vue 3 / Svelte:* Considered, but rejected due to smaller ecosystem for complex enterprise diffing viewers, virtualized lists, and OpenAPI TypeScript client generators.
- **Rationale:**
  - Type-safe integration: OpenAPI schema can automatically generate complete TypeScript client SDKs and interface types (`openapi-typescript`).
  - Rich document rendering: Broad ecosystem for high-performance virtualized document viewing (react-window) and side-by-side synchronized scroll handling.
  - Tailwind CSS provides rapid, accessible UI styling with predictable CSS bundle sizes.

### 2.2 Backend Framework: Python with FastAPI & Pydantic
- **Selection:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2 (asyncpg).
- **Alternatives Considered:**
  - *Node.js / Express or NestJS:* Rejected. While high-concurrency I/O is excellent, Node.js lacks native, high-performance bindings for Indic NLP tokenization, PyTorch transformers, and PyMuPDF text extraction.
  - *Go / Rust:* Rejected for the main application layer due to the heavy reliance on Python-centric machine learning models (`transformers`, `sentence-transformers`, `torch`).
  - *Django:* Rejected due to synchronous ORM overhead and rigid monolithic structures unsuited for modern async vector APIs.
- **Rationale:**
  - FastAPI provides native asynchronous request processing, automatic OpenAPI 3.1 generation, and strict type validation via Pydantic v2.
  - Python is the undisputed standard ecosystem for natural language processing, transformer inference, and data science evaluation.

### 2.3 Persistence & Vector Store: PostgreSQL with pgvector
- **Selection:** PostgreSQL 16+ with the `pgvector` extension.
- **Alternatives Considered:**
  - *Dedicated Vector DBs (Milvus, Qdrant, Pinecone, Weaviate):* Rejected for core baseline. Introducing a separate vector database creates distributed state, complex two-phase commit transactions, multi-database backup overhead, and cross-database authorization synchronization issues.
  - *Elasticsearch / OpenSearch:* Considered for BM25 and vector search, but requires substantial JVM memory footprint ($>4$ GB baseline) and complicates local developer setups.
- **Rationale:**
  - Unified ACID transactions: Document metadata, passage offsets, collection access permissions, and vector embeddings reside in the same relational engine.
  - Filtered vector search: SQL queries can seamlessly combine relational permission predicates (`WHERE collection_id IN (...)`) with vector similarity operators (`ORDER BY embedding <#> :query_vector`).
  - Native migration support via Alembic.

### 2.4 Asynchronous Worker & Queue Broker: Redis with RQ (Redis Queue)
- **Selection:** Redis 7+ with Python RQ (Redis Queue).
- **Alternatives Considered:**
  - *Celery:* Considered. Highly capable but introduces significant configuration complexity, challenging debugging on Windows environments, broker-result-backend synchronization quirks, and heavy boilerplate.
  - *RabbitMQ / Kafka:* Unnecessary architectural overkill for document comparison task queues.
- **Rationale:**
  - Python RQ is lightweight, robust, native to Python, and explicitly designed for long-running CPU-bound tasks.
  - Direct job state inspection and timeout handling with minimal operational overhead.
  - Fallback strategy: If multi-language worker pools or advanced task routing are demanded in Phase 7, Celery can be introduced via an identical interface adapter.

### 2.5 Architectural Topology: Modular Monolith
- **Selection:** Modular Monolith with separate asynchronous worker processes.
- **Alternatives Considered:**
  - *Microservices (e.g., Ingestion Service, ML Service, Scoring Service, Auth Service):* Strongly rejected. Microservices introduce premature distributed systems complexity: network serialization latency, distributed tracing overhead, deployment friction, and transaction orchestration overhead for a single unified product.
- **Rationale:**
  - High internal cohesion with strict module boundaries.
  - Zero inter-service network latency for in-memory operations.
  - Independent horizontal scaling: Worker containers can scale independently from API web containers.

### 2.6 Vector Search Strategy: Exact Nearest-Neighbor Search First
- **Selection:** Exact $k$-NN search using PostgreSQL `pgvector` inner product (`<#>`) on unit-normalized vectors.
- **Alternatives Considered:**
  - *HNSW / IVFFlat Approximate Nearest Neighbor (ANN):* Deferred to conditional optimization (ADR-0004).
- **Rationale:**
  - Guaranteed 100% recall: In academic plagiarism detection, missing a matching source due to ANN graph index approximation is unacceptable during early evaluation.
  - Modest dataset scale: For reference collections under 10,000 documents (approx. 200,000 passages), modern CPUs execute exact brute-force vector scans in $<100$ ms.

### 2.7 AI Model Strategy: Multilingual E5 Baseline with Structured Evaluation
- **Selection:** `intfloat/multilingual-e5-base` (768-dim) as the primary baseline; LaBSE and BGE-M3 for benchmark ablation.
- **Alternatives Considered:**
  - *English-only models (all-MiniLM-L6-v2, bge-base-en):* Incapable of handling Hindi or Telugu text.
  - *OpenAI text-embedding-3 / Commercial APIs:* Rejected. Breaches academic privacy mandates (sending unpublished student manuscripts to third-party APIs), introduces recurring financial costs, and prevents offline air-gapped institutional deployments.
- **Rationale:**
  - Pre-trained on 100+ languages including Hindi and Telugu.
  - Strong benchmark performance on cross-lingual retrieval (BEIR, MTEB).
  - Practical inference footprint: ~1.1 GB model weights, capable of fast CPU inference on standard 8-core host systems.
