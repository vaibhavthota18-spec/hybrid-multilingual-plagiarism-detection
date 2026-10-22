"""
Reference Collections (Corpus) API Routes
Implements OpenAPI contracts for /collections creation, listing, membership, and management.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from plagiarism.core.errors import NotFoundError
from plagiarism.core.security import UserPrincipal, get_current_user_or_dev
from plagiarism.storage.local_db import get_local_repo

router = APIRouter(prefix="/collections", tags=["Collections"])


class CreateCollectionRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=120, description="Collection name")
    description: str | None = Field(None, max_length=1000, description="Optional collection description")
    is_public_within_tenant: bool = Field(False, description="Whether collection is visible to tenant peers")


class AddDocumentToCollectionRequest(BaseModel):
    document_id: str = Field(..., description="ID of existing uploaded document to link into collection")


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a Reference Collection (Corpus)",
    operation_id="createCollection"
)
async def create_collection(
    request: CreateCollectionRequest,
    user: UserPrincipal = Depends(get_current_user_or_dev)
) -> dict[str, Any]:
    """Creates a new private reference collection for group-based plagiarism analysis."""
    repo = get_local_repo()
    collection_id = str(uuid.uuid4())

    collection = repo.create_collection(
        collection_id=collection_id,
        name=request.name.strip(),
        description=request.description,
        owner_user_id=user.user_id,
        is_public_within_tenant=request.is_public_within_tenant
    )

    return {
        "collection_id": collection["id"],
        "name": collection["name"],
        "description": collection.get("description", ""),
        "document_count": collection.get("document_count", 0),
        "is_public_within_tenant": collection.get("is_public_within_tenant", False),
        "created_at": collection["created_at"]
    }


@router.get(
    "",
    summary="List Authorized Reference Collections",
    operation_id="listCollections"
)
async def list_collections(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserPrincipal = Depends(get_current_user_or_dev)
) -> dict[str, Any]:
    """Lists reference collections owned by or shared with the authenticated user."""
    repo = get_local_repo()
    items, total = repo.list_collections(owner_user_id=user.user_id, limit=limit, offset=offset)

    return {
        "items": [
            {
                "collection_id": c["id"],
                "name": c["name"],
                "description": c.get("description", ""),
                "document_count": c.get("document_count", 0),
                "is_public_within_tenant": c.get("is_public_within_tenant", False),
                "created_at": c["created_at"]
            }
            for c in items
        ],
        "pagination": {
            "total_items": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(items)) < total
        }
    }


@router.get(
    "/{collection_id}",
    summary="Get Collection Details",
    operation_id="getCollection"
)
async def get_collection(
    collection_id: str,
    user: UserPrincipal = Depends(get_current_user_or_dev)
) -> dict[str, Any]:
    """Retrieves metadata and document statistics for a specific reference collection."""
    repo = get_local_repo()
    col = repo.get_collection(collection_id)
    if not col:
        raise NotFoundError(f"Collection with ID '{collection_id}' not found")

    return {
        "collection_id": col["id"],
        "name": col["name"],
        "description": col.get("description", ""),
        "document_count": col.get("document_count", 0),
        "is_public_within_tenant": col.get("is_public_within_tenant", False),
        "created_at": col["created_at"]
    }


@router.get(
    "/{collection_id}/documents",
    summary="List Documents in Reference Collection",
    operation_id="listCollectionDocuments"
)
async def list_collection_documents(
    collection_id: str,
    user: UserPrincipal = Depends(get_current_user_or_dev)
) -> dict[str, Any]:
    """Lists all source documents currently indexed within a reference collection."""
    repo = get_local_repo()
    col = repo.get_collection(collection_id)
    if not col:
        raise NotFoundError(f"Collection with ID '{collection_id}' not found")

    docs = repo.list_collection_documents(collection_id)
    return {
        "collection_id": collection_id,
        "collection_name": col["name"],
        "total_documents": len(docs),
        "documents": [
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
                "status": d.get("status", "completed"),
                "indexed_at": d.get("collection_indexed_at", d["created_at"])
            }
            for d in docs
        ]
    }


@router.post(
    "/{collection_id}/documents",
    status_code=status.HTTP_201_CREATED,
    summary="Add Document to Reference Collection",
    operation_id="addDocumentToCollection"
)
async def add_document_to_collection(
    collection_id: str,
    request: AddDocumentToCollectionRequest,
    user: UserPrincipal = Depends(get_current_user_or_dev)
) -> dict[str, Any]:
    """Links an existing processed document into a reference collection."""
    repo = get_local_repo()
    col = repo.get_collection(collection_id)
    if not col:
        raise NotFoundError(f"Collection with ID '{collection_id}' not found")

    doc = repo.get_document(request.document_id)
    if not doc:
        raise NotFoundError(f"Document with ID '{request.document_id}' not found")

    repo.add_document_to_collection(collection_id, request.document_id)
    updated_col = repo.get_collection(collection_id) or col

    return {
        "status": "success",
        "message": f"Document '{doc['filename']}' linked to collection '{col['name']}'",
        "collection_id": collection_id,
        "document_id": request.document_id,
        "document_count": updated_col.get("document_count", 0)
    }


@router.delete(
    "/{collection_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Document from Reference Collection",
    operation_id="removeDocumentFromCollection"
)
async def remove_document_from_collection(
    collection_id: str,
    document_id: str,
    user: UserPrincipal = Depends(get_current_user_or_dev)
) -> None:
    """Removes a document from a reference collection (does not delete the document itself)."""
    repo = get_local_repo()
    col = repo.get_collection(collection_id)
    if not col:
        raise NotFoundError(f"Collection with ID '{collection_id}' not found")

    removed = repo.remove_document_from_collection(collection_id, document_id)
    if not removed:
        raise NotFoundError(f"Document '{document_id}' is not a member of collection '{collection_id}'")
    return None
