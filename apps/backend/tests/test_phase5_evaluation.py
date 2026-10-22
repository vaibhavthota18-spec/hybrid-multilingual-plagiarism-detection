"""
Phase 5 Scientific Evaluation Test Suite.
Tests statistical formulas (Wilson intervals, bootstrap CIs), classification metrics,
retrieval rankings (Recall@K, MRR, MAP), localization IoU, split leakage detection,
and evaluation runner execution.
"""

from pathlib import Path

import pytest

from plagiarism.evaluation.classification_metrics import (
    compute_classification_metrics,
    compute_wilson_interval,
)
from plagiarism.evaluation.dataset_loader import (
    DatasetValidationError,
    SplitLeakageError,
    load_benchmark_dataset,
    validate_example_spans,
    validate_split_leakage,
)
from plagiarism.evaluation.localization_metrics import (
    compute_boundary_error,
    compute_localization_metrics,
    compute_span_iou,
    merge_intervals,
)
from plagiarism.evaluation.retrieval_metrics import compute_retrieval_metrics
from plagiarism.evaluation.runner import EvaluationRunner
from plagiarism.evaluation.schemas import (
    DifficultyLevel,
    EvaluationDataset,
    EvaluationExample,
    GroundTruthSpan,
    PlagiarismCategory,
    SplitPartition,
)
from plagiarism.evaluation.statistical import compute_bootstrap_ci

# =============================================================================
# 1. Classification Metrics & Wilson Score Tests
# =============================================================================

def test_wilson_interval_bounds():
    """Verify Wilson interval properties on standard and edge cases."""
    # 50% success
    ci_50 = compute_wilson_interval(successes=50, total=100, confidence=0.95)
    assert ci_50.point_estimate == 0.5
    assert 0.40 < ci_50.lower_bound < 0.50
    assert 0.50 < ci_50.upper_bound < 0.60

    # 100% success (upper bound bounded at 1.0)
    ci_100 = compute_wilson_interval(successes=10, total=10, confidence=0.95)
    assert ci_100.point_estimate == 1.0
    assert ci_100.upper_bound == 1.0
    assert ci_100.lower_bound > 0.65

    # 0% success (lower bound bounded at 0.0)
    ci_0 = compute_wilson_interval(successes=0, total=10, confidence=0.95)
    assert ci_0.point_estimate == 0.0
    assert ci_0.lower_bound == 0.0
    assert ci_0.upper_bound < 0.35

    # Zero total handled gracefully
    ci_empty = compute_wilson_interval(successes=0, total=0)
    assert ci_empty.point_estimate == 0.0
    assert ci_empty.lower_bound == 0.0
    assert ci_empty.upper_bound == 0.0


def test_classification_metrics_math():
    """Verify precision, recall, f1, specificity, balanced accuracy, and FPR/FNR."""
    # y_true: [T, T, T, T, F, F, F, F]
    # y_pred: [T, T, T, F, T, F, F, F]
    # TP=3, FN=1, FP=1, TN=3
    y_true = [True, True, True, True, False, False, False, False]
    y_pred = [True, True, True, False, True, False, False, False]

    m = compute_classification_metrics(y_true, y_pred)
    assert m.tp == 3
    assert m.fn == 1
    assert m.fp == 1
    assert m.tn == 3
    assert m.precision == 0.75  # 3 / 4
    assert m.recall == 0.75     # 3 / 4
    assert m.f1 == 0.75         # 2*(0.75*0.75)/(1.5)
    assert m.specificity == 0.75  # 3 / 4
    assert m.fpr == 0.25          # 1 / 4
    assert m.fnr == 0.25          # 1 / 4
    assert m.balanced_accuracy == 0.75


def test_classification_metrics_edge_cases():
    """Ensure zero division does not raise exceptions when all negative or all positive."""
    # All false predictions
    y_true = [True, True]
    y_pred = [False, False]
    m_zero_pred = compute_classification_metrics(y_true, y_pred)
    assert m_zero_pred.tp == 0
    assert m_zero_pred.precision == 0.0
    assert m_zero_pred.recall == 0.0
    assert m_zero_pred.f1 == 0.0

    # Perfect predictions
    y_true = [True, False]
    y_pred = [True, False]
    m_perfect = compute_classification_metrics(y_true, y_pred)
    assert m_perfect.precision == 1.0
    assert m_perfect.recall == 1.0
    assert m_perfect.f1 == 1.0
    assert m_perfect.fpr == 0.0


# =============================================================================
# 2. Retrieval Metrics Tests
# =============================================================================

