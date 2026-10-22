"""
Safe Local Backup and Restore Utility for Phase 7 Hardening.
Uses SQLite's official online backup API (sqlite3.Connection.backup)
to produce crash-consistent hot backups of the metadata repository,
and synchronizes private document storage with manifest verification.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_SRC = REPO_ROOT / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from plagiarism.core.config import get_settings


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def perform_backup(
    backup_dest_dir: Path,
    db_path: Optional[Path] = None,
    storage_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    settings = get_settings()
    src_db = db_path or settings.LOCAL_SQLITE_PATH
    src_storage = storage_dir or (REPO_ROOT / "storage" / "documents")

    backup_dest_dir.mkdir(parents=True, exist_ok=True)
    dest_db = backup_dest_dir / "metadata_backup.db"
    dest_storage = backup_dest_dir / "documents"
    dest_storage.mkdir(parents=True, exist_ok=True)

    if not src_db.exists():
        raise FileNotFoundError(f"Source database not found at: {src_db}")

    # 1. Consistent SQLite Online Backup (safe under WAL concurrency)
    src_conn = sqlite3.connect(str(src_db), timeout=30.0)
    dest_conn = sqlite3.connect(str(dest_db), timeout=30.0)
    try:
        src_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        src_conn.close()

    # 2. Collect database statistics
    dest_conn = sqlite3.connect(str(dest_db))
    dest_conn.row_factory = sqlite3.Row
    try:
        cur = dest_conn.cursor()
        doc_count = cur.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        analysis_count = cur.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        finding_count = cur.execute("SELECT COUNT(*) FROM analysis_findings").fetchone()[0]
        review_count = cur.execute("SELECT COUNT(*) FROM analysis_findings WHERE review_decision != 'unreviewed'").fetchone()[0]
        collection_count = cur.execute("SELECT COUNT(*) FROM collections").fetchone()[0]
    finally:
        dest_conn.close()

    # 3. Synchronize Private Document Storage
    copied_files = 0
    file_hashes: Dict[str, str] = {}
    if src_storage.exists():
        for f in src_storage.rglob("*"):
            if f.is_file():
                rel_path = f.relative_to(src_storage)
                target_f = dest_storage / rel_path
                target_f.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target_f)
                copied_files += 1
                file_hashes[str(rel_path)] = sha256_file(target_f)

    # 4. Generate Manifest
    manifest = {
        "manifest_version": "1.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "database_sha256": sha256_file(dest_db),
        "database_size_bytes": dest_db.stat().st_size,
        "engine_metadata": {
            "model_name": "intfloat/multilingual-e5-small",
            "model_dimension": 384,
            "winnowing_k": 25,
            "winnowing_w": 16,
            "system_phase": "Phase 7",
        },
        "counts": {
            "documents": doc_count,
            "analyses": analysis_count,
            "findings": finding_count,
            "reviewed_findings": review_count,
            "collections": collection_count,
            "stored_files": copied_files,
        },
        "file_hashes": file_hashes,
    }

    manifest_path = backup_dest_dir / "backup_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2)

    return manifest


def perform_restore(
    backup_dir: Path,
    target_db_path: Path,
    target_storage_dir: Path,
) -> Dict[str, Any]:
    manifest_path = backup_dir / "backup_manifest.json"
    backup_db = backup_dir / "metadata_backup.db"
    backup_storage = backup_dir / "documents"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing backup manifest: {manifest_path}")
    if not backup_db.exists():
        raise FileNotFoundError(f"Missing backup database: {backup_db}")

    with open(manifest_path, "r", encoding="utf-8") as mf:
        manifest = json.load(mf)

    # Verify Database Integrity Checksum
    current_db_hash = sha256_file(backup_db)
    if current_db_hash != manifest["database_sha256"]:
        raise ValueError(
            f"Database checksum mismatch! Expected: {manifest['database_sha256']}, got: {current_db_hash}"
        )

    target_db_path.parent.mkdir(parents=True, exist_ok=True)
    target_storage_dir.mkdir(parents=True, exist_ok=True)

    # Online Restore to target DB
    src_conn = sqlite3.connect(str(backup_db), timeout=30.0)
    dest_conn = sqlite3.connect(str(target_db_path), timeout=30.0)
    try:
        src_conn.backup(dest_conn)
        # Check SQLite integrity
        cur = dest_conn.cursor()
        integrity = cur.execute("PRAGMA integrity_check;").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Restored database failed integrity check: {integrity}")

        # Check row counts
        doc_count = cur.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        analysis_count = cur.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
    finally:
        dest_conn.close()
        src_conn.close()

    # Restore Document Storage
    restored_files = 0
    if backup_storage.exists():
        for f in backup_storage.rglob("*"):
            if f.is_file():
                rel = f.relative_to(backup_storage)
                dest_f = target_storage_dir / rel
                dest_f.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest_f)
                restored_files += 1

    return {
        "status": "success",
        "restored_documents": doc_count,
        "restored_analyses": analysis_count,
        "restored_files": restored_files,
        "manifest_timestamp": manifest["timestamp_utc"],
    }


def self_test_backup_and_restore() -> bool:
    """Verifies backup and restore round-trip into disposable isolated directories."""
    print("=" * 70)
    print("  PHASE 7 BACKUP & RESTORE INTEGRITY VERIFICATION")
    print("=" * 70)

    temp_root = Path(tempfile.mkdtemp(prefix="plagiarism_backup_test_"))
    try:
        backup_dir = temp_root / "backup"
        restore_dir = temp_root / "restore"
        restored_db = restore_dir / "restored_metadata.db"
        restored_storage = restore_dir / "documents"

        print(f"1. Performing hot online backup to: {backup_dir}")
        manifest = perform_backup(backup_dir)
        print(f"   [PASS] Backup completed: {manifest['counts']['documents']} documents, {manifest['counts']['analyses']} analyses.")

        print(f"2. Performing isolated restore to: {restore_dir}")
        res = perform_restore(backup_dir, restored_db, restored_storage)
        print(f"   [PASS] Restore completed: {res['restored_documents']} documents restored.")
        assert res["restored_documents"] == manifest["counts"]["documents"]
        assert res["restored_analyses"] == manifest["counts"]["analyses"]

        # Verify restored DB queryable
        conn = sqlite3.connect(str(restored_db))
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]
            assert "documents" in tables
            assert "analyses" in tables
            assert "analysis_findings" in tables
            print(f"   [PASS] Verified {len(tables)} tables present and queryable in restored database.")
        finally:
            conn.close()

        print("\n  [SUCCESS] Backup and Restore self-test verified with zero errors.")
        return True
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plagiarism Platform Backup and Restore Tool")
    parser.add_argument("--test", action="store_true", help="Run self-test in isolated temp dir")
    parser.add_argument("--backup-dir", type=str, default="data/backups/latest", help="Backup destination directory")
    parser.add_argument("--action", choices=["backup", "restore", "test"], default="test")
    args = parser.parse_args()

    if args.action == "test" or args.test:
        ok = self_test_backup_and_restore()
        sys.exit(0 if ok else 1)
    elif args.action == "backup":
        m = perform_backup(Path(args.backup_dir))
        print(f"Backup succeeded into {args.backup_dir}: {json.dumps(m['counts'])}")
    elif args.action == "restore":
        settings = get_settings()
        r = perform_restore(Path(args.backup_dir), settings.LOCAL_SQLITE_PATH, REPO_ROOT / "storage" / "documents")
        print(f"Restore succeeded: {r}")
