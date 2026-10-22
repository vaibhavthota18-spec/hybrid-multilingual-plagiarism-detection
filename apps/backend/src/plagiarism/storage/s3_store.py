"""
Production S3 and MinIO Compatible Object Storage Backend
Supports AWS S3, Cloudflare R2, MinIO, and other S3-compatible cloud object storage providers.
"""

import hashlib
import io
import logging
import os
from pathlib import Path

from fastapi import UploadFile

from plagiarism.core.config import get_settings
from plagiarism.core.errors import BadRequestError, PayloadTooLargeError

logger = logging.getLogger(__name__)


class S3StorageManager:
    """
    Manages private object storage in S3-compatible services.
    Enforces bucket separation, encryption at rest, and size validation.
    """

    def __init__(self):
        self.settings = get_settings()
        self.bucket = os.getenv("S3_BUCKET_NAME", "plagiarism-platform-private")
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL")
        self.region = os.getenv("S3_REGION_NAME", "us-east-1")
        self.access_key = os.getenv("S3_ACCESS_KEY_ID")
        self.secret_key = os.getenv("S3_SECRET_ACCESS_KEY")
        self.max_size_bytes = self.settings.MAX_UPLOAD_SIZE_BYTES
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    "s3",
                    endpoint_url=self.endpoint_url,
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                )
            except ImportError:
                raise RuntimeError("boto3 package required for S3 object storage backend")
        return self._client

    async def save_upload_file(
        self,
        upload_file: UploadFile,
        document_id: str,
        extension: str
    ) -> tuple[str, int, str]:
        """
        Streams an uploaded file directly to S3 private bucket.
        Returns: (s3_uri, total_bytes_written, sha256_hex_digest)
        """
        if not extension.startswith("."):
            extension = f".{extension}"

        key = f"documents/{document_id}{extension}"
        client = self._get_client()

        hasher = hashlib.sha256()
        buffer = io.BytesIO()
        total_bytes = 0
        chunk_size = 64 * 1024

        while True:
            chunk = await upload_file.read(chunk_size)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > self.max_size_bytes:
                raise PayloadTooLargeError(
                    f"File size exceeds maximum permitted limit of {self.max_size_bytes // (1024 * 1024)} MiB"
                )
            hasher.update(chunk)
            buffer.write(chunk)

        if total_bytes == 0:
            raise BadRequestError("Uploaded file is empty (0 bytes)", code="EMPTY_FILE")

        buffer.seek(0)
        client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=buffer.getvalue(),
            ContentType=upload_file.content_type or "application/octet-stream",
            ServerSideEncryption="AES256"
        )

        return f"s3://{self.bucket}/{key}", total_bytes, hasher.hexdigest()

    def download_file_to_temp(self, s3_uri: str, target_local_path: Path) -> Path:
        """Downloads object from S3 URI to local cache directory for extraction."""
        client = self._get_client()
        parts = s3_uri.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        target_local_path.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(bucket, key, str(target_local_path))
        return target_local_path

    def delete_file(self, s3_uri: str) -> bool:
        """Permanently deletes object from S3."""
        try:
            client = self._get_client()
            parts = s3_uri.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1]
            client.delete_object(Bucket=bucket, Key=key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete S3 object {s3_uri}: {e}")
            return False
