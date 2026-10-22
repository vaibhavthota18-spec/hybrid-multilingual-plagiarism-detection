"""
Statistical Uncertainty and Bootstrap Confidence Intervals.
Provides deterministic, seed-fixed non-parametric bootstrap resampling
for classification and localization metrics.
"""

from typing import Callable, List, Tuple
import numpy as np
from plagiarism.evaluation.schemas import BootstrapConfidenceInterval


def compute_bootstrap_ci(
    y_true: List[bool],
    y_pred: List[bool],
    metric_func: Callable[[List[bool], List[bool]], float],
    metric_name: str,
    n_resamples: int = 1000,
    confidence_level: float = 0.95,
    random_seed: int = 42,
) -> BootstrapConfidenceInterval:
    """
    Computes a deterministic non-parametric bootstrap confidence interval
    for a classification metric using fixed-seed pseudo-random sampling.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have identical length")

    n = len(y_true)
    if n == 0:
        return BootstrapConfidenceInterval(
            metric_name=metric_name,
            point_estimate=0.0,
            lower_bound=0.0,
            upper_bound=0.0,
            confidence_level=confidence_level,
            bootstrap_samples=n_resamples,
        )

    # Point estimate on original dataset
    point_est = round(float(metric_func(y_true, y_pred)), 4)

    rng = np.random.RandomState(random_seed)
    y_true_arr = np.array(y_true, dtype=bool)
    y_pred_arr = np.array(y_pred, dtype=bool)

    bootstrap_estimates = []
    alpha = (1.0 - confidence_level) / 2.0

    for _ in range(n_resamples):
        indices = rng.randint(0, n, size=n)
        sample_true = y_true_arr[indices].tolist()
        sample_pred = y_pred_arr[indices].tolist()
        score = metric_func(sample_true, sample_pred)
        bootstrap_estimates.append(score)

    bootstrap_estimates = np.array(bootstrap_estimates)
    lower_pct = alpha * 100.0
    upper_pct = (1.0 - alpha) * 100.0

    lower = round(float(np.percentile(bootstrap_estimates, lower_pct)), 4)
    upper = round(float(np.percentile(bootstrap_estimates, upper_pct)), 4)

    return BootstrapConfidenceInterval(
        metric_name=metric_name,
        point_estimate=point_est,
        lower_bound=lower,
        upper_bound=upper,
        confidence_level=confidence_level,
        bootstrap_samples=n_resamples,
    )
