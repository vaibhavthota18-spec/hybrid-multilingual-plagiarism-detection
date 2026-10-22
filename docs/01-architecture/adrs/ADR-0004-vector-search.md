# ADR-0004: Exact Vector Search First vs. Conditional HNSW

- **Status:** Accepted
- **Deciders:** Principal Software Architect, Database Architect, IR Engineer
- **Date:** October 2026
- **Technical Story:** Vector indexing strategy in PostgreSQL pgvector

---

## Context
Vector search over dense sentence embeddings can be executed either via exact nearest-neighbor search (flat brute-force scan) or approximate nearest-neighbor (ANN) search using graph indexes like HNSW (Hierarchical Navigable Small World) or inverted file indexes (IVFFlat).
In academic plagiarism detection, false negatives (failing to retrieve an actual plagiarized source because the ANN index took an approximate graph path) damage system trust.

## Decision
1. **Initial Baseline (Phases 1–4):** We implement **Exact Vector Nearest-Neighbor Search** using PostgreSQL `pgvector` with the negative inner product operator (`<#>`) over unit-normalized L2 vectors:
   - *Operator Semantics:* Computes $-(u \cdot v)$. For unit vectors, $u \cdot v = \cos(\theta) \in [-1, 1]$. Hence, `<#>` returns values in $[-1, 1]$, where $-1.0$ represents identical vectors.
   - *Ordering & Filter:* Ascending order (`ORDER BY embedding <#> :query_vector ASC`) correctly orders closest vectors first. Calibrated threshold filter: `WHERE (embedding <#> :query_vector) <= -:calibrated_threshold`.
2. **Conditional Optimization (Phase 5/7):** We establish a clear trigger for **HNSW Indexing**:
   - *Trigger Criteria:* When indexed reference corpus passages exceed 200,000 (approx. 10,000 documents) OR Stage 1 vector query latency exceeds 500 ms p95.
   - *Index Specification:* `CREATE INDEX ON embeddings USING hnsw (embedding vector_ip_ops) WITH (m = 16, ef_construction = 64);`
   - *Acceptance Gate:* Empirical evaluation must prove HNSW achieves $\ge 98\%$ recall relative to exact search.

## Alternatives Considered
1. **HNSW from Day 1:** Rejected. Introduces unnecessary indexing build overhead during testing, requires tuning `ef_search`, and consumes 1.5x additional RAM before corpus scale demands it.
2. **External Vector Database (Qdrant/Milvus):** Rejected to avoid dual-database state management and cross-system transaction complexity (see ADR-0001).

## Rationale
Exact search is 100% deterministic, guarantees zero ANN recall loss, and for collections under 1,000 documents (approx. 20,000 passages), executes in $<60$ ms on modern multi-core CPUs.

## Consequences & Trade-offs
- **Positive:** Absolute ground-truth recall during development and evaluation phases; zero index build latency during document ingestion.
- **Negative:** Linear query scan time $O(N)$ with respect to passage count; requires monitoring to trigger HNSW when scale thresholds are breached.

## Validation Requirements
Automated query performance tests profiling vector query duration at 1,000, 5,000, and 10,000 document corpus sizes.
