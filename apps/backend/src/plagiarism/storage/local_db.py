"""
Local SQLite Metadata Repository Adapter for Development Mode
Survives backend restart, enforces foreign keys, and isolates local metadata.
"""

import json
import logging
import sqlite3
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from plagiarism.core.config import get_settings

logger = logging.getLogger(__name__)


def utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


class LocalMetadataRepository:
    """
    SQLite-backed local development adapter for document metadata,
    extracted passages, and reference collections.
    """
    def __init__(self, db_path: Path | None = None):
        settings = get_settings()
        self.db_path = db_path or settings.LOCAL_SQLITE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=30.0
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    owner_user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    page_count INTEGER DEFAULT 1,
                    char_count INTEGER DEFAULT 0,
                    word_count INTEGER DEFAULT 0,
                    raw_text TEXT DEFAULT '',
                    detected_language TEXT DEFAULT 'en',
                    status TEXT DEFAULT 'queued',
                    created_at TEXT NOT NULL,
                    processing_warnings TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS document_sources (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    author TEXT,
                    license TEXT DEFAULT 'CC-BY-4.0',
                    provenance_uri TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS passages (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    sequence_index INTEGER NOT NULL,
                    start_offset INTEGER NOT NULL,
                    end_offset INTEGER NOT NULL,
                    text_content TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    page_number INTEGER DEFAULT 1,
                    language TEXT DEFAULT 'en',
                    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS collections (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_user_id TEXT NOT NULL,
                    is_public_within_tenant INTEGER DEFAULT 0,
                    document_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS collection_documents (
                    collection_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    indexed_at TEXT NOT NULL,
                    status TEXT DEFAULT 'INDEXED',
                    PRIMARY KEY (collection_id, document_id),
                    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS document_fingerprints (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    hash_val INTEGER NOT NULL,
                    token_start INTEGER NOT NULL,
                    token_end INTEGER NOT NULL,
                    char_start INTEGER NOT NULL,
                    char_end INTEGER NOT NULL,
                    algorithm_version TEXT NOT NULL,
                    is_short_fallback INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS analyses (
                    analysis_id TEXT PRIMARY KEY,
                    owner_user_id TEXT NOT NULL,
                    submission_document_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    detection_mode TEXT DEFAULT 'hybrid',
                    reference_document_id TEXT,
                    collection_id TEXT,
                    status TEXT DEFAULT 'queued',
                    current_step TEXT DEFAULT 'enqueued',
                    progress_percent INTEGER DEFAULT 0,
                    overall_lexical_coverage_percent REAL DEFAULT 0.0,
                    overall_semantic_coverage_percent REAL DEFAULT 0.0,
                    net_adjusted_score_percent REAL DEFAULT 0.0,
                    hybrid_evidence_coverage_percent REAL DEFAULT 0.0,
                    reviewer_adjusted_coverage_percent REAL,
                    reviewer_notes TEXT DEFAULT '',
                    reviewed_findings_count INTEGER DEFAULT 0,
                    matched_source_count INTEGER DEFAULT 0,
                    total_findings_count INTEGER DEFAULT 0,
                    candidate_metadata TEXT DEFAULT '{}',
                    error_code TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (submission_document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS analysis_findings (
                    finding_id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL,
                    submission_document_id TEXT NOT NULL,
                    reference_document_id TEXT NOT NULL,
                    reference_source_title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    submission_start_offset INTEGER NOT NULL,
                    submission_end_offset INTEGER NOT NULL,
                    submission_excerpt TEXT NOT NULL,
                    reference_start_offset INTEGER NOT NULL,
                    reference_end_offset INTEGER NOT NULL,
                    reference_excerpt TEXT NOT NULL,
                    reference_page_number INTEGER DEFAULT 1,
                    matched_token_count INTEGER NOT NULL,
                    lexical_similarity REAL DEFAULT 1.0,
                    semantic_similarity REAL DEFAULT 0.0,
                    is_quoted INTEGER DEFAULT 0,
                    is_excluded INTEGER DEFAULT 0,
                    language_pair TEXT,
                    model_name TEXT,
                    review_decision TEXT DEFAULT 'unreviewed',
                    reviewer_notes TEXT DEFAULT '',
                    reviewer_updated_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id) ON DELETE CASCADE,
                    FOREIGN KEY (submission_document_id) REFERENCES documents(document_id) ON DELETE CASCADE,
                    FOREIGN KEY (reference_document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS analysis_sources (
                    analysis_id TEXT NOT NULL,
                    reference_document_id TEXT NOT NULL,
                    source_title TEXT NOT NULL,
                    matched_passage_count INTEGER NOT NULL,
                    lexical_coverage_percent REAL NOT NULL,
                    semantic_coverage_percent REAL DEFAULT 0.0,
                    PRIMARY KEY (analysis_id, reference_document_id),
                    FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id) ON DELETE CASCADE,
                    FOREIGN KEY (reference_document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                );

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

                CREATE INDEX IF NOT EXISTS idx_documents_owner ON documents(owner_user_id);
                CREATE INDEX IF NOT EXISTS idx_passages_doc ON passages(document_id);
                CREATE INDEX IF NOT EXISTS idx_colldoc_col ON collection_documents(collection_id);
                CREATE INDEX IF NOT EXISTS idx_doc_fp_hash ON document_fingerprints(hash_val);
                CREATE INDEX IF NOT EXISTS idx_doc_fp_doc ON document_fingerprints(document_id);
                CREATE INDEX IF NOT EXISTS idx_analyses_owner ON analyses(owner_user_id);
                CREATE INDEX IF NOT EXISTS idx_analyses_sub ON analyses(submission_document_id);
                CREATE INDEX IF NOT EXISTS idx_findings_analysis ON analysis_findings(analysis_id);
                CREATE INDEX IF NOT EXISTS idx_emb_doc ON passage_embeddings(document_id);
                CREATE INDEX IF NOT EXISTS idx_emb_model ON passage_embeddings(model_id, model_revision);
                """)

                # Non-destructive migrations for existing SQLite databases
                try:
                    cursor.execute("ALTER TABLE analyses ADD COLUMN detection_mode TEXT DEFAULT 'hybrid';")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute("ALTER TABLE analyses ADD COLUMN hybrid_evidence_coverage_percent REAL DEFAULT 0.0;")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute("ALTER TABLE analyses ADD COLUMN reviewer_adjusted_coverage_percent REAL;")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute("ALTER TABLE analyses ADD COLUMN reviewer_notes TEXT DEFAULT '';")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute("ALTER TABLE analyses ADD COLUMN reviewed_findings_count INTEGER DEFAULT 0;")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute("ALTER TABLE analysis_findings ADD COLUMN language_pair TEXT;")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute("ALTER TABLE analysis_findings ADD COLUMN model_name TEXT;")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute("ALTER TABLE analysis_findings ADD COLUMN review_decision TEXT DEFAULT 'unreviewed';")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute("ALTER TABLE analysis_findings ADD COLUMN reviewer_notes TEXT DEFAULT '';")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute("ALTER TABLE analysis_findings ADD COLUMN reviewer_updated_at TEXT;")
                except sqlite3.OperationalError:
                    pass

                conn.commit()
            finally:
                conn.close()

    def reconcile_incomplete_jobs(self) -> int:
        """Mark any jobs left in 'processing' or 'queued' state during an unexpected restart as failed."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE documents SET status = 'failed', processing_warnings = 'Processing interrupted by server restart' WHERE status = 'processing'"
                )
                reconciled = cursor.rowcount
                cursor.execute(
                    "UPDATE analyses SET status = 'failed', error_code = 'INTERRUPTED', error_message = 'Analysis interrupted by server restart' WHERE status IN ('queued', 'processing')"
                )
                reconciled += cursor.rowcount
                conn.commit()
                return reconciled
            finally:
                conn.close()

    # --- Document Operations ---

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
        title: str | None = None
    ) -> dict[str, Any]:
        with self._lock:
            conn = self._get_connection()
            try:
                now = utcnow_iso()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO documents (
                        document_id, owner_user_id, filename, mime_type,
                        sha256_hash, storage_path, file_size_bytes, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (document_id, owner_user_id, filename, mime_type, sha256_hash, storage_path, file_size_bytes, status, now)
                )
                if title:
                    source_id = f"src-{document_id}"
                    cursor.execute(
                        """
                        INSERT INTO document_sources (id, document_id, title)
                        VALUES (?, ?, ?)
                        """,
                        (source_id, document_id, title)
                    )
                conn.commit()
                return self.get_document(document_id) or {}
            finally:
                conn.close()

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
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE documents
                    SET status = ?, page_count = ?, char_count = ?, word_count = ?,
                        raw_text = ?, detected_language = ?, processing_warnings = ?
                    WHERE document_id = ?
                    """,
                    (status, page_count, char_count, word_count, raw_text, detected_language, warnings, document_id)
                )
                conn.commit()
            finally:
                conn.close()

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT d.*, s.title, s.author, s.license
                    FROM documents d
                    LEFT JOIN document_sources s ON d.document_id = s.document_id
                    WHERE d.document_id = ?
                    """,
                    (document_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def list_documents(
        self,
        owner_user_id: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if owner_user_id:
                    cursor.execute("SELECT COUNT(*) FROM documents WHERE owner_user_id = ?", (owner_user_id,))
                    total = cursor.fetchone()[0]
                    cursor.execute(
                        """
                        SELECT d.*, s.title, s.author, s.license
                        FROM documents d
                        LEFT JOIN document_sources s ON d.document_id = s.document_id
                        WHERE d.owner_user_id = ?
                        ORDER BY d.created_at DESC
                        LIMIT ? OFFSET ?
                        """,
                        (owner_user_id, limit, offset)
                    )
                else:
                    cursor.execute("SELECT COUNT(*) FROM documents")
                    total = cursor.fetchone()[0]
                    cursor.execute(
                        """
                        SELECT d.*, s.title, s.author, s.license
                        FROM documents d
                        LEFT JOIN document_sources s ON d.document_id = s.document_id
                        ORDER BY d.created_at DESC
                        LIMIT ? OFFSET ?
                        """,
                        (limit, offset)
                    )
                rows = cursor.fetchall()
                return [dict(r) for r in rows], total
            finally:
                conn.close()

    def delete_document(self, document_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                # Find collections that contained this document to update document_count
                cursor.execute("SELECT collection_id FROM collection_documents WHERE document_id = ?", (document_id,))
                col_ids = [r[0] for r in cursor.fetchall()]

                cursor.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
                deleted = cursor.rowcount > 0

                for cid in col_ids:
                    cursor.execute(
                        "UPDATE collections SET document_count = (SELECT COUNT(*) FROM collection_documents WHERE collection_id = ?) WHERE id = ?",
                        (cid, cid)
                    )
                conn.commit()
                return deleted
            finally:
                conn.close()

    # --- Passages Operations ---

    def insert_passages(self, passages: list[dict[str, Any]]) -> None:
        if not passages:
            return
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.executemany(
                    """
                    INSERT INTO passages (
                        id, document_id, sequence_index, start_offset,
                        end_offset, text_content, token_count, page_number, language
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            p["id"],
                            p["document_id"],
                            p["sequence_index"],
                            p["start_offset"],
                            p["end_offset"],
                            p["text_content"],
                            p["token_count"],
                            p.get("page_number", 1),
                            p.get("language", "en")
                        )
                        for p in passages
                    ]
                )
                conn.commit()
            finally:
                conn.close()

    def get_passages(self, document_id: str) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM passages WHERE document_id = ? ORDER BY sequence_index ASC",
                    (document_id,)
                )
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    # --- Collections Operations ---

    def create_collection(
        self,
        collection_id: str,
        name: str,
        owner_user_id: str,
        description: str | None = None,
        is_public_within_tenant: bool = False
    ) -> dict[str, Any]:
        with self._lock:
            conn = self._get_connection()
            try:
                now = utcnow_iso()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO collections (
                        id, name, description, owner_user_id, is_public_within_tenant, document_count, created_at
                    ) VALUES (?, ?, ?, ?, ?, 0, ?)
                    """,
                    (collection_id, name, description or "", owner_user_id, 1 if is_public_within_tenant else 0, now)
                )
                conn.commit()
                return self.get_collection(collection_id) or {}
            finally:
                conn.close()

    def get_collection(self, collection_id: str) -> dict[str, Any] | None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM collections WHERE id = ?", (collection_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                data = dict(row)
                data["is_public_within_tenant"] = bool(data["is_public_within_tenant"])
                return data
            finally:
                conn.close()

    def list_collections(
        self,
        owner_user_id: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if owner_user_id:
                    cursor.execute("SELECT COUNT(*) FROM collections WHERE owner_user_id = ? OR is_public_within_tenant = 1", (owner_user_id,))
                    total = cursor.fetchone()[0]
                    cursor.execute(
                        """
                        SELECT * FROM collections
                        WHERE owner_user_id = ? OR is_public_within_tenant = 1
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                        """,
                        (owner_user_id, limit, offset)
                    )
                else:
                    cursor.execute("SELECT COUNT(*) FROM collections")
                    total = cursor.fetchone()[0]
                    cursor.execute(
                        "SELECT * FROM collections ORDER BY created_at DESC LIMIT ? OFFSET ?",
                        (limit, offset)
                    )
                rows = cursor.fetchall()
                result = []
                for r in rows:
                    item = dict(r)
                    item["is_public_within_tenant"] = bool(item["is_public_within_tenant"])
                    result.append(item)
                return result, total
            finally:
                conn.close()

    def add_document_to_collection(self, collection_id: str, document_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            try:
                now = utcnow_iso()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO collection_documents (collection_id, document_id, indexed_at, status)
                    VALUES (?, ?, ?, 'INDEXED')
                    """,
                    (collection_id, document_id, now)
                )
                # Recalculate document_count
                cursor.execute(
                    "UPDATE collections SET document_count = (SELECT COUNT(*) FROM collection_documents WHERE collection_id = ?) WHERE id = ?",
                    (collection_id, collection_id)
                )
                conn.commit()
                return True
            finally:
                conn.close()

    def remove_document_from_collection(self, collection_id: str, document_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM collection_documents WHERE collection_id = ? AND document_id = ?",
                    (collection_id, document_id)
                )
                deleted = cursor.rowcount > 0
                cursor.execute(
                    "UPDATE collections SET document_count = (SELECT COUNT(*) FROM collection_documents WHERE collection_id = ?) WHERE id = ?",
                    (collection_id, collection_id)
                )
                conn.commit()
                return deleted
            finally:
                conn.close()

    def list_collection_documents(self, collection_id: str) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT d.*, cd.indexed_at as collection_indexed_at
                    FROM collection_documents cd
                    JOIN documents d ON cd.document_id = d.document_id
                    WHERE cd.collection_id = ?
                    ORDER BY cd.indexed_at DESC
                    """,
                    (collection_id,)
                )
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    # --- Fingerprint Operations ---

    def save_fingerprints(
        self,
        document_id: str,
        fingerprints: list[Any],
        algorithm_version: str = "winnowing-k25-w16-v1"
    ) -> int:
        if not fingerprints:
            return 0
        now_str = utcnow_iso()
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM document_fingerprints WHERE document_id = ? AND algorithm_version = ?",
                    (document_id, algorithm_version)
                )
                cursor.executemany(
                    """
                    INSERT INTO document_fingerprints (
                        id, document_id, hash_val, token_start, token_end,
                        char_start, char_end, algorithm_version, is_short_fallback, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            str(uuid.uuid4()),
                            document_id,
                            int(fp.hash_val),
                            int(fp.token_start),
                            int(fp.token_end),
                            int(fp.char_start),
                            int(fp.char_end),
                            algorithm_version,
                            1 if getattr(fp, "is_short_fallback", False) else 0,
                            now_str
                        )
                        for fp in fingerprints
                    ]
                )
                conn.commit()
                return len(fingerprints)
            finally:
                conn.close()

    def get_fingerprints(self, document_id: str) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM document_fingerprints WHERE document_id = ? ORDER BY token_start ASC",
                    (document_id,)
                )
                return [dict(r) for r in cursor.fetchall()]
            finally:
                conn.close()

    def find_shared_fingerprints(
        self,
        submission_id: str,
        candidate_ids: list[str]
    ) -> list[dict[str, Any]]:
        if not candidate_ids:
            return []
        placeholders = ",".join("?" for _ in candidate_ids)
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                query = f"""
                SELECT
                    s.hash_val,
                    s.document_id as submission_document_id,
                    s.token_start as sub_token_start,
                    s.token_end as sub_token_end,
                    s.char_start as sub_char_start,
                    s.char_end as sub_char_end,
                    r.document_id as reference_document_id,
                    r.token_start as ref_token_start,
                    r.token_end as ref_token_end,
                    r.char_start as ref_char_start,
                    r.char_end as ref_char_end
                FROM document_fingerprints s
                JOIN document_fingerprints r ON s.hash_val = r.hash_val
                WHERE s.document_id = ? AND r.document_id IN ({placeholders})
                ORDER BY s.token_start ASC
                """
                cursor.execute(query, [submission_id, *candidate_ids])
                return [dict(r) for r in cursor.fetchall()]
            finally:
                conn.close()

    # --- Analysis Operations ---

    def create_analysis(
        self,
        analysis_id: str,
        owner_user_id: str,
        submission_document_id: str,
        mode: str,
        reference_document_id: str | None = None,
        collection_id: str | None = None,
        candidate_metadata: dict[str, Any] | None = None,
        detection_mode: str = "hybrid",
    ) -> dict[str, Any]:
        now_str = utcnow_iso()
        meta_json = json.dumps(candidate_metadata or {})
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO analyses (
                        analysis_id, owner_user_id, submission_document_id, mode,
                        detection_mode, reference_document_id, collection_id, status, current_step,
                        progress_percent, overall_lexical_coverage_percent,
                        overall_semantic_coverage_percent, net_adjusted_score_percent,
                        hybrid_evidence_coverage_percent, candidate_metadata, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', 'enqueued', 0, 0.0, 0.0, 0.0, 0.0, ?, ?)
                    """,
                    (
                        analysis_id,
                        owner_user_id,
                        submission_document_id,
                        mode,
                        detection_mode,
                        reference_document_id,
                        collection_id,
                        meta_json,
                        now_str
                    )
                )
                conn.commit()
            finally:
                conn.close()
        return self.get_analysis(analysis_id)

    def update_analysis_status(
        self,
        analysis_id: str,
        status: str,
        progress_percent: int,
        current_step: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        completed_at: str | None = None
    ) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE analyses SET
                        status = ?,
                        progress_percent = ?,
                        current_step = COALESCE(?, current_step),
                        error_code = COALESCE(?, error_code),
                        error_message = COALESCE(?, error_message),
                        completed_at = COALESCE(?, completed_at)
                    WHERE analysis_id = ?
                    """,
                    (
                        status,
                        progress_percent,
                        current_step,
                        error_code,
                        error_message,
                        completed_at,
                        analysis_id
                    )
                )
                conn.commit()
            finally:
                conn.close()

    def save_analysis_results(
        self,
        analysis_id: str,
        overall_lexical_cov: float,
        findings: list[Any],
        sources: list[Any],
        candidate_metadata: dict[str, Any] | None = None,
        overall_semantic_cov: float = 0.0,
        net_adjusted_score: float | None = None,
        hybrid_evidence_cov: float | None = None,
    ) -> None:
        now_str = utcnow_iso()
        calculated_net = net_adjusted_score if net_adjusted_score is not None else overall_lexical_cov
        calculated_hybrid_cov = hybrid_evidence_cov if hybrid_evidence_cov is not None else max(overall_lexical_cov, overall_semantic_cov)

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                meta_json = json.dumps(candidate_metadata or {})
                cursor.execute(
                    """
                    UPDATE analyses SET
                        status = 'completed',
                        progress_percent = 100,
                        current_step = 'completed',
                        overall_lexical_coverage_percent = ?,
                        overall_semantic_coverage_percent = ?,
                        net_adjusted_score_percent = ?,
                        hybrid_evidence_coverage_percent = ?,
                        reviewer_adjusted_coverage_percent = ?,
                        reviewed_findings_count = 0,
                        matched_source_count = ?,
                        total_findings_count = ?,
                        candidate_metadata = ?,
                        completed_at = ?
                    WHERE analysis_id = ?
                    """,
                    (
                        overall_lexical_cov,
                        overall_semantic_cov,
                        calculated_net,
                        calculated_hybrid_cov,
                        calculated_hybrid_cov,
                        len(sources),
                        len(findings),
                        meta_json,
                        now_str,
                        analysis_id
                    )
                )

                if findings:
                    cursor.executemany(
                        """
                        INSERT INTO analysis_findings (
                            finding_id, analysis_id, submission_document_id,
                            reference_document_id, reference_source_title,
                            category, confidence, submission_start_offset,
                            submission_end_offset, submission_excerpt,
                            reference_start_offset, reference_end_offset,
                            reference_excerpt, reference_page_number,
                            matched_token_count, lexical_similarity,
                            semantic_similarity, is_quoted, is_excluded,
                            language_pair, model_name, review_decision,
                            reviewer_notes, reviewer_updated_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        [
                            (
                                f.finding_id,
                                analysis_id,
                                f.submission_document_id,
                                f.reference_document_id,
                                f.reference_source_title,
                                f.category,
                                f.confidence,
                                f.submission_start_offset,
                                f.submission_end_offset,
                                f.submission_excerpt,
                                f.reference_start_offset,
                                f.reference_end_offset,
                                f.reference_excerpt,
                                getattr(f, "reference_page_number", 1) or 1,
                                getattr(f, "matched_token_count", 0),
                                getattr(f, "lexical_similarity", 1.0),
                                getattr(f, "semantic_similarity", 0.0),
                                1 if f.is_quoted else 0,
                                1 if f.is_excluded else 0,
                                getattr(f, "language_pair", None),
                                getattr(f, "model_name", None),
                                getattr(f, "review_decision", "unreviewed") or "unreviewed",
                                getattr(f, "reviewer_notes", "") or "",
                                getattr(f, "reviewer_updated_at", None),
                                now_str
                            )
                            for f in findings
                        ]
                    )

                if sources:
                    cursor.executemany(
                        """
                        INSERT OR REPLACE INTO analysis_sources (
                            analysis_id, reference_document_id, source_title,
                            matched_passage_count, lexical_coverage_percent,
                            semantic_coverage_percent
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        [
                            (
                                analysis_id,
                                s.reference_document_id,
                                s.source_title,
                                s.matched_passage_count,
                                s.lexical_coverage_percent,
                                getattr(s, "semantic_coverage_percent", 0.0)
                            )
                            for s in sources
                        ]
                    )

                conn.commit()
            finally:
                conn.close()

    def get_analysis(self, analysis_id: str) -> dict[str, Any] | None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT a.*, d.filename as submission_filename
                    FROM analyses a
                    LEFT JOIN documents d ON a.submission_document_id = d.document_id
                    WHERE a.analysis_id = ?
                    """,
                    (analysis_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return None
                data = dict(row)
                if data.get("candidate_metadata"):
                    try:
                        data["candidate_metadata"] = json.loads(data["candidate_metadata"])
                    except Exception:
                        pass
                return data
            finally:
                conn.close()

    def get_analysis_findings(self, analysis_id: str) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM analysis_findings
                    WHERE analysis_id = ?
                    ORDER BY submission_start_offset ASC
                    """,
                    (analysis_id,)
                )
                return [dict(r) for r in cursor.fetchall()]
            finally:
                conn.close()

    def get_finding(self, finding_id: str) -> dict[str, Any] | None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM analysis_findings WHERE finding_id = ?", (finding_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def update_finding_review(
        self,
        finding_id: str,
        decision: str,
        notes: str | None = None
    ) -> dict[str, Any] | None:
        with self._lock:
            conn = self._get_connection()
            try:
                now_str = utcnow_iso()
                is_quoted = 1 if decision == "quoted_cited" else 0
                is_excluded = 1 if decision == "exclude" else 0
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE analysis_findings SET
                        review_decision = ?,
                        reviewer_notes = COALESCE(?, reviewer_notes),
                        reviewer_updated_at = ?,
                        is_quoted = ?,
                        is_excluded = ?
                    WHERE finding_id = ?
                    """,
                    (decision, notes, now_str, is_quoted, is_excluded, finding_id)
                )
                conn.commit()
                cursor.execute("SELECT * FROM analysis_findings WHERE finding_id = ?", (finding_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def update_analysis_review_summary(
        self,
        analysis_id: str,
        reviewer_adjusted_coverage_percent: float,
        reviewed_findings_count: int,
        notes: str | None = None
    ) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE analyses SET
                        reviewer_adjusted_coverage_percent = ?,
                        reviewed_findings_count = ?,
                        reviewer_notes = COALESCE(?, reviewer_notes)
                    WHERE analysis_id = ?
                    """,
                    (reviewer_adjusted_coverage_percent, reviewed_findings_count, notes, analysis_id)
                )
                conn.commit()
            finally:
                conn.close()

    def get_analysis_sources(self, analysis_id: str) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM analysis_sources
                    WHERE analysis_id = ?
                    ORDER BY lexical_coverage_percent DESC
                    """,
                    (analysis_id,)
                )
                return [dict(r) for r in cursor.fetchall()]
            finally:
                conn.close()

    def list_analyses(
        self,
        owner_user_id: str | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if owner_user_id:
                    cursor.execute("SELECT COUNT(*) FROM analyses WHERE owner_user_id = ?", (owner_user_id,))
                    total = cursor.fetchone()[0]
                    cursor.execute(
                        """
                        SELECT a.*, d.filename as submission_filename
                        FROM analyses a
                        LEFT JOIN documents d ON a.submission_document_id = d.document_id
                        WHERE a.owner_user_id = ?
                        ORDER BY a.created_at DESC
                        LIMIT ? OFFSET ?
                        """,
                        (owner_user_id, limit, offset)
                    )
                else:
                    cursor.execute("SELECT COUNT(*) FROM analyses")
                    total = cursor.fetchone()[0]
                    cursor.execute(
                        """
                        SELECT a.*, d.filename as submission_filename
                        FROM analyses a
                        LEFT JOIN documents d ON a.submission_document_id = d.document_id
                        ORDER BY a.created_at DESC
                        LIMIT ? OFFSET ?
                        """,
                        (limit, offset)
                    )
                rows = cursor.fetchall()
                results = []
                for r in rows:
                    item = dict(r)
                    if item.get("candidate_metadata"):
                        try:
                            item["candidate_metadata"] = json.loads(item["candidate_metadata"])
                        except Exception:
                            pass
                    results.append(item)
                return results, total
            finally:
                conn.close()

    def delete_analysis(self, analysis_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM analyses WHERE analysis_id = ?", (analysis_id,))
                deleted = cursor.rowcount > 0
                conn.commit()
                return deleted
            finally:
                conn.close()


_local_repo: Any | None = None


def get_local_repo() -> Any:
    """Returns singleton MetadataRepository instance (PostgreSQL in production, SQLite in local)."""
    global _local_repo
    if _local_repo is None:
        from plagiarism.core.config import get_settings
        settings = get_settings()
        if getattr(settings, "APP_RUNTIME_MODE", "local") == "production":
            try:
                from plagiarism.storage.pg_db import get_pg_repo
                _local_repo = get_pg_repo()
                logger.info("Initialized production PostgreSQL metadata repository")
            except Exception as e:
                logger.warning(
                    f"Could not initialize PostgresMetadataRepository ({e}); falling back to LocalMetadataRepository"
                )
                _local_repo = LocalMetadataRepository()
        else:
            _local_repo = LocalMetadataRepository()
    return _local_repo


get_repository = get_local_repo
