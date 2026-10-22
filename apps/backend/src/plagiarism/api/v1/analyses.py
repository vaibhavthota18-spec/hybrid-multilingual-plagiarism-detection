"""
Analyses API Router for Phase 3 Lexical Detection.
Provides endpoints to create, monitor, cancel, list, and inspect similarity analyses and findings.
"""

import os
import re
import uuid
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Response, status

from plagiarism.core.errors import BadRequestError, NotFoundError
from plagiarism.core.security import get_current_user_or_dev
from plagiarism.domain.models import (
    AnalysisJobStatus,
    AnalysisResult,
    AnalysisSummary,
    CreateAnalysisRequest,
    ReviewFindingRequest,
    ReviewFindingResponse,
    SimilarityFinding,
    SourceBreakdown,
)
from plagiarism.services.executor import get_task_executor
from plagiarism.services.hybrid_service import get_hybrid_service
from plagiarism.services.reports.report_generator import ReportGenerator
from plagiarism.storage.local_db import LocalMetadataRepository, get_local_repo

router = APIRouter(prefix="/analyses", tags=["Analyses"])


def extract_user_id(user: Any) -> str:
    if hasattr(user, "user_id"):
        return getattr(user, "user_id")
    if isinstance(user, dict):
        return user.get("user_id", "00000000-0000-0000-0000-000000000001")
    return "00000000-0000-0000-0000-000000000001"


@router.get(
    "/models/info",
    summary="Get Semantic AI Model Information",
    operation_id="getModelInfo"
)
async def get_model_information(
    current_user: Any = Depends(get_current_user_or_dev),
) -> dict[str, Any]:
    """Returns local embedding model details and execution device."""
    from plagiarism.services.semantic.provider import get_embedding_provider
    provider = get_embedding_provider()
    return provider.get_model_info()


@router.post(
    "",
    response_model=AnalysisJobStatus,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create and Enqueue Similarity Analysis",
    operation_id="createAnalysis"
)
async def create_analysis(
    req: CreateAnalysisRequest,
    sync_processing: bool = Query(False, description="Run analysis synchronously (useful for tests)"),
    current_user: Any = Depends(get_current_user_or_dev),
    repo: LocalMetadataRepository = Depends(get_local_repo)
) -> AnalysisJobStatus:
    user_id = extract_user_id(current_user)
    detection_mode = req.detection_mode or "hybrid"
    if detection_mode not in ("lexical", "semantic", "hybrid"):
        raise BadRequestError(f"Unsupported detection_mode: '{detection_mode}'; must be 'lexical', 'semantic', or 'hybrid'")

    # Validate mode parameters
    if req.mode == "direct":
        if not req.reference_document_id:
            raise BadRequestError("Direct comparison mode requires 'reference_document_id'")
    elif req.mode == "one_to_many":
        if not req.reference_document_ids or len(req.reference_document_ids) == 0:
            raise BadRequestError("One-to-many comparison mode requires 'reference_document_ids'")
        if len(req.reference_document_ids) > 50:
            raise BadRequestError("One-to-many mode supports a maximum of 50 reference documents")
    elif req.mode == "corpus":
        if not req.collection_id:
            raise BadRequestError("Corpus comparison mode requires 'collection_id'")
    else:
        raise BadRequestError(f"Unsupported comparison mode: '{req.mode}'")

    # Validate submission document exists
    sub_doc = repo.get_document(req.submission_document_id)
    if not sub_doc:
        raise NotFoundError(f"Submission document {req.submission_document_id} not found")
    if sub_doc["status"] != "completed":
        raise BadRequestError(f"Submission document is in '{sub_doc['status']}' status; must be 'completed'")

    analysis_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    # Create analysis record in SQLite
    repo.create_analysis(
        analysis_id=analysis_id,
        owner_user_id=user_id,
        submission_document_id=req.submission_document_id,
        mode=req.mode,
        reference_document_id=req.reference_document_id,
        collection_id=req.collection_id,
        detection_mode=detection_mode,
    )

    if sync_processing:
        # Run synchronously on calling thread
        hybrid_service = get_hybrid_service()
        hybrid_service.run_analysis(
            analysis_id=analysis_id,
            owner_user_id=user_id,
            submission_document_id=req.submission_document_id,
            mode=req.mode,
            detection_mode=detection_mode,
            reference_document_id=req.reference_document_id,
            reference_document_ids=req.reference_document_ids,
            collection_id=req.collection_id,
        )
    else:
        # Dispatch to queue (production RQ) or bounded thread pool (local mode)
        executor = get_task_executor()
        executor.submit_analysis(
            analysis_id=analysis_id,
            owner_user_id=user_id,
            submission_document_id=req.submission_document_id,
            mode=req.mode,
            detection_mode=detection_mode,
            reference_document_id=req.reference_document_id,
            reference_document_ids=req.reference_document_ids,
            collection_id=req.collection_id,
        )

    # Fetch recorded status
    analysis_record = repo.get_analysis(analysis_id)
    return AnalysisJobStatus(
        job_id=job_id,
        analysis_id=analysis_id,
        status=analysis_record["status"] if analysis_record else "queued",
        current_step=analysis_record.get("current_step") if analysis_record else "enqueued",
        progress_percent=analysis_record.get("progress_percent", 0) if analysis_record else 0,
        error_code=analysis_record.get("error_code") if analysis_record else None,
        error_message=analysis_record.get("error_message") if analysis_record else None,
        created_at=analysis_record["created_at"] if analysis_record else "",
        completed_at=analysis_record.get("completed_at") if analysis_record else None,
    )


