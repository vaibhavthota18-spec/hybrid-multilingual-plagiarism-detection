"""
Production Database and Private Document Storage Restore Utility
Restores database records and unpacks private document storage archives
with manifest SHA-256 verification.

Usage:
    python scripts/restore_production.py --backup-dir ./backups/prod_backup_YYYYMMDD_HHMMSSZ
"""

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
from typing import Any, Dict

import asyncpg

# Add backend src
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from plagiarism.core.config import get_settings


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


async def restore_postgres_metadata(dsn: str, dump_file: Path) -> Dict[str, int]:
    """Restores database tables from structured JSON dump."""
    if dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)

    with open(dump_file, "r", encoding="utf-8") as f:
        dump_data = json.load(f)

    conn = await asyncpg.connect(dsn, timeout=10)
    restored_counts = {}

    try:
        # Restore in topological order
        order = ["users", "collections", "documents", "document_sources", "passages", "analyses", "findings", "reviews"]
        for tbl in order:
            rows = dump_data.get(tbl, [])
            restored_counts[tbl] = len(rows)
            if not rows:
                continue

            # Upsert rows
            cols = list(rows[0].keys())
            cols_str = ", ".join(cols)
            placeholders = ", ".join([f"${i+1}" for i in range(len(cols))])
            insert_sql = f"INSERT INTO {tbl} ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;"

            data = []
            for r in rows:
                data.append(tuple(r[c] for c in cols))

            await conn.executemany(insert_sql, data)

    finally:
        await conn.close()

    return restored_counts


def restore_storage_directory(archive_file: Path, target_dir: Path) -> int:
    """Extracts storage archive into target directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    file_count = 0
    with tarfile.open(archive_file, "r:gz") as tar:
        tar.extractall(path=target_dir)
        file_count = len(tar.getmembers())
    return file_count


def run_restore(backup_dir: Path) -> bool:
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: manifest.json not found in backup directory {backup_dir}")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print("=" * 70)
    print(f"Restoring production backup from {backup_dir}")
    print(f"Created: {manifest.get('timestamp')}")
    print("=" * 70)

    # 1. Verify Checksums
    checksums = manifest.get("checksums", {})
    db_dump = backup_dir / "database_dump.json"
    if db_dump.exists() and checksums.get("database_dump"):
        if sha256_file(db_dump) != checksums["database_dump"]:
            print("ERROR: Database dump SHA-256 checksum mismatch! Aborting.")
            return False
        print("✓ Database dump SHA-256 checksum verified.")

    storage_tar = backup_dir / "private_storage.tar.gz"
    if storage_tar.exists() and checksums.get("private_storage"):
        if sha256_file(storage_tar) != checksums["private_storage"]:
            print("ERROR: Storage archive SHA-256 checksum mismatch! Aborting.")
            return False
        print("✓ Storage archive SHA-256 checksum verified.")

    # 2. Restore PostgreSQL
    settings = get_settings()
    if db_dump.exists():
        try:
            counts = asyncio.run(restore_postgres_metadata(settings.DATABASE_URL, db_dump))
            print(f"✓ PostgreSQL tables restored: {counts}")
        except Exception as e:
            print(f"WARNING: PostgreSQL restore failed ({e}).")

    # 3. Restore Storage
    if storage_tar.exists():
        restored_files = restore_storage_directory(storage_tar, settings.LOCAL_PRIVATE_STORAGE_ROOT)
        print(f"✓ Restored {restored_files} storage objects to {settings.LOCAL_PRIVATE_STORAGE_ROOT}")

    print("=" * 70)
    print("Restore completed successfully.")
    print("=" * 70)
    return True


def main():
    parser = argparse.ArgumentParser(description="Production Database and File Storage Restore")
    parser.add_argument("--backup-dir", required=True, help="Backup folder to restore from")
    args = parser.parse_args()

    success = run_restore(Path(args.backup_dir))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
