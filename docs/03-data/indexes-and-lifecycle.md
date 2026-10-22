# Index Architecture & Data Lifecycle Management

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Index Architecture & Physical Storage

The platform maintains three complementary indexing structures in PostgreSQL to power Stage 1 candidate retrieval:

### 1.1 Inverted Fingerprint Index (Winnowing Rolling Hashes)
- **Table:** `fingerprints`
- **Columns:** `hash_value` (BIGINT), `passage_id` (UUID), `document_id` (UUID), `start_offset`, `end_offset`.
- **Parameter Semantics:** Provisional character $k$-gram $k_{\text{char}} = 25$ characters, window size $w_{\text{hashes}} = 16$ consecutive $k$-gram hashes.
- **Window Text Span & Guarantee:** The sliding hash window covers $k + w - 1 = 40$ characters of text. Any identical substring of length $t \ge 40$ characters is guaranteed to produce at least one shared fingerprint.
- **Tie-Breaking Rule:** Rightmost minimum hash selected in sliding window ties.
- **Verification Rule:** Hash collisions in Stage 1 are verified and filtered in Stage 2 against exact text offsets.
- **Physical Index:** Standard B-Tree index:
  ```sql
  CREATE INDEX idx_fingerprints_hash ON fingerprints(hash_value);
  ```
- **Lookup Mechanics:** Given submission fingerprints $H = \{ h_1, h_2, \dots, h_p \}$, the query executes:
  ```sql
  SELECT passage_id, document_id, COUNT(*) as shared_hashes
  FROM fingerprints
  WHERE hash_value = ANY(:hash_array)
    AND document_id IN (SELECT document_id FROM collection_documents WHERE collection_id = :target_collection)
  GROUP BY passage_id, document_id
  HAVING COUNT(*) >= :min_shared_threshold
  ORDER BY shared_hashes DESC
  LIMIT 50;
  ```

### 1.2 Lexical BM25 Search Index
- **Implementation:** In Phase 3, lexical token search is backed by an inverted token index or PostgreSQL `tsvector` with language-specific dictionaries (or an in-memory Okapi BM25 engine for ad-hoc Modes A and B).
- **Physical Index:** Generalized Inverted Index (GIN) on normalized passage tokens:
  ```sql
  CREATE INDEX idx_passages_tokens_gin ON passages USING gin (to_tsvector('simple', text_content));
  ```

### 1.3 Dense Vector Index (`pgvector`) & Distance Semantics
- **Table:** `embeddings`
- **Vector Spec:** `vector(768)` unit-normalized ($||v||_2 = 1.0$).
- **Mathematical Distance Semantics of `<#>`:**
  In PostgreSQL `pgvector`, the `<#>` operator computes the **negative inner product**:
  $$\text{op}(u, v) = -(u \cdot v) = -\sum_{i=1}^{768} u_i v_i$$
  For $L_2$ unit-normalized vectors, inner product equals cosine similarity: $u \cdot v = \cos(\theta) \in [-1, 1]$.
  Therefore:
  - Identical vectors ($\cos(\theta) = 1.0$) yield $\text{op}(u, v) = -1.0$.
  - Orthogonal vectors ($\cos(\theta) = 0.0$) yield $\text{op}(u, v) = 0.0$.
  - Opposing vectors ($\cos(\theta) = -1.0$) yield $\text{op}(u, v) = +1.0$.
- **Query Ordering & Threshold Syntax:**
  Sorting in ascending order (`ASC`, default) naturally places the most negative values (highest cosine similarities) first.
  To filter by a calibrated cosine similarity threshold $\tau \in [0, 1]$:
  $$\cos(\theta) \ge \tau \iff -(u \cdot v) \le -\tau$$
  ```sql
  SELECT 
      embeddings.passage_id, 
      embeddings.document_id, 
      (embeddings.embedding <#> :query_vector) * -1 AS cosine_similarity
  FROM embeddings
  JOIN collection_documents cd ON cd.document_id = embeddings.document_id
  WHERE cd.collection_id = :target_collection_id
    AND embeddings.model_config_id = :active_model_config
    AND (embeddings.embedding <#> :query_vector) <= -:calibrated_threshold
  ORDER BY embeddings.embedding <#> :query_vector ASC
  LIMIT :top_k;
  ```
- **Alternative Operator `<=>` (Cosine Distance):**
  PostgreSQL `pgvector` also provides the `<=>` operator calculating cosine distance ($1 - \cos(\theta) \in [0, 2]$). The negative inner product `<#>` is preferred for primary retrieval because it avoids additional square-root operations on pre-normalized vectors.
- **Conditional HNSW Trigger:** When indexed passages exceed 200,000 rows (approx. 10,000 documents), the HNSW index is activated:
  ```sql
  CREATE INDEX idx_embeddings_hnsw ON embeddings 
  USING hnsw (embedding vector_ip_ops) 
  WITH (m = 16, ef_construction = 64);
  ```

---

## 2. Model Revision Compatibility & Reindexing Lifecycle

Embeddings from different models (or different checkpoint commits of the same model) cannot be compared in vector space.

### Incompatibility Guardrail
1. Every vector row is tagged with `model_config_id` (e.g., `multilingual-e5-base-v1`).
2. Search queries strictly require `model_config_id = :current_active_model`.
3. Mismatched model searches are blocked at both application and database constraint levels.