@router.get(
    "",
    summary="List User Similarity Analyses",
    operation_id="listAnalyses"
)
async def list_analyses(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Any = Depends(get_current_user_or_dev),
    repo: LocalMetadataRepository = Depends(get_local_repo)
) -> dict[str, Any]:
    user_id = extract_user_id(current_user)
    records, total = repo.list_analyses(owner_user_id=user_id, limit=limit, offset=offset)

    items = [
        AnalysisSummary(
            analysis_id=r["analysis_id"],
            submission_document_id=r["submission_document_id"],
            submission_filename=r.get("submission_filename"),
            mode=r["mode"],
            detection_mode=r.get("detection_mode", "hybrid"),
            status=r["status"],
            lexical_coverage=r.get("overall_lexical_coverage_percent", 0.0),
            semantic_coverage=r.get("overall_semantic_coverage_percent", 0.0),
            net_score=r.get("net_adjusted_score_percent", 0.0),
            matched_source_count=r.get("matched_source_count", 0),
            total_findings_count=r.get("total_findings_count", 0),
            processing_time_ms=r.get("processing_time_ms"),
            created_at=r["created_at"],
        )
        for r in records
    ]

    return {
        "items": items,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    }


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResult,
    summary="Retrieve Complete Analysis Results & Findings",
    operation_id="getAnalysisResults"
)
async def get_analysis_results(
    analysis_id: str,
    current_user: dict[str, Any] = Depends(get_current_user_or_dev),
    repo: LocalMetadataRepository = Depends(get_local_repo)
) -> AnalysisResult:
    analysis = repo.get_analysis(analysis_id)
    if not analysis:
        raise NotFoundError(f"Analysis {analysis_id} not found")

    findings_raw = repo.get_analysis_findings(analysis_id)
    sources_raw = repo.get_analysis_sources(analysis_id)
    cand_meta = analysis.get("candidate_metadata") or {}
    model_meta = cand_meta.get("model_info") if isinstance(cand_meta, dict) else None

    findings = [
        SimilarityFinding(
            finding_id=f["finding_id"],
            category=f["category"],
            confidence=f["confidence"],
            submission_start_offset=f["submission_start_offset"],
            submission_end_offset=f["submission_end_offset"],
            submission_excerpt=f["submission_excerpt"],
            reference_document_id=f["reference_document_id"],
            reference_source_title=f["reference_source_title"],
            reference_start_offset=f["reference_start_offset"],
            reference_end_offset=f["reference_end_offset"],
            reference_excerpt=f["reference_excerpt"],
            reference_page_number=f.get("reference_page_number", 1) or 1,
            lexical_similarity=f.get("lexical_similarity", 1.0),
            semantic_similarity=f.get("semantic_similarity", 0.0),
            is_quoted=bool(f.get("is_quoted", False)),
            is_excluded=bool(f.get("is_excluded", False)),
            language_pair=f.get("language_pair"),
            model_name=f.get("model_name"),
            review_decision=f.get("review_decision", "unreviewed") or "unreviewed",
            reviewer_notes=f.get("reviewer_notes", "") or "",
            reviewer_updated_at=f.get("reviewer_updated_at"),
        )
        for f in findings_raw
    ]

    sources = [
        SourceBreakdown(
            reference_document_id=s["reference_document_id"],
            source_title=s["source_title"],
            matched_passage_count=s["matched_passage_count"],
            lexical_coverage_percent=s["lexical_coverage_percent"],
            semantic_coverage_percent=s.get("semantic_coverage_percent", 0.0),
        )
        for s in sources_raw
    ]

    adj_cov = analysis.get("reviewer_adjusted_coverage_percent")
    if adj_cov is None:
        adj_cov = analysis.get("hybrid_evidence_coverage_percent", analysis.get("overall_lexical_coverage_percent", 0.0))

    return AnalysisResult(
        analysis_id=analysis["analysis_id"],
        submission_document_id=analysis["submission_document_id"],
        submission_filename=analysis.get("submission_filename"),
        mode=analysis["mode"],
        detection_mode=analysis.get("detection_mode", "hybrid"),
        status=analysis["status"],
        overall_lexical_coverage_percent=analysis.get("overall_lexical_coverage_percent", 0.0),
        overall_semantic_coverage_percent=analysis.get("overall_semantic_coverage_percent", 0.0),
        net_adjusted_score_percent=analysis.get("net_adjusted_score_percent", 0.0),
        hybrid_evidence_coverage_percent=analysis.get("hybrid_evidence_coverage_percent", 0.0),
        reviewer_adjusted_coverage_percent=adj_cov,
        reviewed_findings_count=analysis.get("reviewed_findings_count", 0),
        reviewer_notes=analysis.get("reviewer_notes", ""),
        matched_source_count=analysis.get("matched_source_count", 0),
        total_findings_count=analysis.get("total_findings_count", len(findings)),
        findings=findings,
        sources=sources,
        model_metadata=model_meta,
        created_at=analysis["created_at"],
        completed_at=analysis.get("completed_at"),
    )


