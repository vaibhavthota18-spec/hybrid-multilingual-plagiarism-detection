# 05 — pgvector Integration & High-Dimensional Semantic Retrieval

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Files:** `apps/backend/src/plagiarism/storage/vector_store.py`, `apps/backend/alembic/versions/0002_pgvector_384_dimensions.py`  
**Status:** IMPLEMENTED & VERIFIED  

---

## 1. Vector Dimension Alignment (384 Dimensions)

The initial migration had provisioned a 768-dimensional column for `intfloat/multilingual-e5-base`. In Phase 4, the system standardized on `intfloat/multilingual-e5-small` to maintain low latency (<150ms per batch) and high inference efficiency on CPU instances.

Migration `0002_pgvector_384_dimensions.py` created the production table:

```sql
CREATE TABLE IF NOT EXISTS passage_embeddings (
    passage_id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL,
    sequence_index INTEGER NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    model_id VARCHAR(128) NOT NULL,
    model_revision VARCHAR(64) NOT NULL,
    embedding vector(384) NOT NULL,
    text_hash VARCHAR(64) NOT NULL,
    created_at VARCHAR(64) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_passage_emb_doc ON passage_embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_passage_emb_cosine_hnsw ON passage_embeddings USING hnsw (embedding vector_cosine_ops);
```

---

## 2. PgVectorRepository Implementation

`PgVectorRepository` inherits from `VectorIndex` in `apps/backend/src/plagiarism/storage/vector_store.py` and implements exact cosine distance vector search using native pgvector operators:

```python
class PgVectorRepository(VectorIndex):
    def search_candidates(self, query_vectors: np.ndarray, candidate_document_ids: List[str], top_k: int = 5, min_similarity: float = 0.50):
        # ...
        search_sql = """
        SELECT passage_id, document_id, start_offset, end_offset,
               text_content, 1 - (embedding <=> $1) AS cosine_similarity
        FROM passage_embeddings
        WHERE document_id = ANY($2::text[])
          AND (1 - (embedding <=> $1)) >= $3
        ORDER BY embedding <=> $1 ASC
        LIMIT $4;
        """
        # ...
```

### Key Performance Benefits
1. **Cosine Operator (`<=>`):** Avoids full-table scans by utilizing HNSW and IVFFlat vector index trees.
2. **Batch Registration:** Uses `pgvector.asyncpg.register_vector` to stream numpy float32 buffers directly over PostgreSQL binary protocol without string serialization overhead.
3. **Graceful Fallback:** If PostgreSQL is unreachable, `get_vector_repository()` safely falls back to `SQLiteVectorRepository`.
