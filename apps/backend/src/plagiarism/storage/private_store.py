"""
Private Local File Storage Manager
Enforces secure internal storage paths, path traversal defense, and streaming size limits.
Never exposes uploaded files to public or static web server routes.
"""

import hashlib
import os
import re
from pathlib import Path

from fastapi import UploadFile

from plagiarism.core.config import get_settings
from plagiarism.core.errors import BadRequestError, PayloadTooLargeError


def sanitize_filename(filename: str) -> str:
    r"""
    Sanitizes raw client-supplied filenames:
    Strips directory separators, removes null bytes, and collapses unsafe sequences.
    Cross-platform safe: handles both POSIX (/) and Windows (\) separators.
    """
    # Remove null bytes
    cleaned = filename.replace("\x00", "")
    # Normalize Windows backslashes to forward slashes before getting basename so it works identically on Linux and Windows
    cleaned = cleaned.replace("\\", "/")
    # Take basename only to prevent directory traversal
    cleaned = os.path.basename(cleaned)
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", cleaned)
    # Fallback to default if filename is empty or only dots
    if not cleaned or cleaned.strip(". ") == "":
        cleaned = "unnamed_document.txt"
    return cleaned.strip()


class PrivateStorageManager:
    """
    Manages private filesystem storage for uploaded source documents.
    """
    def __init__(self, root_dir: Path | None = None):
        settings = get_settings()
        self.root_dir = (root_dir or settings.LOCAL_PRIVATE_STORAGE_ROOT).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = settings.MAX_UPLOAD_SIZE_BYTES

    def _get_safe_path(self, internal_filename: str) -> Path:
        """
        Resolves path and enforces that it remains strictly inside self.root_dir.
        Defends against directory traversal attacks.
        """
        if ".." in internal_filename or "/" in internal_filename or "\\" in internal_filename:
            raise BadRequestError("Path traversal attempt detected", code="SECURITY_VIOLATION")
        clean_name = os.path.basename(internal_filename)
        candidate = (self.root_dir / clean_name).resolve()
        try:
            candidate.relative_to(self.root_dir)
        except ValueError:
            raise BadRequestError("Path traversal attempt detected", code="SECURITY_VIOLATION")
        return candidate

    async def save_upload_file(
        self,
        upload_file: UploadFile,
        document_id: str,
        extension: str
    ) -> tuple[str, int, str]:
        """
        Streams an uploaded file to secure private storage.
        Computes SHA-256 hash incrementally and enforces maximum upload size.
        Returns: (storage_relative_path, total_bytes_written, sha256_hex_digest)
        """
        # Enforce extension begins with a dot
        if not extension.startswith("."):
            extension = f".{extension}"

        # Clean extension of unsafe characters
        extension = re.sub(r'[^a-zA-Z0-9.]', '', extension.lower())

        internal_filename = f"{document_id}{extension}"
        target_path = self._get_safe_path(internal_filename)

        hasher = hashlib.sha256()
        total_bytes = 0
        chunk_size = 64 * 1024  # 64 KiB chunks

        try:
            with open(target_path, "wb") as out_file:
                while True:
                    chunk = await upload_file.read(chunk_size)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    if total_bytes > self.max_size_bytes:
                        out_file.close()
                        # Immediately remove oversized file
                        if target_path.exists():
                            target_path.unlink()
                        raise PayloadTooLargeError(
                            f"File size exceeds maximum permitted limit of {self.max_size_bytes // (1024 * 1024)} MiB"
                        )
                    hasher.update(chunk)
                    out_file.write(chunk)

            if total_bytes == 0:
                if target_path.exists():
                    target_path.unlink()
                raise BadRequestError("Uploaded file is empty (0 bytes)", code="EMPTY_FILE")

            return str(target_path), total_bytes, hasher.hexdigest()

        except Exception:
            # Clean up on any failure
            if target_path.exists():
                try:
                    target_path.unlink()
                except Exception:
                    pass
            raise

    def delete_file(self, storage_path: str) -> bool:
        """Permanently removes a document file from private storage."""
        try:
            path = Path(storage_path).resolve()
            # Ensure path is within storage root
            path.relative_to(self.root_dir)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception:
            return False

    def get_file_path(self, storage_path: str) -> Path:
        """Returns verified Path to private storage file."""
        path = Path(storage_path).resolve()
        path.relative_to(self.root_dir)
        if not path.exists():
            raise BadRequestError("Referenced storage file not found", code="FILE_NOT_FOUND")
        return path


_storage_manager: PrivateStorageManager | None = None


def get_private_storage() -> PrivateStorageManager:
    """Returns singleton PrivateStorageManager instance."""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = PrivateStorageManager()
    return _storage_manager
