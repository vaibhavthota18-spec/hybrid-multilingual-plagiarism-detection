"""
Document Ingestion & Management API Routes
Implements OpenAPI contracts for /documents upload, listing, preview, and deletion.
"""

import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from plagiarism.core.config import get_settings
from plagiarism.core.errors import BadRequestError, NotFoundError, UnsupportedMediaTypeError
from plagiarism.core.security import UserPrincipal, get_current_user_or_dev
from plagiarism.services.executor import get_executor
from plagiarism.storage.local_db import get_local_repo
from plagiarism.storage.private_store import get_private_storage, sanitize_filename

router = APIRouter(prefix="/documents", tags=["Documents"])

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Ingest a Document",
    operation_id="uploadDocument"
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (PDF, DOCX, TXT)"),
    title: Optional[str] = Form(None, description="Optional custom title for the document"),
    language_hint: str = Form("auto", description="Language hint: en, hi, te, auto"),
    user: UserPrincipal = Depends(get_current_user_or_dev),
    sync_processing: bool = Query(False, description="Process synchronously (used by tests/e2e)")
) -> Dict[str, Any]:
    """
    Uploads a document to private storage, validates structural integrity,
    and initiates asynchronous text extraction and passage segmentation.
    """
    settings = get_settings()
    repo = get_local_repo()
    storage = get_private_storage()
    executor = get_executor()

    raw_filename = file.filename or "uploaded_document.txt"
    clean_filename = sanitize_filename(raw_filename)
    _, ext = os.path.splitext(clean_filename)
    ext = ext.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedMediaTypeError(
            f"Unsupported file format '{ext}'. Allowed formats are: .pdf, .docx, .txt"
        )

    document_id = str(uuid.uuid4())
    content_type = file.content_type or "application/octet-stream"

    # Save to private filesystem storage with size enforcement
    storage_path, file_size, sha256_hash = await storage.save_upload_file(
        upload_file=file,
        document_id=document_id,
        extension=ext
    )

    # Insert metadata record into local SQLite database
    initial_status = "completed" if sync_processing else "processing"
    doc_record = repo.insert_document(
        document_id=document_id,
        owner_user_id=user.user_id,
        filename=clean_filename,
        mime_type=content_type,
        sha256_hash=sha256_hash,
        storage_path=storage_path,
        file_size_bytes=file_size,
        status=initial_status,
        title=title
    )

    # Execute processing
    if sync_processing:
        executor.process_document_sync(
            document_id=document_id,
            storage_path=storage_path,
            extension=ext,
            language_hint=language_hint
        )
        doc_record = repo.get_document(document_id) or doc_record
    else:
        executor.submit_document_processing(
            document_id=document_id,
            storage_path=storage_path,
            extension=ext,
            language_hint=language_hint
        )

    return {
        "document_id": doc_record.get("document_id"),
        "filename": doc_record.get("filename"),
        "mime_type": doc_record.get("mime_type"),
        "sha256_hash": doc_record.get("sha256_hash"),
        "file_size_bytes": doc_record.get("file_size_bytes"),
        "page_count": doc_record.get("page_count", 1),
        "char_count": doc_record.get("char_count", 0),
        "word_count": doc_record.get("word_count", 0),
        "detected_language": doc_record.get("detected_language", "en"),
        "status": doc_record.get("status", "processing"),
        "created_at": doc_record.get("created_at"),
        "title": doc_record.get("title")
    }


