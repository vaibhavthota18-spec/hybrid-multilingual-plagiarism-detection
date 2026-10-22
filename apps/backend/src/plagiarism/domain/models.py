"""
Domain Models and Enums
Adheres to Phase 0 contracts and terminology
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    GUEST = "GUEST"
    STUDENT = "STUDENT"
    RESEARCHER = "RESEARCHER"
    EDUCATOR = "EDUCATOR"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"


class ComparisonMode(str, Enum):
    DIRECT = "direct"
    ONE_TO_MANY = "one_to_many"
    CORPUS = "corpus"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MatchCategory(str, Enum):
    EXACT_COPY = "exact_copy"
    NEAR_EXACT_REWRITE = "near_exact_rewrite"
    PARAPHRASE = "paraphrase"
    POTENTIAL_TRANSLATION = "potential_translation"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class ReviewLabel(str, Enum):
    VALID_CITATION = "VALID_CITATION"
    SUSPECTED_PLAGIARISM = "SUSPECTED_PLAGIARISM"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    IGNORED = "IGNORED"


class HealthStatus(BaseModel):
    """
    Matches contracts/openapi.yaml HealthStatus schema
    """
    status: str = Field(default="healthy", examples=["healthy"])
    timestamp: str = Field(description="ISO-8601 formatted UTC timestamp")
    database: str = Field(default="connected", examples=["connected"])
    redis: str = Field(default="connected", examples=["connected"])
    worker_pool: str = Field(default="operational", examples=["operational"])
    version: Optional[str] = Field(default="0.1.0", description="API version")


class DetectionMode(str, Enum):
    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class CreateAnalysisRequest(BaseModel):
    submission_document_id: str = Field(..., description="UUID of the submission document")
    mode: str = Field(..., description="Comparison mode: direct, one_to_many, or corpus")
    detection_mode: Optional[str] = Field(default="hybrid", description="Detection mode: lexical, semantic, or hybrid")
    reference_document_id: Optional[str] = Field(None, description="Required for direct mode")
    reference_document_ids: Optional[list[str]] = Field(None, description="Required for one_to_many mode")
    collection_id: Optional[str] = Field(None, description="Required for corpus mode")
    exclude_citations: bool = Field(True, description="Exclude quoted and cited regions")
    exclude_references: bool = Field(True, description="Exclude reference bibliography lists")


class AnalysisJobStatus(BaseModel):
    job_id: str
    analysis_id: str
    status: str
    current_step: Optional[str] = None
    progress_percent: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class SimilarityFinding(BaseModel):
    finding_id: str
    category: str
    confidence: str
    submission_start_offset: int
    submission_end_offset: int
    submission_excerpt: str
    reference_document_id: str
    reference_source_title: str
    reference_start_offset: int
    reference_end_offset: int
    reference_excerpt: str
    reference_page_number: Optional[int] = 1
    lexical_similarity: float = 1.0
    semantic_similarity: float = 0.0
    is_quoted: bool = False
    is_excluded: bool = False
    language_pair: Optional[str] = None
    model_name: Optional[str] = None
    review_decision: Optional[str] = "unreviewed"
    reviewer_notes: Optional[str] = ""
    reviewer_updated_at: Optional[str] = None


class ReviewFindingRequest(BaseModel):
    decision: str = Field(..., description="Review decision: 'keep', 'exclude', 'quoted_cited', 'needs_review', or 'unreviewed'")
    notes: Optional[str] = Field(None, description="Optional reviewer notes or rationale")


class ReviewFindingResponse(BaseModel):
    finding: SimilarityFinding
    analysis_id: str
    original_evidence_coverage_percent: float
    reviewer_adjusted_coverage_percent: float
    reviewed_findings_count: int
    total_findings_count: int
    status_counts: dict[str, int]


class SourceBreakdown(BaseModel):
    reference_document_id: str
    source_title: str
    matched_passage_count: int
    lexical_coverage_percent: float
    semantic_coverage_percent: float = 0.0


class AnalysisResult(BaseModel):
    analysis_id: str
    submission_document_id: str
    submission_filename: Optional[str] = None
    mode: str
    detection_mode: str = "hybrid"
    status: str = "completed"
    overall_lexical_coverage_percent: float = 0.0
    overall_semantic_coverage_percent: float = 0.0
    net_adjusted_score_percent: float = 0.0
    hybrid_evidence_coverage_percent: float = 0.0
    reviewer_adjusted_coverage_percent: Optional[float] = None
    reviewed_findings_count: Optional[int] = 0
    reviewer_notes: Optional[str] = ""
    matched_source_count: int = 0
    total_findings_count: int = 0
    findings: list[SimilarityFinding] = []
    sources: list[SourceBreakdown] = []
    model_metadata: Optional[dict] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class AnalysisSummary(BaseModel):
    analysis_id: str
    submission_document_id: str
    submission_filename: Optional[str] = None
    mode: str
    detection_mode: str = "hybrid"
    status: str
    lexical_coverage: float = 0.0
    semantic_coverage: float = 0.0
    net_score: float = 0.0
    matched_source_count: int = 0
    total_findings_count: int = 0
    processing_time_ms: Optional[int] = None
    created_at: str