def test_retrieval_metrics_calculations():
    """Verify Recall@K, MRR, and MAP calculation logic."""
    queries = [
        # Query 1: Target at rank 1 (reciprocal rank = 1.0)
        {"target_source_id": "doc1", "ranked_source_ids": ["doc1", "doc2", "doc3"], "latency_ms": 10.0},
        # Query 2: Target at rank 2 (reciprocal rank = 0.5)
        {"target_source_id": "doc2", "ranked_source_ids": ["doc1", "doc2", "doc3"], "latency_ms": 12.0},
        # Query 3: Target at rank 3 (reciprocal rank = 0.3333)
        {"target_source_id": "doc3", "ranked_source_ids": ["doc1", "doc2", "doc3"], "latency_ms": 14.0},
        # Query 4: Target not in top 3 (reciprocal rank = 0.0)
        {"target_source_id": "docX", "ranked_source_ids": ["doc1", "doc2", "doc3"], "latency_ms": 8.0},
    ]

    metrics = compute_retrieval_metrics(queries, candidate_pool_size=10)
    assert metrics.queries_evaluated == 4
    assert metrics.recall_at_1 == 0.25   # 1/4
    assert metrics.recall_at_5 == 0.75   # 3/4 within rank 3 <= 5
    assert metrics.recall_at_10 == 0.75  # 3/4
    # MRR = (1.0 + 0.5 + 0.333333 + 0.0) / 4 = 1.833333 / 4 = 0.4583
    assert pytest.approx(metrics.mrr, abs=1e-3) == 0.4583
    assert pytest.approx(metrics.map_score, abs=1e-3) == 0.4583
    assert metrics.mean_latency_ms == 11.0


# =============================================================================
# 3. Localization Metrics Tests
# =============================================================================

def test_merge_intervals():
    """Verify interval union and merging."""
    assert merge_intervals([]) == []
    assert merge_intervals([(1, 5)]) == [(1, 5)]
    assert merge_intervals([(1, 4), (3, 7)]) == [(1, 7)]
    assert merge_intervals([(1, 3), (5, 8)]) == [(1, 3), (5, 8)]
    assert merge_intervals([(1, 10), (2, 5), (6, 9)]) == [(1, 10)]


def test_span_iou_and_overlap():
    """Verify interval intersection and IoU calculation."""
    # Exact overlap: IoU = 1.0
    iou_exact = compute_span_iou([(10, 50)], [(10, 50)])
    assert iou_exact == 1.0

    # Disjoint intervals: IoU = 0.0
    iou_disjoint = compute_span_iou([(10, 20)], [(30, 40)])
    assert iou_disjoint == 0.0

    # Partial overlap: [10, 50] and [30, 70]
    # Inter: [30, 50] (len 20)
    # Union: [10, 70] (len 60)
    # IoU = 20 / 60 = 0.3333
    iou_partial = compute_span_iou([(10, 50)], [(30, 70)])
    assert pytest.approx(iou_partial, abs=1e-3) == 0.3333

    # Boundary error: [10, 50] vs [12, 53] -> |10-12| + |50-53| = 2 + 3 = 5
    b_err = compute_boundary_error([(10, 50)], [(12, 53)])
    assert b_err == 5.0


def test_aggregate_localization_metrics():
    """Verify aggregated localization metrics over test cases."""
    cases = [
        {
            "gt_char_spans": [(0, 100)],
            "pred_char_spans": [(0, 100)],
            "gt_token_spans": [(0, 20)],
            "pred_token_spans": [(0, 20)],
        },
        {
            "gt_char_spans": [(0, 50)],
            "pred_char_spans": [(0, 25)],
            "gt_token_spans": [(0, 10)],
            "pred_token_spans": [(0, 5)],
        },
    ]
    loc = compute_localization_metrics(cases)
    assert loc.evaluated_positive_pairs == 2
    assert 0.70 < loc.char_iou < 0.80
    assert loc.span_recall == 0.75  # case 1: 1.0, case 2: 0.5


# =============================================================================
# 4. Deterministic Bootstrap Confidence Interval Tests
# =============================================================================

def test_deterministic_bootstrap_ci():
    """Verify bootstrap CI determinism and validity under fixed random seed."""
    y_true = [True] * 15 + [False] * 5
    y_pred = [True] * 12 + [False] * 3 + [True] * 1 + [False] * 4

    def acc_metric(yt, yp):
        tp = sum(1 for t, p in zip(yt, yp) if t and p)
        tn = sum(1 for t, p in zip(yt, yp) if not t and not p)
        return (tp + tn) / len(yt)

    ci_1 = compute_bootstrap_ci(y_true, y_pred, acc_metric, "accuracy", n_resamples=500, random_seed=42)
    ci_2 = compute_bootstrap_ci(y_true, y_pred, acc_metric, "accuracy", n_resamples=500, random_seed=42)

    # Identical results due to seed 42
    assert ci_1.point_estimate == ci_2.point_estimate
    assert ci_1.lower_bound == ci_2.lower_bound
    assert ci_1.upper_bound == ci_2.upper_bound
    assert ci_1.lower_bound <= ci_1.point_estimate <= ci_1.upper_bound


# =============================================================================
# 5. Dataset Validation & Leakage Detection Tests
# =============================================================================

