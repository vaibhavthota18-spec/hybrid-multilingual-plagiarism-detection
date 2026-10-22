"""
Dataset Loader and Split Integrity Validator.
Loads benchmark JSON datasets, verifies schema compliance, validates character offsets,
and performs strict leakage detection across data partitions.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

from plagiarism.evaluation.schemas import EvaluationDataset, EvaluationExample, SplitPartition


class SplitLeakageError(Exception):
    """Raised when leakage is detected between calibration and held-out evaluation splits."""
    pass


class DatasetValidationError(Exception):
    """Raised when an evaluation dataset fails schema or span integrity checks."""
    pass


def compute_sha256(text: str) -> str:
    """Computes SHA-256 hex digest of normalized string."""
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()


def compute_char_ngrams(text: str, n: int = 5) -> set[str]:
    """Extracts character n-grams from normalized text."""
    clean = "".join(text.lower().split())
    if len(clean) < n:
        return {clean} if clean else set()
    return {clean[i:i + n] for i in range(len(clean) - n + 1)}


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Computes Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


def validate_example_spans(example: EvaluationExample) -> None:
    """
    Verifies that ground truth span offsets accurately index into suspicious_text.
    """
    text_len = len(example.suspicious_text)
    for span in example.ground_truth_spans:
        if span.start_char < 0 or span.end_char > text_len or span.start_char >= span.end_char:
            raise DatasetValidationError(
                f"Example {example.id}: Invalid span offsets [{span.start_char}:{span.end_char}] "
                f"for suspicious_text of length {text_len}."
            )
        actual_slice = example.suspicious_text[span.start_char:span.end_char]
        if actual_slice != span.text:
            raise DatasetValidationError(
                f"Example {example.id}: Span text mismatch. Expected '{span.text}', "
                f"found '{actual_slice}' at [{span.start_char}:{span.end_char}]."
            )


def validate_split_leakage(dataset: EvaluationDataset, max_ngram_jaccard: float = 0.50) -> dict[str, Any]:
    """
    Validates that calibration and held-out evaluation splits share:
    - Zero identical text hashes (SHA-256)
    - Zero suspicious or source text collision
    - Zero excessive n-gram Jaccard overlap (leakage guard)
    - Distinct example IDs
    """
    calib_examples: list[EvaluationExample] = []
    eval_examples: list[EvaluationExample] = []

    for ex in dataset.examples:
        if ex.split == SplitPartition.CALIBRATION:
            calib_examples.append(ex)
        elif ex.split == SplitPartition.HELD_OUT_EVALUATION:
            eval_examples.append(ex)

    if not calib_examples:
        raise SplitLeakageError("Dataset has no examples in calibration split.")
    if not eval_examples:
        raise SplitLeakageError("Dataset has no examples in held_out_evaluation split.")

    calib_hashes = set()
    calib_texts = []
    for ex in calib_examples:
        sub_hash = compute_sha256(ex.suspicious_text)
        src_hash = compute_sha256(ex.source_text)
        calib_hashes.add(sub_hash)
        calib_hashes.add(src_hash)
        calib_texts.append(ex.suspicious_text)
        calib_texts.append(ex.source_text)

    leakage_violations = []

    for ex in eval_examples:
        sub_hash = compute_sha256(ex.suspicious_text)
        src_hash = compute_sha256(ex.source_text)

        if sub_hash in calib_hashes:
            leakage_violations.append(f"Example {ex.id}: Suspicious text hash collision with calibration split.")
        if src_hash in calib_hashes:
            leakage_violations.append(f"Example {ex.id}: Source text hash collision with calibration split.")

        # Check n-gram similarity against all calibration texts
        eval_ngrams = compute_char_ngrams(ex.suspicious_text)
        for c_text in calib_texts:
            c_ngrams = compute_char_ngrams(c_text)
            sim = jaccard_similarity(eval_ngrams, c_ngrams)
            if sim > max_ngram_jaccard:
                leakage_violations.append(
                    f"Example {ex.id}: Excessive n-gram similarity ({sim:.2f} > {max_ngram_jaccard}) "
                    f"with calibration text: '{c_text[:40]}...'"
                )

    if leakage_violations:
        raise SplitLeakageError(
            f"Split leakage detected ({len(leakage_violations)} violations):\n" + "\n".join(leakage_violations)
        )

    return {
        "status": "leakage_free",
        "calibration_count": len(calib_examples),
        "held_out_evaluation_count": len(eval_examples),
        "total_count": len(dataset.examples),
        "unique_calibration_hashes": len(calib_hashes),
        "max_observed_jaccard": max_ngram_jaccard,
    }


def load_benchmark_dataset(file_path: Path | str) -> EvaluationDataset:
    """
    Loads, parses, and validates a benchmark dataset from a JSON file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Benchmark dataset file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    dataset = EvaluationDataset(**data)

    # Validate spans and example ID uniqueness
    seen_ids = set()
    for ex in dataset.examples:
        if ex.id in seen_ids:
            raise DatasetValidationError(f"Duplicate example ID found: {ex.id}")
        seen_ids.add(ex.id)
        validate_example_spans(ex)

    # Validate split leakage
    validate_split_leakage(dataset)

    return dataset