@router.get(
    "/{analysis_id}/status",
    response_model=AnalysisJobStatus,
    summary="Poll Analysis Job Progress",
    operation_id="getAnalysisStatus"
)
async def get_analysis_status(
    analysis_id: str,
    current_user: dict[str, Any] = Depends(get_current_user_or_dev),
    repo: LocalMetadataRepository = Depends(get_local_repo)
) -> AnalysisJobStatus:
    analysis = repo.get_analysis(analysis_id)
    if not analysis:
        raise NotFoundError(f"Analysis {analysis_id} not found")

    return AnalysisJobStatus(
        job_id=analysis_id,
        analysis_id=analysis_id,
        status=analysis["status"],
        current_step=analysis.get("current_step"),
        progress_percent=analysis.get("progress_percent", 0),
        error_code=analysis.get("error_code"),
        error_message=analysis.get("error_message"),
        created_at=analysis["created_at"],
        completed_at=analysis.get("completed_at"),
    )


@router.post(
    "/{analysis_id}/cancel",
    response_model=AnalysisJobStatus,
    summary="Cancel In-Progress Analysis Job",
    operation_id="cancelAnalysis"
)
async def cancel_analysis(
    analysis_id: str,
    current_user: dict[str, Any] = Depends(get_current_user_or_dev),
    repo: LocalMetadataRepository = Depends(get_local_repo)
) -> AnalysisJobStatus:
    analysis = repo.get_analysis(analysis_id)
    if not analysis:
        raise NotFoundError(f"Analysis {analysis_id} not found")

    if analysis["status"] in ["completed", "failed"]:
        raise BadRequestError(f"Cannot cancel analysis in '{analysis['status']}' state")

    repo.update_analysis_status(
        analysis_id=analysis_id,
        status="cancelled",
        progress_percent=analysis.get("progress_percent", 0),
        current_step="cancelled_by_user",
    )

    updated = repo.get_analysis(analysis_id)
    return AnalysisJobStatus(
        job_id=analysis_id,
        analysis_id=analysis_id,
        status="cancelled",
        current_step="cancelled_by_user",
        progress_percent=updated.get("progress_percent", 0),
        created_at=updated["created_at"],
        completed_at=updated.get("completed_at"),
    )


