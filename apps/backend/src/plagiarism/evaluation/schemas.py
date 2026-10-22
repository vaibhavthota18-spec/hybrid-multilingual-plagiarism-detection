"""
Pydantic v2 Schemas and Dataclasses for Phase 5 Scientific Evaluation.
Defines versioned dataset structures, split partitions, metric containers,
and reproducible evaluation reports.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PlagiarismCategory(str, Enum):
    EXACT = "exact"
    NEAR_EXACT = "near_exact"
    PARAPHRASE = "paraphrase"
    TRANSLATION = "translation"
    HARD_NEGATIVE = "hard_negative"
    UNRELATED_CONTROL = "unrelated_control"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SplitPartition(str, Enum):
    CALIBRATION = "calibration"
    HELD_OUT_EVALUATION = "held_out_evaluation"


class GroundTruthSpan(BaseModel):
    start_char: int = Field(..., description="0-indexed start character offset in suspicious text")
    end_char: int = Field(..., description="0-indexed end character offset in suspicious text")
    text: str = Field(..., description="Exact matched substring within suspicious text")
    language: str = Field(..., description="ISO 639-1 language code (en, hi, te)")
    label: str = Field(default="plagiarized", description="Semantic annotation label")


class EvaluationExample(BaseModel):
    id: str = Field(..., description="Unique example identifier (e.g., EVAL-CALIB-01, EVAL-TEST-01)")
    suspicious_text: str = Field(..., description="The query/suspicious text submitted for analysis")
    source_text: str = Field(..., description="The reference source text in repository")
    suspicious_language: str = Field(..., description="Language code of suspicious text (en, hi, te)")
    source_language: str = Field(..., description="Language code of source text (en, hi, te)")
    plagiarism_type: PlagiarismCategory = Field(..., description="Plagiarism category or negative type")
    is_plagiarism: bool = Field(..., description="Binary ground-truth label: True if plagiarized, False if non-plagiarized")
    difficulty: DifficultyLevel = Field(..., description="Difficulty rating for benchmark assessment")
    domain: str = Field(..., description="Knowledge domain (e.g., computer_science, climate, medicine)")
    provenance: str = Field(..., description="Dataset provenance or reference source metadata")
    split: SplitPartition = Field(..., description="Data partition: calibration or held_out_evaluation")
    ground_truth_spans: list[GroundTruthSpan] = Field(default_factory=list, description="Ground truth suspicious spans")
    rationale: str = Field(..., description="Detailed annotation rationale and expected detector behavior")


class EvaluationDataset(BaseModel):
    dataset_id: str = Field(..., description="Dataset identifier")
    version: str = Field(..., description="Semantic version string (e.g., 1.0.0)")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    description: str = Field(..., description="Comprehensive dataset overview and design goals")
    languages: list[str] = Field(default_factory=lambda: ["en", "hi", "te"])
    examples: list[EvaluationExample] = Field(..., description="List of evaluation examples")


class PredictionSpan(BaseModel):
    start_char: int
    end_char: int
    excerpt: str
    confidence: float
    category: str


class PredictionResult(BaseModel):
    example_id: str
    predicted_is_plagiarism: bool
    similarity_score: float
    predicted_spans: list[PredictionSpan] = Field(default_factory=list)
    latency_ms: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class WilsonInterval(BaseModel):
    point_estimate: float
    lower_bound: float
    upper_bound: float
    confidence_level: float = 0.95


class ClassificationMetrics(BaseModel):
    tp: int
    fp: int
    tn: int
    fn: int
    total: int
    precision: float
    recall: float
    f1: float
    specificity: float
    fpr: float
    fnr: float
    balanced_accuracy: float
    confusion_matrix: dict[str, int]
    precision_wilson_ci: WilsonInterval
    recall_wilson_ci: WilsonInterval
    f1_wilson_ci: WilsonInterval | None = None


class RetrievalMetrics(BaseModel):
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    mrr: float
    map_score: float
    mean_latency_ms: float
    candidate_pool_size: int
    queries_evaluated: int


class LocalizationMetrics(BaseModel):
    char_iou: float
    token_iou: float
    span_precision: float
    span_recall: float
    span_f1: float
    mean_boundary_error_chars: float
    evaluated_positive_pairs: int


class BootstrapConfidenceInterval(BaseModel):
    metric_name: str
    point_estimate: float
    lower_bound: float
    upper_bound: float
    confidence_level: float = 0.95
    bootstrap_samples: int = 1000


class ErrorRecord(BaseModel):
    example_id: str
    plagiarism_type: str
    language_pair: str
    ground_truth: bool
    predicted: bool
    score: float
    error_type: str  # 'false_positive' or 'false_negative'
    failure_mode: str  # 'negation_shift', 'numerical_shift', 'domain_adjacent_lexicon', 'lexical_miss', etc.
    suspicious_excerpt: str
    source_excerpt: str
    analysis: str


class EvaluationReport(BaseModel):
    split_name: str
    detector_mode: str
    dataset_version: str
    timestamp: str
    thresholds: dict[str, float]
    classification: ClassificationMetrics
    localization: LocalizationMetrics
    bootstrap_ci: dict[str, BootstrapConfidenceInterval]
    per_language_breakdown: dict[str, dict[str, float]]
    per_category_breakdown: dict[str, dict[str, float]]
    error_records: list[ErrorRecord] = Field(default_factory=list)
