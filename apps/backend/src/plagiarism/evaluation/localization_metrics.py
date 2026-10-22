"""
Passage Localization and Boundary Metrics.
Calculates token-level and character-level IoU (Intersection-over-Union),
Span Precision, Span Recall, Span F1, and mean boundary error on Unicode offsets.
"""

from typing import List, Tuple
from plagiarism.evaluation.schemas import LocalizationMetrics


def merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Merges overlapping or contiguous integer intervals.
    """
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged = [sorted_intervals[0]]
    for current_start, current_end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        if current_start <= last_end:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))
    return merged


def compute_interval_overlap(
    set_a: List[Tuple[int, int]],
    set_b: List[Tuple[int, int]],
) -> Tuple[int, int, int]:
    """
    Given two lists of intervals, computes:
    - intersection_len
    - len_a
    - len_b
    """
    merged_a = merge_intervals(set_a)
    merged_b = merge_intervals(set_b)

    len_a = sum(e - s for s, e in merged_a if e > s)
    len_b = sum(e - s for s, e in merged_b if e > s)

    intersection_len = 0
    for s_a, e_a in merged_a:
        for s_b, e_b in merged_b:
            overlap_s = max(s_a, s_b)
            overlap_e = min(e_a, e_b)
            if overlap_e > overlap_s:
                intersection_len += (overlap_e - overlap_s)

    return intersection_len, len_a, len_b


def compute_span_iou(
    gt_intervals: List[Tuple[int, int]],
    pred_intervals: List[Tuple[int, int]],
) -> float:
    """
    Computes Intersection-over-Union (IoU) between ground-truth and predicted intervals.
    """
    inter, len_gt, len_pred = compute_interval_overlap(gt_intervals, pred_intervals)
    union_len = len_gt + len_pred - inter
    if union_len == 0:
        return 1.0 if (len_gt == 0 and len_pred == 0) else 0.0
    return round(inter / union_len, 4)


def compute_boundary_error(
    gt_intervals: List[Tuple[int, int]],
    pred_intervals: List[Tuple[int, int]],
) -> float:
    """
    Computes average boundary deviation (start error + end error) in characters
    between predicted spans and their nearest ground truth span.
    """
    if not gt_intervals or not pred_intervals:
        return 0.0

    errors = []
    for p_s, p_e in pred_intervals:
        # Find closest ground truth span
        best_err = float("inf")
        for g_s, g_e in gt_intervals:
            err = abs(p_s - g_s) + abs(p_e - g_e)
            if err < best_err:
                best_err = err
        errors.append(best_err)

    return round(sum(errors) / len(errors), 2) if errors else 0.0


def compute_localization_metrics(
    eval_cases: List[dict],
) -> LocalizationMetrics:
    """
    Aggregates localization metrics across all positive evaluation cases.
    Each case in `eval_cases` must contain:
    - `gt_char_spans`: List[Tuple[int, int]]
    - `pred_char_spans`: List[Tuple[int, int]]
    - `gt_token_spans`: List[Tuple[int, int]]
    - `pred_token_spans`: List[Tuple[int, int]]
    """
    if not eval_cases:
        return LocalizationMetrics(
            char_iou=0.0,
            token_iou=0.0,
            span_precision=0.0,
            span_recall=0.0,
            span_f1=0.0,
            mean_boundary_error_chars=0.0,
            evaluated_positive_pairs=0,
        )

    char_ious = []
    token_ious = []
    span_precisions = []
    span_recalls = []
    span_f1s = []
    boundary_errors = []

    for case in eval_cases:
        gt_chars = case.get("gt_char_spans", [])
        pred_chars = case.get("pred_char_spans", [])
        gt_tokens = case.get("gt_token_spans", [])
        pred_tokens = case.get("pred_token_spans", [])

        # Character IoU & overlap
        c_iou = compute_span_iou(gt_chars, pred_chars)
        char_ious.append(c_iou)

        inter_c, len_gt_c, len_pred_c = compute_interval_overlap(gt_chars, pred_chars)
        prec = (inter_c / len_pred_c) if len_pred_c > 0 else 0.0
        rec = (inter_c / len_gt_c) if len_gt_c > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        span_precisions.append(prec)
        span_recalls.append(rec)
        span_f1s.append(f1)

        # Token IoU
        t_iou = compute_span_iou(gt_tokens, pred_tokens)
        token_ious.append(t_iou)

        # Boundary error
        b_err = compute_boundary_error(gt_chars, pred_chars)
        boundary_errors.append(b_err)

    n = len(eval_cases)
    mean_char_iou = round(sum(char_ious) / n, 4)
    mean_token_iou = round(sum(token_ious) / n, 4)
    mean_prec = round(sum(span_precisions) / n, 4)
    mean_rec = round(sum(span_recalls) / n, 4)
    mean_f1 = round(sum(span_f1s) / n, 4)
    mean_b_err = round(sum(boundary_errors) / n, 2)

    return LocalizationMetrics(
        char_iou=mean_char_iou,
        token_iou=mean_token_iou,
        span_precision=mean_prec,
        span_recall=mean_rec,
        span_f1=mean_f1,
        mean_boundary_error_chars=mean_b_err,
        evaluated_positive_pairs=n,
    )
