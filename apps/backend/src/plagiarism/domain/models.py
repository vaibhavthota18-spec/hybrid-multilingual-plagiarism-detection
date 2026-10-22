"""
Domain Models and Enums
Adheres to Phase 0 contracts and terminology
"""

from enum import Enum

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
    version: str | None = Field(default="0.1.0", description="API version")


class DetectionMode(str, Enum):
    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class CreateAnalysisRequest(BaseModel):
    submission_document_id: str = Field(..., description="UUID of the submission document")
    mode: str = Field(..., description="Comparison mode: direct, one_to_many, or corpus")
    detection_mode: str | None = Field(default="hybrid", description="Detection mode: lexical, semantic, or hybrid")
    reference_document_id: str | None = Field(None, description="Required for direct mode")
    reference_document_ids: list[str] | None = Field(None, description="Required for one_to_many mode")
    collection_id: str | None = Field(None, description="Required for corpus mode")
    exclude_citations: bool = Field(True, description="Exclude quoted and cited regions")
    exclude_references: bool = Field(True, description="Exclude reference bibliography lists")


class AnalysisJobStatus(BaseModel):
    job_id: str
    analysis_id: str
    status: str
    current_step: str | None = None
    progress_percent: int = 0
    error_code: str | None = None
    error_message: str | None = None
    created_at: str
    completed_at: str | None = None


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
    reference_page_number: int | None = 1
    lexical_similarity: float = 1.0
    semantic_similarity: float = 0.0
    is_quoted: bool = False
    is_excluded: bool = False
    language_pair: str | None = None
    model_name: str | None = None
    review_decision: str | None = "unreviewed"
    reviewer_notes: str | None = ""
    reviewer_updated_at: str | None = None


class ReviewFindingRequest(BaseModel):
    decision: str = Field(..., description="Review decision: 'keep', 'exclude', 'quoted_cited', 'needs_review', or 'unreviewed'")
    notes: str | None = Field(None, description="Optional reviewer notes or rationale")


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
    submission_filename: str | None = None
    mode: str
    detection_mode: str = "hybrid"
    status: str = "completed"
    overall_lexical_coverage_percent: float = 0.0
    overall_semantic_coverage_percent: float = 0.0
    net_adjusted_score_percent: float = 0.0
    hybrid_evidence_coverage_percent: float = 0.0
    reviewer_adjusted_coverage_percent: float | None = None
    reviewed_findings_count: int | None = 0
    reviewer_notes: str | None = ""
    matched_source_count: int = 0
    total_findings_count: int = 0
    findings: list[SimilarityFinding] = []
    sources: list[SourceBreakdown] = []
    model_metadata: dict | None = None
    created_at: str | None = None
    completed_at: str | None = None


class AnalysisSummary(BaseModel):
    analysis_id: str
    submission_document_id: str
    submission_filename: str | None = None
    mode: str
    detection_mode: str = "hybrid"
    status: str
    lexical_coverage: float = 0.0
    semantic_coverage: float = 0.0
    net_score: float = 0.0
    matched_source_count: int = 0
    total_findings_count: int = 0
    processing_time_ms: int | None = None
    created_at: str


