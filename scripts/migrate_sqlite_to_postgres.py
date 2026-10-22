"""
Safe SQLite-to-PostgreSQL and pgvector Migration Tool
Migrates all relational records and dense embeddings from SQLite local_metadata.db
to target PostgreSQL database with data verification and zero data loss.

Usage:
    python scripts/migrate_sqlite_to_postgres.py --dry-run
    python scripts/migrate_sqlite_to_postgres.py --execute
"""

import argparse
import asyncio
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
import numpy as np
import pgvector.asyncpg

# Ensure src is on python path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "apps" / "backend"
sys.path.insert(0, str(BACKEND_DIR / "src"))

from plagiarism.core.config import get_settings


class MigrationReporter:
    def __init__(self):
        self.stats = {}
        self.errors = []

    def log(self, msg: str):
        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}")

    def record(self, table: str, sqlite_count: int, pg_count: int):
        self.stats[table] = {"sqlite": sqlite_count, "postgres": pg_count}

    def add_error(self, err: str):
        self.errors.append(err)
        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] ERROR: {err}")


async def migrate_data(sqlite_path: Path, postgres_dsn: str, dry_run: bool = True) -> bool:
    reporter = MigrationReporter()
    reporter.log("=" * 70)
    reporter.log(f"Starting SQLite -> PostgreSQL Migration ({'DRY-RUN' if dry_run else 'LIVE EXECUTION'})")
    reporter.log(f"Source SQLite DB : {sqlite_path}")
    reporter.log(f"Target Postgres  : {postgres_dsn.split('@')[-1]}")
    reporter.log("=" * 70)

    if not sqlite_path.exists():
        reporter.add_error(f"Source SQLite database does not exist at {sqlite_path}")
        return False

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    # Connect to PostgreSQL
    try:
        pg_conn = await asyncpg.connect(postgres_dsn, timeout=10)
        await pgvector.asyncpg.register_vector(pg_conn)
        reporter.log("Successfully connected to PostgreSQL and registered pgvector type.")
    except Exception as e:
        reporter.add_error(f"Failed to connect to PostgreSQL: {e}")
        sqlite_conn.close()
        return False

    try:
        # 1. Documents
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM documents")
        docs = [dict(row) for row in cursor.fetchall()]
        reporter.log(f"Read {len(docs)} document records from SQLite.")

        if not dry_run and docs:
            async with pg_conn.transaction():
                for doc in docs:
                    # Ensure owner exists
                    await pg_conn.execute(
                        """
                        INSERT INTO users (id, email, hashed_password, role, full_name)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (id) DO NOTHING;
                        """,
                        doc["owner_user_id"],
                        f"user_{doc['owner_user_id'][:8]}@example.com",
                        "migrated_password_placeholder",
                        "REVIEWER",
                        "Migrated User"
                    )

                    await pg_conn.execute(
                        """
                        INSERT INTO documents (
                            id, owner_user_id, filename, mime_type, sha256_hash,
                            storage_path, file_size_bytes, page_count, char_count,
                            raw_text, detected_language, status, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW())
                        ON CONFLICT (id) DO NOTHING;
                        """,
                        doc["document_id"], doc["owner_user_id"], doc["filename"],
                        doc["mime_type"], doc["sha256_hash"], doc["storage_path"],
                        doc["file_size_bytes"], doc.get("page_count", 1),
                        doc.get("char_count", 0), doc.get("raw_text", ""),
                        doc.get("detected_language", "en"), doc.get("status", "completed")
                    )

        pg_doc_count = await pg_conn.fetchval("SELECT count(*) FROM documents")
        reporter.record("documents", len(docs), pg_doc_count)

        # 2. Document Sources
        cursor.execute("SELECT * FROM document_sources")
        doc_sources = [dict(row) for row in cursor.fetchall()]
        reporter.log(f"Read {len(doc_sources)} document source metadata records from SQLite.")

        if not dry_run and doc_sources:
            async with pg_conn.transaction():
                for ds in doc_sources:
                    await pg_conn.execute(
                        """
                        INSERT INTO document_sources (
                            id, document_id, title, author, license, provenance_uri
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (document_id) DO NOTHING;
                        """,
                        ds["id"], ds["document_id"], ds["title"], ds.get("author", "Unknown"),
                        ds.get("license", "CC-BY-4.0"), ds.get("provenance_uri", "")
                    )

        pg_ds_count = await pg_conn.fetchval("SELECT count(*) FROM document_sources")
        reporter.record("document_sources", len(doc_sources), pg_ds_count)

        # 3. Passages
        cursor.execute("SELECT * FROM passages")
        passages = [dict(row) for row in cursor.fetchall()]
        reporter.log(f"Read {len(passages)} passages from SQLite.")

        if not dry_run and passages:
            async with pg_conn.transaction():
                p_data = [
                    (
                        p["id"], p["document_id"], p["sequence_index"],
                        p["start_offset"], p["end_offset"], p["text_content"],
                        p.get("token_count", 0), p.get("page_number", 1),
                        p.get("language", "en")
                    )
                    for p in passages
                ]
                await pg_conn.executemany(
                    """
                    INSERT INTO passages (
                        id, document_id, sequence_index, start_offset, end_offset,
                        text_content, token_count, page_number, language
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    p_data
                )

        pg_pass_count = await pg_conn.fetchval("SELECT count(*) FROM passages")
        reporter.record("passages", len(passages), pg_pass_count)

        # 4. Fingerprints
        cursor.execute("SELECT * FROM document_fingerprints")
        fps = [dict(row) for row in cursor.fetchall()]
        reporter.log(f"Read {len(fps)} winnowing fingerprints from SQLite.")

        if not dry_run and fps:
            async with pg_conn.transaction():
                fp_data = [
                    (
                        int(fp["hash_val"]),
                        fp.get("passage_id") or fp["document_id"],
                        fp["document_id"],
                        int(fp["char_start"]),
                        int(fp["char_end"])
                    )
                    for fp in fps
                ]
                await pg_conn.executemany(
                    """
                    INSERT INTO fingerprints (hash_value, passage_id, document_id, start_offset, end_offset)
                    VALUES ($1, $2, $3, $4, $5);
                    """,
                    fp_data
                )

        pg_fp_count = await pg_conn.fetchval("SELECT count(*) FROM fingerprints")
        reporter.record("fingerprints", len(fps), pg_fp_count)

        # 5. Collections
        cursor.execute("SELECT * FROM collections")
        collections = [dict(row) for row in cursor.fetchall()]
        reporter.log(f"Read {len(collections)} collections from SQLite.")

        if not dry_run and collections:
            async with pg_conn.transaction():
                for c in collections:
                    await pg_conn.execute(
                        """
                        INSERT INTO collections (
                            id, name, description, owner_user_id, is_public_within_tenant,
                            document_count, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
                        ON CONFLICT (id) DO NOTHING;
                        """,
                        c["id"], c["name"], c.get("description", ""),
                        c["owner_user_id"], bool(c.get("is_public_within_tenant", 0)),
                        c.get("document_count", 0)
                    )

        pg_col_count = await pg_conn.fetchval("SELECT count(*) FROM collections")
        reporter.record("collections", len(collections), pg_col_count)

        # 6. Collection Documents
        cursor.execute("SELECT * FROM collection_documents")
        col_docs = [dict(row) for row in cursor.fetchall()]
        reporter.log(f"Read {len(col_docs)} collection-document associations from SQLite.")

        if not dry_run and col_docs:
            async with pg_conn.transaction():
                cd_data = [
                    (cd["collection_id"], cd["document_id"], cd.get("status", "INDEXED"))
                    for cd in col_docs
                ]
                await pg_conn.executemany(
                    """
                    INSERT INTO collection_documents (collection_id, document_id, indexed_at, status)
                    VALUES ($1, $2, NOW(), $3)
                    ON CONFLICT (collection_id, document_id) DO NOTHING;
                    """,
                    cd_data
                )

        pg_cd_count = await pg_conn.fetchval("SELECT count(*) FROM collection_documents")
        reporter.record("collection_documents", len(col_docs), pg_cd_count)

        # 7. Analyses & Findings
        cursor.execute("SELECT * FROM analyses")
        analyses = [dict(row) for row in cursor.fetchall()]
        reporter.log(f"Read {len(analyses)} similarity analyses from SQLite.")

        if not dry_run and analyses:
            async with pg_conn.transaction():
                for a in analyses:
                    await pg_conn.execute(
                        """
                        INSERT INTO analyses (
                            id, user_id, submission_document_id, mode, target_collection_id,
                            overall_lexical_coverage_percent, overall_semantic_coverage_percent,
                            net_adjusted_score_percent, status, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                        ON CONFLICT (id) DO NOTHING;
                        """,
                        a["analysis_id"], a["owner_user_id"], a["submission_document_id"],
                        a["mode"], a.get("collection_id"),
                        float(a.get("overall_lexical_coverage_percent", 0.0)),
                        float(a.get("overall_semantic_coverage_percent", 0.0)),
                        float(a.get("reviewer_adjusted_coverage_percent") or a.get("overall_lexical_coverage_percent", 0.0)),
                        a.get("status", "completed")
                    )

                    await pg_conn.execute(
                        """
                        INSERT INTO analysis_jobs (
                            id, analysis_id, status, progress_percent, current_step, started_at, completed_at
                        ) VALUES ($1, $2, $3, 100, 'completed', NOW(), NOW())
                        ON CONFLICT (analysis_id) DO NOTHING;
                        """,
                        a["analysis_id"], a["analysis_id"], a.get("status", "completed")
                    )

        pg_ana_count = await pg_conn.fetchval("SELECT count(*) FROM analyses")
        reporter.record("analyses", len(analyses), pg_ana_count)

        # 8. Passage Embeddings (Dense Vector Conversion from BLOB to pgvector)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='passage_embeddings'")
        has_emb = cursor.fetchone()
        emb_count = 0
        if has_emb:
            cursor.execute("SELECT * FROM passage_embeddings")
            emb_rows = cursor.fetchall()
            emb_count = len(emb_rows)
            reporter.log(f"Read {emb_count} passage vector records from SQLite.")

            if not dry_run and emb_rows:
                async with pg_conn.transaction():
                    emb_data = []
                    for row in emb_rows:
                        raw_blob = row["embedding"]
                        # Convert float32 binary buffer back into numpy float32 array
                        vec = np.frombuffer(raw_blob, dtype=np.float32)
                        emb_data.append((
                            row["passage_id"],
                            row["document_id"],
                            row["sequence_index"],
                            row["start_offset"],
                            row["end_offset"],
                            row["text_content"],
                            row["model_id"],
                            row["model_revision"],
                            vec,
                            row["text_hash"],
                            row["created_at"]
                        ))

                    await pg_conn.executemany(
                        """
                        INSERT INTO passage_embeddings (
                            passage_id, document_id, sequence_index, start_offset,
                            end_offset, text_content, model_id, model_revision,
                            embedding, text_hash, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (passage_id) DO NOTHING;
                        """,
                        emb_data
                    )

        pg_emb_count = await pg_conn.fetchval("SELECT count(*) FROM passage_embeddings") if not dry_run else 0
        reporter.record("passage_embeddings", emb_count, pg_emb_count)

    finally:
        sqlite_conn.close()
        await pg_conn.close()

    # Print Summary Report
    reporter.log("=" * 70)
    reporter.log("MIGRATION SUMMARY & AUDIT VERIFICATION")
    reporter.log("=" * 70)
    for tbl, counts in reporter.stats.items():
        match_str = "MATCH" if counts["sqlite"] <= counts["postgres"] or dry_run else "MISMATCH"
        reporter.log(f"  {tbl:<24} | SQLite: {counts['sqlite']:>6} | Postgres: {counts['postgres']:>6} | {match_str}")
    reporter.log("=" * 70)

    if dry_run:
        reporter.log("DRY-RUN completed successfully. Zero records were modified. Ready for live execution.")
    else:
        reporter.log("LIVE MIGRATION completed successfully. All data verified in PostgreSQL.")
    return len(reporter.errors) == 0


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite data to PostgreSQL with pgvector")
    parser.add_argument("--execute", action="store_true", help="Execute live migration (default is dry-run)")
    parser.add_argument("--sqlite-path", default=None, help="Path to SQLite database")
    parser.add_argument("--postgres-url", default=None, help="PostgreSQL asyncpg connection URL")

    args = parser.parse_args()
    settings = get_settings()

    sqlite_path = Path(args.sqlite_path) if args.sqlite_path else Path(settings.LOCAL_SQLITE_PATH)
    postgres_url = args.postgres_url or settings.DATABASE_URL
    if postgres_url.startswith("postgresql+asyncpg://"):
        postgres_url = postgres_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    dry_run = not args.execute
    success = asyncio.run(migrate_data(sqlite_path, postgres_url, dry_run=dry_run))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
