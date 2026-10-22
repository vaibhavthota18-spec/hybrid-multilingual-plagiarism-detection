"""
Replaceable Local Vector Storage and Search Index.
Implements bounded exact cosine search over dense embeddings using safe binary BLOB representation in SQLite.
Preserves abstraction boundaries for future production pgvector migration (ADR-0004).
"""

import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from plagiarism.core.config import get_settings
from plagiarism.storage.local_db import LocalMetadataRepository, get_local_repo

logger = logging.getLogger(__name__)


@dataclass
class PassageVectorRecord:
    passage_id: str
    document_id: str
    sequence_index: int
    start_offset: int
    end_offset: int
    text_content: str
    model_id: str
    model_revision: str
    embedding: np.ndarray  # shape (dim,), float32, normalized
    text_hash: str
    created_at: str


@dataclass
class VectorSearchResult:
    query_index: int
    reference_document_id: str
    reference_passage_id: str
    reference_start_offset: int
    reference_end_offset: int
    reference_text_content: str
    cosine_similarity: float
    rank: int


class VectorIndex(ABC):
    """Abstract interface for dense vector indexing and retrieval."""

    @abstractmethod
    def store_document_embeddings(self, records: list[PassageVectorRecord]) -> None:
        pass

    @abstractmethod
    def get_document_embeddings(self, document_id: str) -> list[PassageVectorRecord]:
        pass

    @abstractmethod
    def search_candidates(
        self,
        query_vectors: np.ndarray,
        candidate_document_ids: list[str],
        top_k: int = 5,
        min_similarity: float = 0.50,
    ) -> list[list[VectorSearchResult]]:
        """
        Returns list of top_k results for each query vector.
        """
        pass

    @abstractmethod
    def delete_document_embeddings(self, document_id: str) -> int:
        pass

    @abstractmethod
    def is_indexed(self, document_id: str, model_id: str, model_revision: str) -> bool:
        pass