def test_dataset_span_offset_validation():
    """Verify span validation rejects out-of-bound or corrupted substrings."""
    ex_valid = EvaluationExample(
        id="TEST-01",
        suspicious_text="Deep neural networks require substantial training data.",
        source_text="Neural networks need data.",
        suspicious_language="en",
        source_language="en",
        plagiarism_type=PlagiarismCategory.PARAPHRASE,
        is_plagiarism=True,
        difficulty=DifficultyLevel.EASY,
        domain="cs",
        provenance="Test Doc",
        split=SplitPartition.CALIBRATION,
        ground_truth_spans=[
            GroundTruthSpan(
                start_char=0,
                end_char=20,
                text="Deep neural networks",
                language="en",
            )
        ],
        rationale="Test valid span",
    )
    # Should pass without error
    validate_example_spans(ex_valid)

    # Corrupt offset
    ex_invalid = ex_valid.model_copy(deep=True)
    ex_invalid.ground_truth_spans[0].end_char = 25  # Mismatched length
    with pytest.raises(DatasetValidationError):
        validate_example_spans(ex_invalid)


def test_split_leakage_detector_catches_collision():
    """Verify split leakage detector identifies text collisions across splits."""
    shared_text = "This is a sensitive paragraph that should not be shared across splits."

    ex_calib = EvaluationExample(
        id="CALIB-T1",
        suspicious_text=shared_text,
        source_text="Source A",
        suspicious_language="en",
        source_language="en",
        plagiarism_type=PlagiarismCategory.EXACT,
        is_plagiarism=True,
        difficulty=DifficultyLevel.EASY,
        domain="cs",
        provenance="Test",
        split=SplitPartition.CALIBRATION,
        ground_truth_spans=[],
        rationale="Test calib",
    )
    ex_held = EvaluationExample(
        id="HELD-T1",
        suspicious_text=shared_text,  # LEAK!
        source_text="Source B",
        suspicious_language="en",
        source_language="en",
        plagiarism_type=PlagiarismCategory.EXACT,
        is_plagiarism=True,
        difficulty=DifficultyLevel.EASY,
        domain="cs",
        provenance="Test",
        split=SplitPartition.HELD_OUT_EVALUATION,
        ground_truth_spans=[],
        rationale="Test held out with leak",
    )

    dataset_leaked = EvaluationDataset(
        dataset_id="TEST-LEAK",
        version="1.0.0",
        created_at="2026-10-14T00:00:00Z",
        description="Leaked test dataset",
        examples=[ex_calib, ex_held],
    )

    with pytest.raises(SplitLeakageError) as exc_info:
        validate_split_leakage(dataset_leaked)
    assert "Suspicious text hash collision" in str(exc_info.value)


def test_benchmark_dataset_integrity():
    """Verify the real data/evaluation/benchmark_dataset_v1.json passes all validations."""
    benchmark_path = Path("data/evaluation/benchmark_dataset_v1.json")
    if not benchmark_path.exists():
        benchmark_path = Path(__file__).resolve().parents[3] / "data" / "evaluation" / "benchmark_dataset_v1.json"
    assert benchmark_path.exists(), "Benchmark dataset file must exist"

    dataset = load_benchmark_dataset(benchmark_path)
    assert len(dataset.examples) == 40
    calib = [e for e in dataset.examples if e.split == SplitPartition.CALIBRATION]
    held = [e for e in dataset.examples if e.split == SplitPartition.HELD_OUT_EVALUATION]
    assert len(calib) == 20
    assert len(held) == 20

    # Ensure zero leakage
    leakage_report = validate_split_leakage(dataset)
    assert leakage_report["status"] == "leakage_free"


# =============================================================================
# 6. Evaluation Runner Execution Tests
# =============================================================================

def test_evaluation_runner_lexical_and_semantic():
    """Test EvaluationRunner runs lexical and semantic evaluations cleanly."""
    runner = EvaluationRunner()

    exact_ex = EvaluationExample(
        id="RUNNER-EX-01",
        suspicious_text="Photosynthesis converts solar light into chemical glucose.",
        source_text="Photosynthesis converts solar light into chemical glucose.",
        suspicious_language="en",
        source_language="en",
        plagiarism_type=PlagiarismCategory.EXACT,
        is_plagiarism=True,
        difficulty=DifficultyLevel.EASY,
        domain="bio",
        provenance="Test",
        split=SplitPartition.CALIBRATION,
        ground_truth_spans=[],
        rationale="Exact match test",
    )

    # Lexical evaluation
    lex_res, _ = runner.evaluate_example(exact_ex, mode="lexical", thresholds={"lexical_coverage_threshold": 15.0})
    assert lex_res.predicted_is_plagiarism is True
    assert lex_res.similarity_score == 100.0

    # Semantic evaluation
    sem_res, _ = runner.evaluate_example(
        exact_ex,
        mode="semantic",
        thresholds={"semantic_paraphrase_threshold": 0.82, "semantic_translation_threshold": 0.80},
    )
    assert sem_res.predicted_is_plagiarism is True
    assert sem_res.similarity_score > 90.0