@router.get(
    "/{analysis_id}/findings",
    response_model=list[SimilarityFinding],
    summary="Retrieve Findings for an Analysis",
    operation_id="getAnalysisFindings"
)
async def get_analysis_findings_endpoint(
    analysis_id: str,
    current_user: dict[str, Any] = Depends(get_current_user_or_dev),
    repo: LocalMetadataRepository = Depends(get_local_repo)
) -> list[SimilarityFinding]:
    analysis = repo.get_analysis(analysis_id)
    if not analysis:
        raise NotFoundError(f"Analysis {analysis_id} not found")

    findings_raw = repo.get_analysis_findings(analysis_id)
    return [
        SimilarityFinding(
            finding_id=f["finding_id"],
            category=f["category"],
            confidence=f["confidence"],
            submission_start_offset=f["submission_start_offset"],
            submission_end_offset=f["submission_end_offset"],
            submission_excerpt=f["submission_excerpt"],
            reference_document_id=f["reference_document_id"],
            reference_source_title=f["reference_source_title"],
            reference_start_offset=f["reference_start_offset"],
            reference_end_offset=f["reference_end_offset"],
            reference_excerpt=f["reference_excerpt"],
            reference_page_number=f.get("reference_page_number", 1) or 1,
            lexical_similarity=f.get("lexical_similarity", 1.0),
            semantic_similarity=f.get("semantic_similarity", 0.0),
            is_quoted=bool(f.get("is_quoted", False)),
            is_excluded=bool(f.get("is_excluded", False)),
            language_pair=f.get("language_pair"),
            model_name=f.get("model_name"),
            review_decision=f.get("review_decision", "unreviewed") or "unreviewed",
            reviewer_notes=f.get("reviewer_notes", "") or "",
            reviewer_updated_at=f.get("reviewer_updated_at"),
        )
        for f in findings_raw
    ]


@router.patch(
    "/{analysis_id}/findings/{finding_id}/review",
    response_model=ReviewFindingResponse,
    summary="Submit Human Reviewer Decision and Notes on Finding",
    operation_id="reviewFinding"
)
async def review_finding_endpoint(
    analysis_id: str,
    finding_id: str,
    req: ReviewFindingRequest,
    current_user: Any = Depends(get_current_user_or_dev),
    repo: LocalMetadataRepository = Depends(get_local_repo),
) -> ReviewFindingResponse:
    analysis = repo.get_analysis(analysis_id)
    if not analysis:
        raise NotFoundError(f"Analysis {analysis_id} not found")

    valid_decisions = {"keep", "exclude", "quoted_cited", "needs_review", "unreviewed"}
    if req.decision not in valid_decisions:
        raise BadRequestError(f"Invalid review decision '{req.decision}'; must be one of {valid_decisions}")

    existing_finding = repo.get_finding(finding_id)
    if not existing_finding or existing_finding.get("analysis_id") != analysis_id:
        raise NotFoundError(f"Finding {finding_id} not found for analysis {analysis_id}")

    updated_raw = repo.update_finding_review(
        finding_id=finding_id,
        decision=req.decision,
        notes=req.notes,
    )
    if not updated_raw:
        raise NotFoundError(f"Failed to update finding {finding_id}")

    # Recompute reviewer adjusted coverage dynamically
    hybrid_service = get_hybrid_service()
    summary = hybrid_service.recompute_reviewer_adjusted_coverage(analysis_id)

    finding_model = SimilarityFinding(
        finding_id=updated_raw["finding_id"],
        category=updated_raw["category"],
        confidence=updated_raw["confidence"],
        submission_start_offset=updated_raw["submission_start_offset"],
        submission_end_offset=updated_raw["submission_end_offset"],
        submission_excerpt=updated_raw["submission_excerpt"],
        reference_document_id=updated_raw["reference_document_id"],
        reference_source_title=updated_raw["reference_source_title"],
        reference_start_offset=updated_raw["reference_start_offset"],
        reference_end_offset=updated_raw["reference_end_offset"],
        reference_excerpt=updated_raw["reference_excerpt"],
        reference_page_number=updated_raw.get("reference_page_number", 1) or 1,
        lexical_similarity=updated_raw.get("lexical_similarity", 1.0),
        semantic_similarity=updated_raw.get("semantic_similarity", 0.0),
        is_quoted=bool(updated_raw.get("is_quoted", False)),
        is_excluded=bool(updated_raw.get("is_excluded", False)),
        language_pair=updated_raw.get("language_pair"),
        model_name=updated_raw.get("model_name"),
        review_decision=updated_raw.get("review_decision", "unreviewed"),
        reviewer_notes=updated_raw.get("reviewer_notes", ""),
        reviewer_updated_at=updated_raw.get("reviewer_updated_at"),
    )

    return ReviewFindingResponse(
        finding=finding_model,
        analysis_id=analysis_id,
        original_evidence_coverage_percent=summary["original_evidence_coverage_percent"],
        reviewer_adjusted_coverage_percent=summary["reviewer_adjusted_coverage_percent"],
        reviewed_findings_count=summary["reviewed_findings_count"],
        total_findings_count=summary["total_findings_count"],
        status_counts=summary["status_counts"],
    )


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an Analysis and Associated Findings",
    operation_id="deleteAnalysis"
)
async def delete_analysis_endpoint(
    analysis_id: str,
    current_user: Any = Depends(get_current_user_or_dev),
    repo: LocalMetadataRepository = Depends(get_local_repo)
) -> None:
    analysis = repo.get_analysis(analysis_id)
    if not analysis:
        raise NotFoundError(f"Analysis {analysis_id} not found")
    repo.delete_analysis(analysis_id)
    return None


