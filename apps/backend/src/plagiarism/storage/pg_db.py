"""
Production PostgreSQL Metadata Repository Adapter
Implements the exact same 28-method interface as LocalMetadataRepository for seamless drop-in
switching when running in containerized and cloud environments.
"""

import asyncio
import concurrent.futures
from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from plagiarism.core.config import get_settings

logger = logging.getLogger("plagiarism.storage.pg_db")


class PostgresMetadataRepository:
    """
    PostgreSQL persistence repository for documents, passages, collections,
    fingerprints, analyses, and audit logs.
    """

    def __init__(self):
        self.settings = get_settings()
        self._executor = None
        self._ensure_executor()

    def _ensure_executor(self):
        if self._executor is None:
            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def _run_async(self, coro):
        self._ensure_executor()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return self._executor.submit(asyncio.run, coro).result()
        return asyncio.run(coro)

    def _get_dsn(self) -> str:
        dsn = self.settings.DATABASE_URL
        if dsn.startswith("postgresql+asyncpg://"):
            return dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
        return dsn

    async def _get_conn(self):
        import asyncpg
        return await asyncpg.connect(self._get_dsn(), timeout=10)

    # 1. Document Management
    def insert_document(
        self,
        document_id: str,
        owner_user_id: str,
        filename: str,
        mime_type: str,
        sha256_hash: str,
        storage_path: str,
        file_size_bytes: int,
        status: str = "queued",
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()

        async def _insert():
            conn = await self._get_conn()
            try:
                # Ensure owner user exists in users table to satisfy foreign key
                await conn.execute(
                    """
                    INSERT INTO users (id, email, hashed_password, role, full_name)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    owner_user_id,
                    f"user_{owner_user_id[:8]}@example.com",
                    "dev_insecure_hash",
                    "REVIEWER",
                    "System User"
                )

                await conn.execute(
                    """
                    INSERT INTO documents (
                        id, owner_user_id, filename, mime_type, sha256_hash,
                        storage_path, file_size_bytes, status, page_count,
                        char_count, raw_text, detected_language, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 1, 0, '', 'en', NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        filename = EXCLUDED.filename,
                        storage_path = EXCLUDED.storage_path,
                        file_size_bytes = EXCLUDED.file_size_bytes,
                        status = EXCLUDED.status;
                    """,
                    document_id, owner_user_id, filename, mime_type, sha256_hash,
                    storage_path, file_size_bytes, status
                )

                if title:
                    await conn.execute(
                        """
                        INSERT INTO document_sources (id, document_id, title, author, license, provenance_uri)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (document_id) DO UPDATE SET title = EXCLUDED.title;
                        """,
                        document_id, document_id, title, "Unknown", "CC-BY-4.0", ""
                    )
            finally:
                await conn.close()

        self._run_async(_insert())
        return {
            "document_id": document_id,
            "id": document_id,
            "owner_user_id": owner_user_id,
            "filename": filename,
            "mime_type": mime_type,
            "sha256_hash": sha256_hash,
            "storage_path": storage_path,
            "file_size_bytes": file_size_bytes,
            "status": status,
            "page_count": 1,
            "char_count": 0,
            "word_count": 0,
            "raw_text": "",
            "detected_language": "en",
            "created_at": now_iso,
            "title": title or filename
        }

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        async def _get():
            conn = await self._get_conn()
            try:
                row = await conn.fetchrow(
                    """
                    SELECT d.id, d.owner_user_id, d.filename, d.mime_type, d.sha256_hash,
                           d.storage_path, d.file_size_bytes, d.status, d.page_count,
                           d.char_count, d.raw_text, d.detected_language, d.created_at,
                           s.title, s.author
                    FROM documents d
                    LEFT JOIN document_sources s ON d.id = s.document_id
                    WHERE d.id = $1
                    """,
                    document_id
                )
                if not row:
                    return None
                doc = dict(row)
                doc["document_id"] = str(doc["id"])
                doc["id"] = str(doc["id"])
                doc["owner_user_id"] = str(doc["owner_user_id"])
                doc["created_at"] = doc["created_at"].isoformat() if doc["created_at"] else ""
                doc["word_count"] = len(doc.get("raw_text", "").split())
                return doc
            finally:
                await conn.close()

        return self._run_async(_get())

    def update_document_extraction(
        self,
        document_id: str,
        status: str,
        page_count: int,
        char_count: int,
        word_count: int,
        raw_text: str,
        detected_language: str,
        warnings: str = ""
    ) -> None:
        async def _update():
            conn = await self._get_conn()
            try:
                await conn.execute(
                    """
                    UPDATE documents
                    SET status = $2,
                        page_count = $3,
                        char_count = $4,
                        raw_text = $5,
                        detected_language = $6
                    WHERE id = $1;
                    """,
                    document_id, status, page_count, char_count, raw_text, detected_language
                )
            finally:
                await conn.close()

        self._run_async(_update())

    def list_documents(
        self,
        owner_user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        async def _list():
            conn = await self._get_conn()
            try:
                if owner_user_id:
                    count = await conn.fetchval(
                        "SELECT count(*) FROM documents WHERE owner_user_id = $1", owner_user_id
                    )
                    rows = await conn.fetch(
                        """
                        SELECT d.id, d.owner_user_id, d.filename, d.mime_type, d.sha256_hash,
                               d.storage_path, d.file_size_bytes, d.status, d.page_count,
                               d.char_count, d.raw_text, d.detected_language, d.created_at,
                               s.title, s.author
                        FROM documents d
                        LEFT JOIN document_sources s ON d.id = s.document_id
                        WHERE d.owner_user_id = $1
                        ORDER BY d.created_at DESC
                        LIMIT $2 OFFSET $3
                        """,
                        owner_user_id, limit, offset
                    )
                else:
                    count = await conn.fetchval("SELECT count(*) FROM documents")
                    rows = await conn.fetch(
                        """
                        SELECT d.id, d.owner_user_id, d.filename, d.mime_type, d.sha256_hash,
                               d.storage_path, d.file_size_bytes, d.status, d.page_count,
                               d.char_count, d.raw_text, d.detected_language, d.created_at,
                               s.title, s.author
                        FROM documents d
                        LEFT JOIN document_sources s ON d.id = s.document_id
                        ORDER BY d.created_at DESC
                        LIMIT $1 OFFSET $2
                        """,
                        limit, offset
                    )

                docs = []
                for r in rows:
                    item = dict(r)
                    item["document_id"] = str(item["id"])
                    item["id"] = str(item["id"])
                    item["owner_user_id"] = str(item["owner_user_id"])
                    item["created_at"] = item["created_at"].isoformat() if item["created_at"] else ""
                    item["word_count"] = len(item.get("raw_text", "").split())
                    docs.append(item)
                return docs, int(count or 0)
            finally:
                await conn.close()

        return self._run_async(_list())

    def delete_document(self, document_id: str) -> bool:
        async def _delete():
            conn = await self._get_conn()
            try:
                res = await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
                return " 0" not in res
            finally:
                await conn.close()

        return self._run_async(_delete())

    # 2. Passages
    def insert_passages(self, passages: List[Dict[str, Any]]) -> None:
        if not passages:
            return

        async def _insert():
            conn = await self._get_conn()
            try:
                insert_sql = """
                INSERT INTO passages (
                    id, document_id, sequence_index, start_offset, end_offset,
                    text_content, token_count, page_number, language
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE SET
                    text_content = EXCLUDED.text_content,
                    token_count = EXCLUDED.token_count;
                """
                data = [
                    (
                        p.get("id") or p.get("passage_id"),
                        p["document_id"],
                        p["sequence_index"],
                        p["start_offset"],
                        p["end_offset"],
                        p["text_content"],
                        p.get("token_count", 0),
                        p.get("page_number", 1),
                        p.get("language", "en")
                    )
                    for p in passages
                ]
                await conn.executemany(insert_sql, data)
            finally:
                await conn.close()

        self._run_async(_insert())

    def get_passages(self, document_id: str) -> List[Dict[str, Any]]:
        async def _get():
            conn = await self._get_conn()
            try:
                rows = await conn.fetch(
                    """
                    SELECT id, document_id, sequence_index, start_offset, end_offset,
                           text_content, token_count, page_number, language
                    FROM passages
                    WHERE document_id = $1
                    ORDER BY sequence_index ASC
                    """,
                    document_id
                )
                return [dict(r) for r in rows]
            finally:
                await conn.close()

        return self._run_async(_get())

    # 3. Fingerprints
    def save_fingerprints(
        self,
        document_id: str,
        fingerprints: List[Any],
        algorithm_version: str = "winnowing-k25-w16-v1"
    ) -> int:
        if not fingerprints:
            return 0

        async def _save():
            conn = await self._get_conn()
            try:
                insert_sql = """
                INSERT INTO fingerprints (hash_value, passage_id, document_id, start_offset, end_offset)
                VALUES ($1, $2, $3, $4, $5)
                """
                data = []
                for fp in fingerprints:
                    h = getattr(fp, "hash_val", None) or getattr(fp, "hash_value", 0)
                    pid = getattr(fp, "passage_id", document_id)
                    s = getattr(fp, "char_start", 0) or getattr(fp, "start_offset", 0)
                    e = getattr(fp, "char_end", 0) or getattr(fp, "end_offset", 0)
                    data.append((int(h), pid, document_id, int(s), int(e)))

                await conn.executemany(insert_sql, data)
                return len(data)
            finally:
                await conn.close()

        return self._run_async(_save())

    def get_fingerprints(self, document_id: str) -> List[Dict[str, Any]]:
        async def _get():
            conn = await self._get_conn()
            try:
                rows = await conn.fetch(
                    """
                    SELECT id, hash_value as hash_val, document_id, start_offset as char_start,
                           end_offset as char_end, passage_id
                    FROM fingerprints
                    WHERE document_id = $1
                    """,
                    document_id
                )
                return [dict(r) for r in rows]
            finally:
                await conn.close()

        return self._run_async(_get())

    def find_shared_fingerprints(
        self, submission_id: str, candidate_ids: List[str]
    ) -> List[Dict[str, Any]]:
        if not candidate_ids:
            return []

        async def _find():
            conn = await self._get_conn()
            try:
                rows = await conn.fetch(
                    """
                    SELECT s.hash_value as hash_val, s.start_offset as sub_start, s.end_offset as sub_end,
                           r.document_id as ref_doc_id, r.start_offset as ref_start, r.end_offset as ref_end
                    FROM fingerprints s
                    JOIN fingerprints r ON s.hash_value = r.hash_value
                    WHERE s.document_id = $1
                      AND r.document_id = ANY($2::text[])
                    """,
                    submission_id, candidate_ids
                )
                return [dict(r) for r in rows]
            finally:
                await conn.close()

        return self._run_async(_find())

    # 4. Collections
    def create_collection(
        self,
        collection_id: str,
        name: str,
        owner_user_id: str,
        description: Optional[str] = None,
        is_public_within_tenant: bool = False
    ) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()

        async def _create():
            conn = await self._get_conn()
            try:
                # Ensure owner user exists
                await conn.execute(
                    """
                    INSERT INTO users (id, email, hashed_password, role, full_name)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    owner_user_id,
                    f"user_{owner_user_id[:8]}@example.com",
                    "dev_insecure_hash",
                    "REVIEWER",
                    "System User"
                )

                await conn.execute(
                    """
                    INSERT INTO collections (id, name, description, owner_user_id, is_public_within_tenant, document_count, created_at)
                    VALUES ($1, $2, $3, $4, $5, 0, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description;
                    """,
                    collection_id, name, description or "", owner_user_id, is_public_within_tenant
                )
            finally:
                await conn.close()

        self._run_async(_create())
        return {
            "id": collection_id,
            "name": name,
            "description": description or "",
            "owner_user_id": owner_user_id,
            "is_public_within_tenant": is_public_within_tenant,
            "document_count": 0,
            "created_at": now_iso
        }

    def get_collection(self, collection_id: str) -> Optional[Dict[str, Any]]:
        async def _get():
            conn = await self._get_conn()
            try:
                row = await conn.fetchrow(
                    "SELECT id, name, description, owner_user_id, is_public_within_tenant, document_count, created_at FROM collections WHERE id = $1",
                    collection_id
                )
                if not row:
                    return None
                c = dict(row)
                c["id"] = str(c["id"])
                c["created_at"] = c["created_at"].isoformat() if c["created_at"] else ""
                return c
            finally:
                await conn.close()

        return self._run_async(_get())

    def list_collections(
        self, owner_user_id: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        async def _list():
            conn = await self._get_conn()
            try:
                if owner_user_id:
                    count = await conn.fetchval(
                        "SELECT count(*) FROM collections WHERE owner_user_id = $1", owner_user_id
                    )
                    rows = await conn.fetch(
                        "SELECT id, name, description, owner_user_id, is_public_within_tenant, document_count, created_at FROM collections WHERE owner_user_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                        owner_user_id, limit, offset
                    )
                else:
                    count = await conn.fetchval("SELECT count(*) FROM collections")
                    rows = await conn.fetch(
                        "SELECT id, name, description, owner_user_id, is_public_within_tenant, document_count, created_at FROM collections ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                        limit, offset
                    )
                cols = []
                for r in rows:
                    c = dict(r)
                    c["id"] = str(c["id"])
                    c["created_at"] = c["created_at"].isoformat() if c["created_at"] else ""
                    cols.append(c)
                return cols, int(count or 0)
            finally:
                await conn.close()

        return self._run_async(_list())

    def add_document_to_collection(self, collection_id: str, document_id: str) -> bool:
        async def _add():
            conn = await self._get_conn()
            try:
                await conn.execute(
                    """
                    INSERT INTO collection_documents (collection_id, document_id, indexed_at, status)
                    VALUES ($1, $2, NOW(), 'INDEXED')
                    ON CONFLICT (collection_id, document_id) DO NOTHING;
                    """,
                    collection_id, document_id
                )
                await conn.execute(
                    """
                    UPDATE collections
                    SET document_count = (
                        SELECT count(*) FROM collection_documents WHERE collection_id = $1
                    )
                    WHERE id = $1;
                    """,
                    collection_id
                )
                return True
            finally:
                await conn.close()

        return self._run_async(_add())

    def remove_document_from_collection(self, collection_id: str, document_id: str) -> bool:
        async def _remove():
            conn = await self._get_conn()
            try:
                await conn.execute(
                    "DELETE FROM collection_documents WHERE collection_id = $1 AND document_id = $2",
                    collection_id, document_id
                )
                await conn.execute(
                    """
                    UPDATE collections
                    SET document_count = (
                        SELECT count(*) FROM collection_documents WHERE collection_id = $1
                    )
                    WHERE id = $1;
                    """,
                    collection_id
                )
                return True
            finally:
                await conn.close()

        return self._run_async(_remove())

    def list_collection_documents(self, collection_id: str) -> List[Dict[str, Any]]:
        async def _list():
            conn = await self._get_conn()
            try:
                rows = await conn.fetch(
                    """
                    SELECT d.id, d.filename, d.mime_type, d.file_size_bytes, d.status,
                           d.created_at, cd.indexed_at
                    FROM collection_documents cd
                    JOIN documents d ON cd.document_id = d.id
                    WHERE cd.collection_id = $1
                    ORDER BY cd.indexed_at DESC
                    """,
                    collection_id
                )
                res = []
                for r in rows:
                    item = dict(r)
                    item["id"] = str(item["id"])
                    item["created_at"] = item["created_at"].isoformat() if item["created_at"] else ""
                    item["indexed_at"] = item["indexed_at"].isoformat() if item["indexed_at"] else ""
                    res.append(item)
                return res
            finally:
                await conn.close()

        return self._run_async(_list())

    # 5. Analyses
    def create_analysis(
        self,
        analysis_id: str,
        owner_user_id: str,
        submission_document_id: str,
        mode: str,
        reference_document_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        candidate_metadata: Optional[Dict[str, Any]] = None,
        detection_mode: str = "hybrid"
    ) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()

        async def _create():
            conn = await self._get_conn()
            try:
                # Ensure owner user exists
                await conn.execute(
                    """
                    INSERT INTO users (id, email, hashed_password, role, full_name)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    owner_user_id,
                    f"user_{owner_user_id[:8]}@example.com",
                    "dev_insecure_hash",
                    "REVIEWER",
                    "System User"
                )

                await conn.execute(
                    """
                    INSERT INTO analyses (
                        id, user_id, submission_document_id, mode, target_collection_id,
                        overall_lexical_coverage_percent, overall_semantic_coverage_percent,
                        net_adjusted_score_percent, status, created_at
                    ) VALUES ($1, $2, $3, $4, $5, 0.0, 0.0, 0.0, 'queued', NOW())
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    analysis_id, owner_user_id, submission_document_id, mode, collection_id
                )

                await conn.execute(
                    """
                    INSERT INTO analysis_jobs (
                        id, analysis_id, status, progress_percent, current_step, started_at
                    ) VALUES ($1, $2, 'queued', 0, 'enqueued', NOW())
                    ON CONFLICT (analysis_id) DO UPDATE SET status = 'queued', progress_percent = 0;
                    """,
                    analysis_id, analysis_id
                )
            finally:
                await conn.close()

        self._run_async(_create())
        return {
            "id": analysis_id,
            "analysis_id": analysis_id,
            "owner_user_id": owner_user_id,
            "submission_document_id": submission_document_id,
            "mode": mode,
            "reference_document_id": reference_document_id,
            "collection_id": collection_id,
            "detection_mode": detection_mode,
            "status": "queued",
            "progress_percent": 0,
            "current_step": "enqueued",
            "created_at": now_iso
        }

    def update_analysis_status(
        self,
        analysis_id: str,
        status: str,
        progress_percent: int,
        current_step: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[str] = None
    ) -> None:
        async def _update():
            conn = await self._get_conn()
            try:
                await conn.execute(
                    """
                    UPDATE analyses
                    SET status = $2
                    WHERE id = $1;
                    """,
                    analysis_id, status
                )
                await conn.execute(
                    """
                    UPDATE analysis_jobs
                    SET status = $2,
                        progress_percent = $3,
                        current_step = COALESCE($4, current_step),
                        error_code = $5,
                        error_message = $6,
                        completed_at = CASE WHEN $2 IN ('completed', 'failed') THEN NOW() ELSE NULL END
                    WHERE analysis_id = $1;
                    """,
                    analysis_id, status, progress_percent, current_step, error_code, error_message
                )
            finally:
                await conn.close()

        self._run_async(_update())

    def update_analysis_review_summary(
        self,
        analysis_id: str,
        reviewer_adjusted_coverage_percent: float,
        reviewed_findings_count: int,
        notes: Optional[str] = None
    ) -> None:
        async def _update():
            conn = await self._get_conn()
            try:
                await conn.execute(
                    """
                    UPDATE analyses
                    SET net_adjusted_score_percent = $2
                    WHERE id = $1;
                    """,
                    analysis_id, reviewer_adjusted_coverage_percent
                )
            finally:
                await conn.close()

        self._run_async(_update())

    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        async def _get():
            conn = await self._get_conn()
            try:
                row = await conn.fetchrow(
                    """
                    SELECT a.id, a.user_id as owner_user_id, a.submission_document_id, a.mode,
                           a.target_collection_id as collection_id, a.status,
                           a.overall_lexical_coverage_percent, a.overall_semantic_coverage_percent,
                           a.net_adjusted_score_percent, a.created_at, a.completed_at,
                           j.progress_percent, j.current_step, j.error_code, j.error_message,
                           d.filename as submission_filename
                    FROM analyses a
                    LEFT JOIN analysis_jobs j ON a.id = j.analysis_id
                    LEFT JOIN documents d ON a.submission_document_id = d.id
                    WHERE a.id = $1
                    """,
                    analysis_id
                )
                if not row:
                    return None
                rec = dict(row)
                rec["id"] = str(rec["id"])
                rec["analysis_id"] = str(rec["id"])
                rec["submission_document_id"] = str(rec["submission_document_id"])
                rec["overall_lexical_coverage_percent"] = float(rec["overall_lexical_coverage_percent"] or 0)
                rec["overall_semantic_coverage_percent"] = float(rec["overall_semantic_coverage_percent"] or 0)
                rec["net_adjusted_score_percent"] = float(rec["net_adjusted_score_percent"] or 0)
                rec["reviewer_adjusted_coverage_percent"] = rec["net_adjusted_score_percent"]
                rec["created_at"] = rec["created_at"].isoformat() if rec["created_at"] else ""
                rec["completed_at"] = rec["completed_at"].isoformat() if rec["completed_at"] else None
                return rec
            finally:
                await conn.close()

        return self._run_async(_get())

    def list_analyses(
        self, owner_user_id: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        async def _list():
            conn = await self._get_conn()
            try:
                if owner_user_id:
                    count = await conn.fetchval(
                        "SELECT count(*) FROM analyses WHERE user_id = $1", owner_user_id
                    )
                    rows = await conn.fetch(
                        """
                        SELECT a.id, a.user_id as owner_user_id, a.submission_document_id, a.mode,
                               a.target_collection_id as collection_id, a.status,
                               a.overall_lexical_coverage_percent, a.overall_semantic_coverage_percent,
                               a.net_adjusted_score_percent, a.created_at, a.completed_at,
                               j.progress_percent, j.current_step, j.error_code, j.error_message,
                               d.filename as submission_filename
                        FROM analyses a
                        LEFT JOIN analysis_jobs j ON a.id = j.analysis_id
                        LEFT JOIN documents d ON a.submission_document_id = d.id
                        WHERE a.user_id = $1
                        ORDER BY a.created_at DESC
                        LIMIT $2 OFFSET $3
                        """,
                        owner_user_id, limit, offset
                    )
                else:
                    count = await conn.fetchval("SELECT count(*) FROM analyses")
                    rows = await conn.fetch(
                        """
                        SELECT a.id, a.user_id as owner_user_id, a.submission_document_id, a.mode,
                               a.target_collection_id as collection_id, a.status,
                               a.overall_lexical_coverage_percent, a.overall_semantic_coverage_percent,
                               a.net_adjusted_score_percent, a.created_at, a.completed_at,
                               j.progress_percent, j.current_step, j.error_code, j.error_message,
                               d.filename as submission_filename
                        FROM analyses a
                        LEFT JOIN analysis_jobs j ON a.id = j.analysis_id
                        LEFT JOIN documents d ON a.submission_document_id = d.id
                        ORDER BY a.created_at DESC
                        LIMIT $1 OFFSET $2
                        """,
                        limit, offset
                    )

                res = []
                for r in rows:
                    rec = dict(r)
                    rec["id"] = str(rec["id"])
                    rec["analysis_id"] = str(rec["id"])
                    rec["submission_document_id"] = str(rec["submission_document_id"])
                    rec["overall_lexical_coverage_percent"] = float(rec["overall_lexical_coverage_percent"] or 0)
                    rec["overall_semantic_coverage_percent"] = float(rec["overall_semantic_coverage_percent"] or 0)
                    rec["net_adjusted_score_percent"] = float(rec["net_adjusted_score_percent"] or 0)
                    rec["reviewer_adjusted_coverage_percent"] = rec["net_adjusted_score_percent"]
                    rec["created_at"] = rec["created_at"].isoformat() if rec["created_at"] else ""
                    rec["completed_at"] = rec["completed_at"].isoformat() if rec["completed_at"] else None
                    res.append(rec)
                return res, int(count or 0)
            finally:
                await conn.close()

        return self._run_async(_list())

    def delete_analysis(self, analysis_id: str) -> bool:
        async def _delete():
            conn = await self._get_conn()
            try:
                res = await conn.execute("DELETE FROM analyses WHERE id = $1", analysis_id)
                return " 0" not in res
            finally:
                await conn.close()

        return self._run_async(_delete())

    def save_analysis_results(
        self,
        analysis_id: str,
        overall_lexical_cov: float,
        findings: List[Any],
        sources: List[Any],
        candidate_metadata: Optional[Dict[str, Any]] = None,
        overall_semantic_cov: float = 0.0,
        net_adjusted_score: Optional[float] = None,
        hybrid_evidence_cov: Optional[float] = None
    ) -> None:
        async def _save():
            conn = await self._get_conn()
            try:
                final_score = net_adjusted_score if net_adjusted_score is not None else max(overall_lexical_cov, overall_semantic_cov)
                await conn.execute(
                    """
                    UPDATE analyses
                    SET overall_lexical_coverage_percent = $2,
                        overall_semantic_coverage_percent = $3,
                        net_adjusted_score_percent = $4,
                        status = 'completed',
                        completed_at = NOW()
                    WHERE id = $1;
                    """,
                    analysis_id, overall_lexical_cov, overall_semantic_cov, final_score
                )
                await conn.execute(
                    """
                    UPDATE analysis_jobs
                    SET status = 'completed', progress_percent = 100, current_step = 'completed', completed_at = NOW()
                    WHERE analysis_id = $1;
                    """,
                    analysis_id
                )

                # Insert findings
                if findings:
                    await conn.execute("DELETE FROM findings WHERE analysis_id = $1", analysis_id)
                    insert_finding_sql = """
                    INSERT INTO findings (
                        id, analysis_id, submission_document_id, reference_document_id,
                        category, confidence, submission_start_offset, submission_end_offset,
                        submission_excerpt, reference_start_offset, reference_end_offset,
                        reference_excerpt, reference_page_number, lexical_similarity,
                        semantic_similarity, is_quoted, is_in_bibliography, is_excluded
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                    """
                    finding_data = []
                    for f in findings:
                        fid = getattr(f, "finding_id", None) or f.get("finding_id") or f.get("id")
                        sub_doc_id = getattr(f, "submission_document_id", None) or f.get("submission_document_id")
                        ref_doc_id = getattr(f, "reference_document_id", None) or f.get("reference_document_id")
                        cat = getattr(f, "match_type", None) or f.get("match_type", "exact")
                        conf = getattr(f, "confidence", None) or f.get("confidence", "high")
                        s_start = getattr(f, "submission_start_offset", None) or f.get("submission_start_offset", 0)
                        s_end = getattr(f, "submission_end_offset", None) or f.get("submission_end_offset", 0)
                        s_exc = getattr(f, "submission_text", None) or f.get("submission_text", "")
                        r_start = getattr(f, "reference_start_offset", None) or f.get("reference_start_offset", 0)
                        r_end = getattr(f, "reference_end_offset", None) or f.get("reference_end_offset", 0)
                        r_exc = getattr(f, "reference_text", None) or f.get("reference_text", "")
                        r_page = getattr(f, "reference_page_number", 1) or f.get("reference_page_number", 1)
                        lex_sim = getattr(f, "lexical_similarity", 0.0) or f.get("lexical_similarity", 0.0)
                        sem_sim = getattr(f, "semantic_similarity", 0.0) or f.get("semantic_similarity", 0.0)
                        is_q = bool(getattr(f, "is_quoted", False) or f.get("is_quoted", False))
                        is_b = bool(getattr(f, "is_in_bibliography", False) or f.get("is_in_bibliography", False))
                        is_ex = bool(getattr(f, "is_excluded", False) or f.get("is_excluded", False))

                        finding_data.append((
                            fid, analysis_id, sub_doc_id, ref_doc_id,
                            cat, conf, s_start, s_end, s_exc,
                            r_start, r_end, r_exc, r_page,
                            lex_sim, sem_sim, is_q, is_b, is_ex
                        ))
                    await conn.executemany(insert_finding_sql, finding_data)
            finally:
                await conn.close()

        self._run_async(_save())

    def get_analysis_findings(self, analysis_id: str) -> List[Dict[str, Any]]:
        async def _get():
            conn = await self._get_conn()
            try:
                rows = await conn.fetch(
                    """
                    SELECT f.id as finding_id, f.id, f.analysis_id, f.submission_document_id,
                           f.reference_document_id, f.category as match_type, f.confidence,
                           f.submission_start_offset, f.submission_end_offset,
                           f.submission_excerpt as submission_text,
                           f.reference_start_offset, f.reference_end_offset,
                           f.reference_excerpt as reference_text,
                           f.reference_page_number, f.lexical_similarity, f.semantic_similarity,
                           f.is_quoted, f.is_in_bibliography, f.is_excluded,
                           r.review_label as review_decision, r.notes as reviewer_notes,
                           d.filename as reference_filename
                    FROM findings f
                    LEFT JOIN reviews r ON f.id = r.finding_id
                    LEFT JOIN documents d ON f.reference_document_id = d.id
                    WHERE f.analysis_id = $1
                    ORDER BY f.submission_start_offset ASC
                    """,
                    analysis_id
                )
                res = []
                for r in rows:
                    item = dict(r)
                    item["finding_id"] = str(item["finding_id"])
                    item["id"] = str(item["id"])
                    item["submission_document_id"] = str(item["submission_document_id"])
                    item["reference_document_id"] = str(item["reference_document_id"])
                    item["lexical_similarity"] = float(item["lexical_similarity"] or 0)
                    item["semantic_similarity"] = float(item["semantic_similarity"] or 0)
                    res.append(item)
                return res
            finally:
                await conn.close()

        return self._run_async(_get())

    def get_analysis_sources(self, analysis_id: str) -> List[Dict[str, Any]]:
        async def _get():
            conn = await self._get_conn()
            try:
                rows = await conn.fetch(
                    """
                    SELECT DISTINCT d.id as document_id, d.filename, s.title, s.author
                    FROM findings f
                    JOIN documents d ON f.reference_document_id = d.id
                    LEFT JOIN document_sources s ON d.id = s.document_id
                    WHERE f.analysis_id = $1
                    """,
                    analysis_id
                )
                res = []
                for r in rows:
                    item = dict(r)
                    item["document_id"] = str(item["document_id"])
                    res.append(item)
                return res
            finally:
                await conn.close()

        return self._run_async(_get())

    def get_finding(self, finding_id: str) -> Optional[Dict[str, Any]]:
        async def _get():
            conn = await self._get_conn()
            try:
                row = await conn.fetchrow(
                    """
                    SELECT f.id as finding_id, f.id, f.analysis_id, f.submission_document_id,
                           f.reference_document_id, f.category as match_type, f.confidence,
                           f.submission_start_offset, f.submission_end_offset,
                           f.submission_excerpt as submission_text,
                           f.reference_start_offset, f.reference_end_offset,
                           f.reference_excerpt as reference_text,
                           f.reference_page_number, f.lexical_similarity, f.semantic_similarity,
                           f.is_quoted, f.is_in_bibliography, f.is_excluded,
                           r.review_label as review_decision, r.notes as reviewer_notes
                    FROM findings f
                    LEFT JOIN reviews r ON f.id = r.finding_id
                    WHERE f.id = $1
                    """,
                    finding_id
                )
                if not row:
                    return None
                item = dict(row)
                item["finding_id"] = str(item["finding_id"])
                item["id"] = str(item["id"])
                return item
            finally:
                await conn.close()

        return self._run_async(_get())

    def update_finding_review(
        self, finding_id: str, decision: str, notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        async def _update():
            conn = await self._get_conn()
            try:
                # Upsert into reviews table
                await conn.execute(
                    """
                    INSERT INTO reviews (id, finding_id, reviewer_user_id, review_label, notes, created_at)
                    VALUES (
                        $1, $1,
                        (SELECT user_id FROM analyses a JOIN findings f ON a.id = f.analysis_id WHERE f.id = $1),
                        $2, $3, NOW()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        review_label = EXCLUDED.review_label,
                        notes = EXCLUDED.notes;
                    """,
                    finding_id, decision, notes or ""
                )
                return await self.get_finding(finding_id)
            finally:
                await conn.close()

        return self._run_async(_update())

    def reconcile_incomplete_jobs(self) -> int:
        async def _reconcile():
            conn = await self._get_conn()
            try:
                res = await conn.execute(
                    """
                    UPDATE documents
                    SET status = 'failed'
                    WHERE status IN ('processing', 'extracting')
                    """
                )
                doc_count = int(res.split(" ")[-1])

                res2 = await conn.execute(
                    """
                    UPDATE analyses
                    SET status = 'failed'
                    WHERE status IN ('running', 'processing')
                    """
                )
                ana_count = int(res2.split(" ")[-1])
                return doc_count + ana_count
            finally:
                await conn.close()

        return self._run_async(_reconcile())


_pg_repo_instance: Optional[PostgresMetadataRepository] = None


def get_pg_repo() -> PostgresMetadataRepository:
    """Returns singleton PostgresMetadataRepository instance."""
    global _pg_repo_instance
    if _pg_repo_instance is None:
        _pg_repo_instance = PostgresMetadataRepository()
    return _pg_repo_instance
