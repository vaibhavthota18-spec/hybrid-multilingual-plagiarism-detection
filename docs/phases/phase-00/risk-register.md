# Project Risk Register & Mitigation Strategy

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Risk Management Framework

Risks are assessed based on **Probability** (High, Medium, Low) and **Impact** (Critical, High, Medium, Low), with concrete architectural mitigations and designated phase checkpoints.

---

## 2. Comprehensive Risk Register

| Risk ID | Risk Title | Probability | Impact | Affected Phase | Mitigation Strategy |
|---|---|---|---|---|---|
| **RSK-001** | **Telugu Semantic Model Quality Degradation** | Medium | High | Phase 4 & 5 | `multilingual-e5-base` has lower training representation for Telugu than English. *Mitigation:* Include LaBSE and BGE-M3 in benchmark ablations; preserve fine-tuning extension interface; establish separate TE-TE and EN-TE reporting. |
| **RSK-002** | **Semantic False Positives on Academic Boilerplate** | High | High | Phase 4 & 6 | Dense embeddings may flag common disciplinary definitions, standard methodology headings, or idioms. *Mitigation:* Calibrate cosine threshold $\ge 0.82$; enforce minimum token length ($\ge 15$ tokens); provide quotation/citation filtering and human review overrides. |
| **RSK-003** | **Character Offset Drift Across Runtimes** | Medium | Critical | Phase 2 & 6 | Multi-byte Indic scripts cause discrepancies between Python code points, UTF-8 bytes, and JavaScript UTF-16 units. *Mitigation:* Mandate canonical Unicode code-point offsets in all backend layers (ADR-0002, `module-contracts.md`); provide standardized frontend `codePointToUtf16Offset` conversion helper. |
| **RSK-004** | **Incompatible Embedding Model Version Drift** | Low | Critical | Phase 4 | Querying pgvector with an embedding produced by an updated or different model returns garbage scores. *Mitigation:* Strict version locking in `model_configurations` and `embeddings.model_config_id`; enforce SQL predicates requiring identical model ID and commit SHA (ADR-0005). |
| **RSK-005** | **CPU Inference Latency Bottlenecks** | Medium | High | Phase 4 & 7 | Warmed 10-page document embedding inference may exceed the 180s p95 threshold on CPU-only hosts. *Mitigation:* Implement batching ($B=16$); support ONNX Runtime INT8 quantization; provide optional CUDA container configuration for GPU servers. |
| **RSK-006** | **Cross-Tenant Corpus Data Leakage** | Low | Critical | Phase 2 & 7 | A malicious user manipulates API parameters to query or download unauthorized reference documents. *Mitigation:* Hard SQL join on `collection_permissions` verified before query execution; return HTTP 403 on permission mismatch (ADR-0006). |
| **RSK-007** | **Incomplete Hard Deletion (Right to Erasure)** | Medium | High | Phase 2 & 7 | Document record is deleted from PostgreSQL but orphaned files or vector embeddings remain. *Mitigation:* Database `ON DELETE CASCADE` foreign keys combined with transactional storage unlinking and post-deletion verification tests. |
| **RSK-008** | **Overlapping Match Score Inflation** | Low | High | Phase 3 & 4 | Naively summing multiple source match spans double-counts overlapping characters, yielding scores $>100\%$. *Mitigation:* Strict geometric interval union algorithm ($\mathcal{U} = \bigcup [s_i, e_i)$) bounded by eligible code points (documented in `offsets-and-scoring.md`). |
| **RSK-009** | **Worker Daemon Crashes on Pathological Files** | Medium | High | Phase 2 & 7 | Malformed PDFs or zip bombs cause worker out-of-memory errors. *Mitigation:* Bounded container memory limits; `defusedxml` in DOCX; state tracking transitions jobs to `failed` upon unhandled worker exit. |
| **RSK-010** | **Benchmark Split Data Leakage** | Medium | Critical | Phase 5 | Paraphrased or translated variants of the same source paper appearing across development and test partitions, yielding false high accuracy. *Mitigation:* Mandatory source-grouped partitioning (`source_group_id`); automated script assertions ensuring disjoint partitions (ADR-0008). |
| **RSK-011** | **Copyright & Licensing Violations on Corpora** | Medium | High | Phase 2 & 4 | Users upload copyrighted textbooks into shared reference collections. *Mitigation:* Compulsory license declaration (`CC-BY`, `Institutional-Internal`) on ingestion; restrict raw full-text viewing to authorized members only. |
| **RSK-012** | **Host Memory Starvation on Small Servers** | Medium | High | Phase 7 | Running web, database, Redis, and 4 workers on servers with $<16$ GB RAM leads to OOM kills. *Mitigation:* Document minimum hardware requirements (16 GB RAM); default to 2 worker processes in `.env.example` with dynamic concurrency tuning. |