class SQLiteVectorRepository(VectorIndex):
    """
    SQLite-backed dense vector repository.
    Embeddings stored as raw IEEE 754 float32 byte buffers (no pickle).
    Uses vectorized NumPy inner product for exact cosine search over candidate pools.
    """

    def __init__(self, repo: LocalMetadataRepository | None = None):
        self.repo = repo or get_local_repo()
        self._lock = threading.RLock()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._lock:
            conn = self.repo._get_connection()
            try:
                cursor = conn.cursor()
                cursor.executescript("""
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

                CREATE INDEX IF NOT EXISTS idx_emb_doc ON passage_embeddings(document_id);
                CREATE INDEX IF NOT EXISTS idx_emb_model ON passage_embeddings(model_id, model_revision);
                """)
                conn.commit()
            finally:
                conn.close()

    def store_document_embeddings(self, records: list[PassageVectorRecord]) -> None:
        if not records:
            return

        with self._lock:
            conn = self.repo._get_connection()
            try:
                cursor = conn.cursor()
                # Delete existing embeddings for this document if re-indexing
                doc_id = records[0].document_id
                cursor.execute("DELETE FROM passage_embeddings WHERE document_id = ?", (doc_id,))

                insert_sql = """
                INSERT INTO passage_embeddings (
                    id, document_id, passage_id, sequence_index,
                    start_offset, end_offset, text_content,
                    model_id, model_revision, embedding, embedding_dim,
                    text_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                rows = []
                for r in records:
                    vec_float32 = r.embedding.astype(np.float32)
                    blob = bytes(vec_float32.tobytes())
                    rows.append((
                        f"{r.document_id}_{r.passage_id}",
                        r.document_id,
                        r.passage_id,
                        r.sequence_index,
                        r.start_offset,
                        r.end_offset,
                        r.text_content,
                        r.model_id,
                        r.model_revision,
                        blob,
                        len(vec_float32),
                        r.text_hash,
                        r.created_at,
                    ))

                cursor.executemany(insert_sql, rows)
                conn.commit()
                logger.info("Persisted %d passage embeddings for document %s", len(rows), doc_id)
            finally:
                conn.close()

    def get_document_embeddings(self, document_id: str) -> list[PassageVectorRecord]:
        with self._lock:
            conn = self.repo._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT passage_id, document_id, sequence_index, start_offset, end_offset,
                           text_content, model_id, model_revision, embedding, embedding_dim,
                           text_hash, created_at
                    FROM passage_embeddings
                    WHERE document_id = ?
                    ORDER BY sequence_index ASC
                    """,
                    (document_id,),
                )
                rows = cursor.fetchall()
                records = []
                for row in rows:
                    vec = np.frombuffer(row["embedding"], dtype=np.float32)
                    records.append(
                        PassageVectorRecord(
                            passage_id=row["passage_id"],
                            document_id=row["document_id"],
                            sequence_index=row["sequence_index"],
                            start_offset=row["start_offset"],
                            end_offset=row["end_offset"],
                            text_content=row["text_content"],
                            model_id=row["model_id"],
                            model_revision=row["model_revision"],
                            embedding=vec,
                            text_hash=row["text_hash"],
                            created_at=row["created_at"],
                        )
                    )
                return records
            finally:
                conn.close()

    def is_indexed(self, document_id: str, model_id: str, model_revision: str) -> bool:
        with self._lock:
            conn = self.repo._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT count(*) as cnt FROM passage_embeddings
                    WHERE document_id = ? AND model_id = ? AND model_revision = ?
                    """,
                    (document_id, model_id, model_revision),
                )
                row = cursor.fetchone()
                return bool(row and row["cnt"] > 0)
            finally:
                conn.close()

    def delete_document_embeddings(self, document_id: str) -> int:
        with self._lock:
            conn = self.repo._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM passage_embeddings WHERE document_id = ?", (document_id,))
                deleted = cursor.rowcount
                conn.commit()
                return deleted
            finally:
                conn.close()

    def search_candidates(
        self,
        query_vectors: np.ndarray,
        candidate_document_ids: list[str],
        top_k: int = 5,
        min_similarity: float = 0.50,
    ) -> list[list[VectorSearchResult]]:
        """
        Computes cosine similarity matrix across query_vectors and candidate passages.
        Query vectors shape: (num_queries, dim).
        Candidate pool shape: (num_candidates, dim).
        """
        if query_vectors.shape[0] == 0 or not candidate_document_ids:
            return [[] for _ in range(query_vectors.shape[0])]

        # Fetch candidate passages
        with self._lock:
            conn = self.repo._get_connection()
            try:
                cursor = conn.cursor()
                placeholders = ",".join("?" for _ in candidate_document_ids)
                query = f"""
                SELECT passage_id, document_id, start_offset, end_offset, text_content, embedding
                FROM passage_embeddings
                WHERE document_id IN ({placeholders})
                ORDER BY document_id, sequence_index ASC
                """
                cursor.execute(query, candidate_document_ids)
                rows = cursor.fetchall()
            finally:
                conn.close()

        if not rows:
            return [[] for _ in range(query_vectors.shape[0])]

        # Construct reference matrix
        ref_passages = []
        vec_list = []
        for r in rows:
            vec = np.frombuffer(r["embedding"], dtype=np.float32)
            vec_list.append(vec)
            ref_passages.append({
                "passage_id": r["passage_id"],
                "document_id": r["document_id"],
                "start_offset": r["start_offset"],
                "end_offset": r["end_offset"],
                "text_content": r["text_content"],
            })

        ref_matrix = np.stack(vec_list, axis=0)  # (N_ref, dim)

        # Dot product: query_vectors (N_q, dim) @ ref_matrix.T (dim, N_ref) -> (N_q, N_ref)
        sim_matrix = np.dot(query_vectors, ref_matrix.T)
        sim_matrix = np.clip(sim_matrix, -1.0, 1.0)

        results_by_query: list[list[VectorSearchResult]] = []

        for q_idx in range(query_vectors.shape[0]):
            scores = sim_matrix[q_idx]  # shape (N_ref,)
            # Sort descending
            sorted_indices = np.argsort(-scores)
            q_results: list[VectorSearchResult] = []

            rank = 1
            for ref_idx in sorted_indices:
                score = float(scores[ref_idx])
                if score < min_similarity:
                    break
                p_meta = ref_passages[ref_idx]
                q_results.append(
                    VectorSearchResult(
                        query_index=q_idx,
                        reference_document_id=p_meta["document_id"],
                        reference_passage_id=p_meta["passage_id"],
                        reference_start_offset=p_meta["start_offset"],
                        reference_end_offset=p_meta["end_offset"],
                        reference_text_content=p_meta["text_content"],
                        cosine_similarity=score,
                        rank=rank,
                    )
                )
                rank += 1
                if rank > top_k:
                    break

            results_by_query.append(q_results)

        return results_by_query


class PgVectorRepository(VectorIndex):
    """
    PostgreSQL + pgvector dense vector repository.
    Stores 384-dimensional dense vectors using pgvector extension and executes
    index-accelerated cosine distance search using the '<=>' operator.
    """

    def __init__(self):
        self.settings = get_settings()
        self._executor = None
        self._ensure_executor()

    def _ensure_executor(self):
        import concurrent.futures
        if self._executor is None:
            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def _run_async(self, coro):
        import asyncio
        self._ensure_executor()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return self._executor.submit(asyncio.run, coro).result()
        return asyncio.run(coro)

    def _get_postgres_dsn(self) -> str:
        dsn = self.settings.DATABASE_URL
        if dsn.startswith("postgresql+asyncpg://"):
            return dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
        return dsn

    async def _get_conn(self):
        import asyncpg
        import pgvector.asyncpg

        dsn = self._get_postgres_dsn()
        conn = await asyncpg.connect(dsn, timeout=10)
        await pgvector.asyncpg.register_vector(conn)
        return conn

    def store_document_embeddings(self, records: list[PassageVectorRecord]) -> None:
        if not records:
            return

        async def _store():
            conn = await self._get_conn()
            try:
                doc_id = records[0].document_id
                async with conn.transaction():
                    await conn.execute("DELETE FROM passage_embeddings WHERE document_id = $1", doc_id)
                    insert_sql = """
                    INSERT INTO passage_embeddings (
                        passage_id, document_id, sequence_index, start_offset,
                        end_offset, text_content, model_id, model_revision,
                        embedding, text_hash, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (passage_id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        text_content = EXCLUDED.text_content,
                        text_hash = EXCLUDED.text_hash,
                        created_at = EXCLUDED.created_at;
                    """
                    data = [
                        (
                            r.passage_id,
                            r.document_id,
                            r.sequence_index,
                            r.start_offset,
                            r.end_offset,
                            r.text_content,
                            r.model_id,
                            r.model_revision,
                            np.asarray(r.embedding, dtype=np.float32),
                            r.text_hash,
                            r.created_at,
                        )
                        for r in records
                    ]
                    await conn.executemany(insert_sql, data)
            finally:
                await conn.close()

        self._run_async(_store())

    def get_document_embeddings(self, document_id: str) -> list[PassageVectorRecord]:
        async def _fetch():
            conn = await self._get_conn()
            try:
                rows = await conn.fetch(
                    """
                    SELECT passage_id, document_id, sequence_index, start_offset,
                           end_offset, text_content, model_id, model_revision,
                           embedding, text_hash, created_at
                    FROM passage_embeddings
                    WHERE document_id = $1
                    ORDER BY sequence_index ASC
                    """,
                    document_id,
                )
                records = []
                for row in rows:
                    raw_emb = row["embedding"]
                    if hasattr(raw_emb, "to_numpy"):
                        emb = raw_emb.to_numpy()
                    else:
                        emb = np.array(raw_emb, dtype=np.float32)
                    records.append(
                        PassageVectorRecord(
                            passage_id=row["passage_id"],
                            document_id=row["document_id"],
                            sequence_index=row["sequence_index"],
                            start_offset=row["start_offset"],
                            end_offset=row["end_offset"],
                            text_content=row["text_content"],
                            model_id=row["model_id"],
                            model_revision=row["model_revision"],
                            embedding=emb,
                            text_hash=row["text_hash"],
                            created_at=row["created_at"],
                        )
                    )
                return records
            finally:
                await conn.close()

        return self._run_async(_fetch())

    def search_candidates(
        self,
        query_vectors: np.ndarray,
        candidate_document_ids: list[str],
        top_k: int = 5,
        min_similarity: float = 0.50,
    ) -> list[list[VectorSearchResult]]:
        if not candidate_document_ids or query_vectors.size == 0:
            return [[] for _ in range(len(query_vectors))]

        async def _search():
            conn = await self._get_conn()
            try:
                results_by_query: list[list[VectorSearchResult]] = []
                search_sql = """
                SELECT passage_id, document_id, start_offset, end_offset,
                       text_content, 1 - (embedding <=> $1) AS cosine_similarity
                FROM passage_embeddings
                WHERE document_id = ANY($2::text[])
                  AND (1 - (embedding <=> $1)) >= $3
                ORDER BY embedding <=> $1 ASC
                LIMIT $4;
                """
                for q_idx, q_vec in enumerate(query_vectors):
                    normalized_vec = np.asarray(q_vec, dtype=np.float32)
                    rows = await conn.fetch(
                        search_sql,
                        normalized_vec,
                        candidate_document_ids,
                        min_similarity,
                        top_k,
                    )
                    q_res = [
                        VectorSearchResult(
                            query_index=q_idx,
                            reference_document_id=r["document_id"],
                            reference_passage_id=r["passage_id"],
                            reference_start_offset=r["start_offset"],
                            reference_end_offset=r["end_offset"],
                            reference_text_content=r["text_content"],
                            cosine_similarity=float(r["cosine_similarity"]),
                            rank=idx + 1,
                        )
                        for idx, r in enumerate(rows)
                    ]
                    results_by_query.append(q_res)
                return results_by_query
            finally:
                await conn.close()

        return self._run_async(_search())

    def delete_document_embeddings(self, document_id: str) -> int:
        async def _delete():
            conn = await self._get_conn()
            try:
                result = await conn.execute(
                    "DELETE FROM passage_embeddings WHERE document_id = $1",
                    document_id,
                )
                return int(result.split(" ")[-1])
            finally:
                await conn.close()

        return self._run_async(_delete())

    def is_indexed(self, document_id: str, model_id: str, model_revision: str) -> bool:
        async def _check():
            conn = await self._get_conn()
            try:
                count = await conn.fetchval(
                    """
                    SELECT count(*) FROM passage_embeddings
                    WHERE document_id = $1 AND model_id = $2 AND model_revision = $3
                    """,
                    document_id,
                    model_id,
                    model_revision,
                )
                return (count or 0) > 0
            finally:
                await conn.close()

        return self._run_async(_check())


_vector_repo_instance: VectorIndex | None = None


def get_vector_repository() -> VectorIndex:
    global _vector_repo_instance
    if _vector_repo_instance is None:
        settings = get_settings()
        if getattr(settings, "APP_RUNTIME_MODE", "local") == "production":
            try:
                _vector_repo_instance = PgVectorRepository()
            except Exception as e:
                logger.warning(
                    f"Could not initialize PgVectorRepository ({e}); falling back to SQLiteVectorRepository"
                )
                _vector_repo_instance = SQLiteVectorRepository()
        else:
            _vector_repo_instance = SQLiteVectorRepository()
    return _vector_repo_instance
