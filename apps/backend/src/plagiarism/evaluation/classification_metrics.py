"""
Classification Metrics Computation for Scientific Evaluation.
Calculates TP, FP, TN, FN, Precision, Recall, F1, Specificity, FPR, FNR,
Balanced Accuracy, Confusion Matrices, and Wilson Score Confidence Intervals.
"""

import math

from plagiarism.evaluation.schemas import ClassificationMetrics, WilsonInterval


def compute_wilson_interval(successes: int, total: int, confidence: float = 0.95) -> WilsonInterval:
    """
    Computes the Wilson score interval for a binomial proportion.
    Handles small sample sizes and boundary conditions (0% or 100%) gracefully.
    """
    if total <= 0:
        return WilsonInterval(point_estimate=0.0, lower_bound=0.0, upper_bound=0.0, confidence_level=confidence)

    # Standard normal quantile for confidence level (e.g., 1.95996 for 95%)
    # Using inverse error function approximation or standard z-values
    z_table = {
        0.90: 1.644853,
        0.95: 1.959964,
        0.98: 2.326348,
        0.99: 2.575829,
    }
    z = z_table.get(round(confidence, 2), 1.959964)

    p = successes / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    variance_term = (p * (1.0 - p) / total) + ((z**2) / (4.0 * (total**2)))
    spread = (z * math.sqrt(max(0.0, variance_term))) / denom

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)

    return WilsonInterval(
        point_estimate=round(p, 4),
        lower_bound=round(lower, 4),
        upper_bound=round(upper, 4),
        confidence_level=confidence,
    )


def compute_classification_metrics(
    y_true: list[bool],
    y_pred: list[bool],
    confidence_level: float = 0.95,
) -> ClassificationMetrics:
    """
    Computes rigorous classification metrics given ground-truth and predicted binary labels.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")

    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt and yp)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if not yt and yp)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if not yt and not yp)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt and not yp)
    total = len(y_true)

    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) > 0 else 0.0

    specificity = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0
    fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
    fnr = round(fn / (fn + tp), 4) if (fn + tp) > 0 else 0.0

    balanced_accuracy = round((recall + specificity) / 2.0, 4)

    precision_ci = compute_wilson_interval(tp, tp + fp, confidence=confidence_level)
    recall_ci = compute_wilson_interval(tp, tp + fn, confidence=confidence_level)

    # For F1 Wilson approximation, using harmonic mean of bounds
    f1_lower = (
        round(2 * precision_ci.lower_bound * recall_ci.lower_bound / (precision_ci.lower_bound + recall_ci.lower_bound), 4)
        if (precision_ci.lower_bound + recall_ci.lower_bound) > 0
        else 0.0
    )
    f1_upper = (
        round(2 * precision_ci.upper_bound * recall_ci.upper_bound / (precision_ci.upper_bound + recall_ci.upper_bound), 4)
        if (precision_ci.upper_bound + recall_ci.upper_bound) > 0
        else 0.0
    )
    f1_ci = WilsonInterval(
        point_estimate=f1,
        lower_bound=f1_lower,
        upper_bound=f1_upper,
        confidence_level=confidence_level,
    )

    return ClassificationMetrics(
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
        total=total,
        precision=precision,
        recall=recall,
        f1=f1,
        specificity=specificity,
        fpr=fpr,
        fnr=fnr,
        balanced_accuracy=balanced_accuracy,
        confusion_matrix={"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        precision_wilson_ci=precision_ci,
        recall_wilson_ci=recall_ci,
        f1_wilson_ci=f1_ci,
    )