### Reindexing Procedure (When Upgrading Models)
When an updated model (e.g., `BAAI/bge-m3`) is introduced in a future phase:
1. **Insert New Configuration:** Insert row into `model_configurations` with `is_active = FALSE`.
2. **Background Batch Reindexing:** Worker processes read raw `passages.text_content`, generate new 768/1024-dimensional vectors, and insert them into `embeddings` under the new `model_config_id`.
3. **Atomic Cutover:** Once 100% of corpus passages are re-embedded, the administrator toggles the new configuration:
   ```sql
   UPDATE model_configurations SET is_active = FALSE WHERE id = 'old-model';
   UPDATE model_configurations SET is_active = TRUE WHERE id = 'new-model';
   ```
4. **Purge Deprecated Embeddings:** After verification, old embeddings are dropped via `DELETE FROM embeddings WHERE model_config_id = 'old-model'`.

---

## 3. Multi-Tenant Collection Isolation

To guarantee that users never search or view documents outside their authorized sphere:
- **Collection-Scoped Queries:** All retrieval queries (Winnowing, BM25, and pgvector) require explicit join against `collection_permissions` and `collection_documents`.
- **Pre-Execution Gate:** If the requesting user lacks `READ` permissions on the requested `collection_id`, the API returns HTTP 403 before any query touches the database.

---

## 4. Testable Multi-Tier Data Lifecycle & Erasure Execution

In accordance with ADR-0006, document deletion permanently expunges data across distinct storage tiers. Cross-tier operations (relational database, object storage, distributed cache, and worker memory) **cannot occur in a single atomic transaction across systems**. Instead, the platform implements a reliable, staged, and verifiable deletion workflow:

### 4.1 Reliable Deletion Workflow & State Transitions

1. **Authorization Verification:**
   - The API verifies that the caller owns the target `document_id` or possesses administrative deletion privileges. If unauthorized, returns HTTP 403 Forbidden.
2. **Immediate Access Restriction (State Invalidation):**
   - The document status is immediately updated to `status = 'DELETING'` in a fast transaction. All retrieval queries, collection listings, and API views filter on `status = 'READY'`, immediately preventing any further user access or search candidate matching.
3. **Durable Deletion Ledger (Independent Tombstone):**
   - A durable tombstone is written to an independent, append-only Deletion Ledger stream (`deletion_ledger` table and replicated audit log):
     `{ledger_id, document_id, tenant_id, requested_at, status: "PENDING"}`.
   - This ledger is maintained independently of regular operational database backups, ensuring deletion records survive and remain authoritative across snapshot restore events.
4. **Job Cancellation & Worker Fencing:**
   - Active or queued RQ worker jobs processing the document are cancelled. A fencing token is set in Redis (`fence:doc:{document_id}`). In-flight background workers check this fencing token prior to database writes; if detected, the worker aborts immediately and discards intermediate results.
5. **Relational & Vector Hard Deletion (ACID Cascade):**
   - The database transaction executes hard deletion cascading through foreign keys:
     - `findings`
     - `embeddings` (in `pgvector`)
     - `fingerprints` (in inverted B-tree index)
     - `passages`
     - `collection_documents`
     - `document_sources`
     - `documents`
6. **Filesystem Unlinking (Idempotent Storage Purge):**
   - The storage service unlinks physical files:
     - Original upload artifact: `storage/uploads/{id}.*`
     - Extracted normalized text cache: `storage/cache/{id}.norm`
     - Generated analysis reports: `storage/reports/rep_{id}_*.pdf`
   - File unlinking is idempotent: missing files do not raise fatal errors.
7. **Cache & Volatile Memory Invalidation:**
   - Evicts Redis job status keys, candidate passage caches, and session buffers. Worker process memory is reclaimed upon task completion.
8. **Worker Retry Handling & Idempotent Cleanup:**
   - Background cleanup workers poll unconfirmed deletion tasks from the Deletion Ledger. If storage file locks (e.g. OneDrive or OS file handle contention) or transient network partitions prevent immediate unlinking, the worker retries with exponential backoff up to 5 times.
9. **Verifiable Completion State:**
   - Once all storage files and relational rows are verified purged, the Deletion Ledger transitions to `status = "COMPLETED"`.
10. **Backup Retention & Post-Restore Disaster Recovery Reconciliation:**
    - Encrypted daily database snapshots and WAL archives retain disaster recovery states for up to 30 days.
    - **Anti-Resurrection Guarantee:** In the event of a disaster recovery database restoration from a historical snapshot, the automated recovery runbook executes a mandatory startup reconciliation hook:
      - The hook reads all entries from the independent Durable Deletion Ledger.
      - Any document records present in the restored snapshot that were marked deleted in the ledger are immediately purged prior to opening the platform to live network traffic.
11. **Physical Storage Retention Boundaries:**
    - Operating system file unlinking marks filesystem allocation table entries and inodes as free; raw physical disk blocks remain until overwritten by subsequent writes.
    - Cloud volume snapshots and OS journal files are governed by host storage provider retention schedules. Real-time physical cryptographic block sanitization (`shred` / DoD 5220.22-M) is not claimed or required on commodity shared SSDs.