@router.get(
    "/{analysis_id}/report",
    summary="Get or Download Analysis Report (PDF, HTML, JSON)",
    operation_id="getAnalysisReport"
)
async def get_analysis_report(
    analysis_id: str,
    format: str = Query("json", description="Report format: 'pdf', 'html', or 'json'"),
    include_notes: bool = Query(True),
    language: str = Query("en"),
    current_user: dict[str, Any] = Depends(get_current_user_or_dev),
    repo: LocalMetadataRepository = Depends(get_local_repo)
) -> Any:
    analysis = repo.get_analysis(analysis_id)
    if not analysis:
        raise NotFoundError(f"Analysis {analysis_id} not found")

    findings = repo.get_analysis_findings(analysis_id)
    sources = repo.get_analysis_sources(analysis_id)
    doc_meta = repo.get_document(analysis.get("submission_document_id")) if analysis.get("submission_document_id") else None

    # Construct safe, human-readable filename (e.g. AOA_Syllabus_Similarity_Report.pdf)
    sub_name = analysis.get("submission_filename") or (doc_meta.get("filename") if doc_meta else None) or "Document"
    base_name = os.path.splitext(sub_name)[0]
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base_name).strip('_')
    if not clean_name:
        clean_name = f"Similarity_Report_{analysis_id[:8]}"
    else:
        clean_name = f"{clean_name}_Similarity_Report"

    fmt = format.lower()
    if fmt == "pdf":
        pdf_bytes = ReportGenerator.generate_pdf_report(
            analysis=analysis,
            findings=findings,
            sources=sources,
            include_notes=include_notes,
            doc_meta=doc_meta,
        )
        dl_filename = f"{clean_name}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{dl_filename}"; filename*=UTF-8\'\'{quote(dl_filename)}',
                "Content-Type": "application/pdf",
                "Cache-Control": "no-cache",
            },
        )
    elif fmt == "html":
        html_str = ReportGenerator.generate_html_report(
            analysis=analysis,
            findings=findings,
            sources=sources,
            include_notes=include_notes,
            doc_meta=doc_meta,
        )
        dl_filename = f"{clean_name}.html"
        return Response(
            content=html_str,
            media_type="text/html; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{dl_filename}"; filename*=UTF-8\'\'{quote(dl_filename)}',
                "Content-Type": "text/html; charset=utf-8",
                "Cache-Control": "no-cache",
            },
        )
    else:
        json_data = ReportGenerator.generate_json_report(
            analysis=analysis,
            findings=findings,
            sources=sources,
            include_notes=include_notes,
            doc_meta=doc_meta,
        )
        dl_filename = f"{clean_name}.json"
        import json as json_lib
        return Response(
            content=json_lib.dumps(json_data, indent=2, ensure_ascii=False).encode("utf-8"),
            media_type="application/json; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{dl_filename}"; filename*=UTF-8\'\'{quote(dl_filename)}',
                "Content-Type": "application/json; charset=utf-8",
                "Cache-Control": "no-cache",
            },
        )
