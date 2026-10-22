"""
Evaluation package for Phase 5 Scientific Benchmarking and Validation.
"""

from plagiarism.evaluation.classification_metrics import (
    compute_classification_metrics,
    compute_wilson_interval,
)
from plagiarism.evaluation.dataset_loader import (
    DatasetValidationError,
    SplitLeakageError,
    load_benchmark_dataset,
    validate_split_leakage,
)
from plagiarism.evaluation.localization_metrics import (
    compute_boundary_error,
    compute_localization_metrics,
    compute_span_iou,
)
from plagiarism.evaluation.retrieval_metrics import compute_retrieval_metrics
from plagiarism.evaluation.runner import EvaluationRunner
from plagiarism.evaluation.schemas import (
    ClassificationMetrics,
    EvaluationDataset,
    EvaluationExample,
    EvaluationReport,
    GroundTruthSpan,
    LocalizationMetrics,
    PlagiarismCategory,
    PredictionResult,
    RetrievalMetrics,
    SplitPartition,
)
from plagiarism.evaluation.statistical import compute_bootstrap_ci

__all__ = [
    "ClassificationMetrics",
    "EvaluationDataset",
    "EvaluationExample",
    "EvaluationReport",
    "GroundTruthSpan",
    "LocalizationMetrics",
    "PlagiarismCategory",
    "PredictionResult",
    "RetrievalMetrics",
    "SplitPartition",
    "compute_classification_metrics",
    "compute_wilson_interval",
    "compute_retrieval_metrics",
    "compute_span_iou",
    "compute_boundary_error",
    "compute_localization_metrics",
    "compute_bootstrap_ci",
    "DatasetValidationError",
    "SplitLeakageError",
    "load_benchmark_dataset",
    "validate_split_leakage",
    "EvaluationRunner",
]