@router.get(
    "",
    summary="List User's Uploaded Documents",
    operation_id="listDocuments"
)
async def list_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserPrincipal = Depends(get_current_user_or_dev)
) -> Dict[str, Any]:
    """Lists uploaded documents belonging to the authenticated user."""
    repo = get_local_repo()
    items, total = repo.list_documents(owner_user_id=user.user_id, limit=limit, offset=offset)

    return {
        "items": [
            {
                "document_id": d["document_id"],
                "filename": d["filename"],
                "mime_type": d["mime_type"],
                "sha256_hash": d["sha256_hash"],
                "file_size_bytes": d["file_size_bytes"],
                "page_count": d.get("page_count", 1),
                "char_count": d.get("char_count", 0),
                "word_count": d.get("word_count", 0),
                "detected_language": d.get("detected_language", "en"),
                "status": d.get("status", "queued"),
                "created_at": d["created_at"],
                "title": d.get("title")
            }
            for d in items
        ],
        "pagination": {
            "total_items": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(items)) < total
        }
    }


@router.get(
    "/{document_id}",
    summary="Get Document Metadata & Extraction State",
    operation_id="getDocument"
)
async def get_document(
    document_id: str,
    user: UserPrincipal = Depends(get_current_user_or_dev)
) -> Dict[str, Any]:
    """Retrieves document metadata, page counts, word counts, and extraction status."""
    repo = get_local_repo()
    doc = repo.get_document(document_id)
    if not doc:
        raise NotFoundError(f"Document with ID '{document_id}' not found")

    return {
        "document_id": doc["document_id"],
        "filename": doc["filename"],
        "mime_type": doc["mime_type"],
        "sha256_hash": doc["sha256_hash"],
        "file_size_bytes": doc["file_size_bytes"],
        "page_count": doc.get("page_count", 1),
        "char_count": doc.get("char_count", 0),
        "word_count": doc.get("word_count", 0),
        "detected_language": doc.get("detected_language", "en"),
        "status": doc.get("status", "queued"),
        "created_at": doc["created_at"],
        "title": doc.get("title"),
        "warnings": doc.get("processing_warnings")
    }


@router.get(
    "/{document_id}/text",
    summary="Preview Extracted Document Text",
    operation_id="getDocumentTextPreview"
)
async def get_document_text_preview(
    document_id: str,
    user: UserPrincipal = Depends(get_current_user_or_dev)
) -> Dict[str, Any]:
    """Retrieves raw extracted text and character metrics for UI preview."""
    repo = get_local_repo()
    doc = repo.get_document(document_id)
    if not doc:
        raise NotFoundError(f"Document with ID '{document_id}' not found")

    return {
        "document_id": doc["document_id"],
        "filename": doc["filename"],
        "status": doc.get("status", "queued"),
        "char_count": doc.get("char_count", 0),
        "word_count": doc.get("word_count", 0),
        "detected_language": doc.get("detected_language", "en"),
        "raw_text": doc.get("raw_text", ""),
        "warnings": doc.get("processing_warnings")
    }


@router.get(
    "/{document_id}/passages",
    summary="List Segmented Document Passages",
    operation_id="getDocumentPassages"
)
async def get_document_passages(
    document_id: str,
    user: UserPrincipal = Depends(get_current_user_or_dev)
) -> Dict[str, Any]:
    """Retrieves deterministic passage segments and code-point offsets."""
    repo = get_local_repo()
    doc = repo.get_document(document_id)
    if not doc:
        raise NotFoundError(f"Document with ID '{document_id}' not found")

    passages = repo.get_passages(document_id)
    return {
        "document_id": document_id,
        "filename": doc["filename"],
        "total_passages": len(passages),
        "passages": passages
    }


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hard Delete Document and Derived Data",
    operation_id="deleteDocument"
)
async def delete_document(
    document_id: str,
    user: UserPrincipal = Depends(get_current_user_or_dev)
) -> None:
    """Permanently deletes document file from private storage, passages, and database records."""
    repo = get_local_repo()
    storage = get_private_storage()

    doc = repo.get_document(document_id)
    if not doc:
        raise NotFoundError(f"Document with ID '{document_id}' not found")

    # 1. Remove file from disk
    storage_path = doc.get("storage_path")
    if storage_path:
        storage.delete_file(storage_path)

    # 2. Remove from database (cascades passages and collection memberships)
    repo.delete_document(document_id)
    return None
