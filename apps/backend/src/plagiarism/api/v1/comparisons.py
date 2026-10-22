"""
Comparison Input Preparation API Routes
Validates submission and reference documents for Direct, One-to-Many, and Corpus modes.
Enforces Phase 2 boundaries: verifies readiness without executing Phase 3 similarity analysis.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from plagiarism.core.errors import BadRequestError, NotFoundError
from plagiarism.core.security import UserPrincipal, get_current_user_or_dev
from plagiarism.storage.local_db import get_local_repo

router = APIRouter(prefix="/comparisons", tags=["Comparisons"])


class ValidateComparisonRequest(BaseModel):
    submission_document_id: str = Field(..., description="ID of candidate submission document")
    mode: str = Field(..., description="Comparison mode: 'direct', 'one_to_many', or 'corpus'")
    reference_document_id: Optional[str] = Field(None, description="Required for 'direct' mode")
    reference_document_ids: Optional[List[str]] = Field(None, description="Required for 'one_to_many' mode")
    collection_id: Optional[str] = Field(None, description="Required for 'corpus' mode")


@router.post(
    "/validate",
    status_code=status.HTTP_200_OK,
    summary="Validate Comparison Inputs and Check Phase 3 Readiness",
    operation_id="validateComparisonInputs"
)
async def validate_comparison_inputs(
    request: ValidateComparisonRequest,
    user: UserPrincipal = Depends(get_current_user_or_dev)
) -> Dict[str, Any]:
    """
    Validates selected submission and reference inputs across comparison modes:
    - Direct (1:1)
    - One-to-Many (1:N)
    - Corpus (1:Collection)

    Ensures all documents are processed and valid. Does NOT compute similarity (Phase 3 boundary).
    """
    repo = get_local_repo()

    # 1. Validate submission document
    sub_doc = repo.get_document(request.submission_document_id)
    if not sub_doc:
        raise NotFoundError(f"Submission document '{request.submission_document_id}' not found")

    if sub_doc.get("status") != "completed":
        raise BadRequestError(
            f"Submission document '{sub_doc['filename']}' is not ready for analysis (status: {sub_doc.get('status')})",
            code="DOCUMENT_NOT_READY"
        )

    mode = request.mode.lower()
    references_summary = []

    # 2. Validate by mode
    if mode == "direct":
        if not request.reference_document_id:
            raise BadRequestError("Direct comparison mode requires 'reference_document_id'", code="MISSING_REFERENCE")
        
        if request.reference_document_id == request.submission_document_id:
            raise BadRequestError("Submission document and reference document cannot be the identical file", code="SELF_COMPARISON")

        ref_doc = repo.get_document(request.reference_document_id)
        if not ref_doc:
            raise NotFoundError(f"Reference document '{request.reference_document_id}' not found")

        if ref_doc.get("status") != "completed":
            raise BadRequestError(
                f"Reference document '{ref_doc['filename']}' is not ready for analysis (status: {ref_doc.get('status')})",
                code="DOCUMENT_NOT_READY"
            )

        references_summary.append({
            "document_id": ref_doc["document_id"],
            "filename": ref_doc["filename"],
            "char_count": ref_doc.get("char_count", 0),
            "detected_language": ref_doc.get("detected_language", "en")
        })

    elif mode == "one_to_many":
        ref_ids = request.reference_document_ids or []
        if not ref_ids:
            raise BadRequestError("One-to-many comparison mode requires at least one 'reference_document_id'", code="MISSING_REFERENCE")

        # Check for duplicates
        if len(ref_ids) != len(set(ref_ids)):
            raise BadRequestError("Duplicate reference document IDs detected in request", code="DUPLICATE_REFERENCE")

        if request.submission_document_id in ref_ids:
            raise BadRequestError("Submission document cannot be included in reference list", code="SELF_COMPARISON")

        for rid in ref_ids:
            rd = repo.get_document(rid)
            if not rd:
                raise NotFoundError(f"Reference document '{rid}' not found")
            if rd.get("status") != "completed":
                raise BadRequestError(
                    f"Reference document '{rd['filename']}' is not ready for analysis (status: {rd.get('status')})",
                    code="DOCUMENT_NOT_READY"
                )
            references_summary.append({
                "document_id": rd["document_id"],
                "filename": rd["filename"],
                "char_count": rd.get("char_count", 0),
                "detected_language": rd.get("detected_language", "en")
            })

    elif mode == "corpus":
        if not request.collection_id:
            raise BadRequestError("Corpus comparison mode requires 'collection_id'", code="MISSING_COLLECTION")

        col = repo.get_collection(request.collection_id)
        if not col:
            raise NotFoundError(f"Reference collection '{request.collection_id}' not found")

        col_docs = repo.list_collection_documents(request.collection_id)
        if not col_docs:
            raise BadRequestError(f"Reference collection '{col['name']}' is empty (contains 0 documents)", code="EMPTY_COLLECTION")

        for cd in col_docs:
            if cd["document_id"] != request.submission_document_id:
                references_summary.append({
                    "document_id": cd["document_id"],
                    "filename": cd["filename"],
                    "char_count": cd.get("char_count", 0),
                    "detected_language": cd.get("detected_language", "en")
                })

    else:
        raise BadRequestError(
            f"Invalid comparison mode '{request.mode}'. Permitted modes are: 'direct', 'one_to_many', 'corpus'",
            code="INVALID_MODE"
        )

    return {
        "status": "ready",
        "mode": mode,
        "submission_document": {
            "document_id": sub_doc["document_id"],
            "filename": sub_doc["filename"],
            "char_count": sub_doc.get("char_count", 0),
            "word_count": sub_doc.get("word_count", 0),
            "detected_language": sub_doc.get("detected_language", "en")
        },
        "reference_count": len(references_summary),
        "references": references_summary,
        "message": "Documents are ready for analysis. Similarity detection will be implemented in Phase 3.",
        "phase_boundary_status": "Phase 2 Complete — Ready for Phase 3 Detection Core"
    }
