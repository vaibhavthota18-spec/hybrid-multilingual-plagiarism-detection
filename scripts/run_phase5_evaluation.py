"""
Master Phase 5 Scientific Evaluation and Benchmarking Runner.
Executes reproducible experiments across Lexical, Semantic, and Hybrid detection modes,
calibrates thresholds on calibration split, tests frozen thresholds on held-out split,
evaluates retrieval and localization, and exports machine-readable results.
"""

import json
from pathlib import Path
import time

from plagiarism.evaluation.dataset_loader import load_benchmark_dataset, validate_split_leakage
from plagiarism.evaluation.runner import EvaluationRunner
from plagiarism.evaluation.schemas import SplitPartition


def run_full_evaluation():
    print("=" * 80)
    print("  PHASE 5 SCIENTIFIC BENCHMARKING AND EVALUATION EXECUTION")
    print("=" * 80)

    benchmark_path = Path("data/evaluation/benchmark_dataset_v1.json")
    print(f"\n[Step 1] Loading benchmark dataset from {benchmark_path}...")
    dataset = load_benchmark_dataset(benchmark_path)
    print(f"  Loaded {len(dataset.examples)} examples across languages: {dataset.languages}")

    leakage_info = validate_split_leakage(dataset)
    print(f"  Split Leakage Verification: {leakage_info['status'].upper()}")
    print(f"  Calibration examples: {leakage_info['calibration_count']}, Held-out examples: {leakage_info['held_out_evaluation_count']}")

    runner = EvaluationRunner()
    calib_examples = [e for e in dataset.examples if e.split == SplitPartition.CALIBRATION]
    held_examples = [e for e in dataset.examples if e.split == SplitPartition.HELD_OUT_EVALUATION]

    # =========================================================================
    # Step 2: Threshold Calibration on Calibration Split
    # =========================================================================
    print("\n[Step 2] Executing Threshold Calibration on Calibration Partition...")
    t0_calib = time.perf_counter()

    lex_thresholds = runner.calibrate_thresholds(calib_examples, mode="lexical")
    print(f"  Calibrated Lexical Thresholds: {lex_thresholds}")

    sem_thresholds = runner.calibrate_thresholds(calib_examples, mode="semantic")
    print(f"  Calibrated Semantic Thresholds: {sem_thresholds}")

    hybrid_thresholds = runner.calibrate_thresholds(calib_examples, mode="hybrid")
    print(f"  Calibrated Hybrid Thresholds: {hybrid_thresholds}")

    calib_duration = round(time.perf_counter() - t0_calib, 2)
    print(f"  Threshold calibration completed in {calib_duration}s.")

    # Save calibration summary
    calib_summary = {
        "dataset_version": dataset.version,
        "calibration_samples": len(calib_examples),
        "calibration_time_seconds": calib_duration,
        "calibrated_thresholds": {
            "lexical": lex_thresholds,
            "semantic": sem_thresholds,
            "hybrid": hybrid_thresholds,
        },
    }
    with open("data/evaluation/calibration_report.json", "w", encoding="utf-8") as f:
        json.dump(calib_summary, f, indent=2)

    # =========================================================================
    # Step 3: Run Calibration Partition Reports
    # =========================================================================
    print("\n[Step 3] Evaluating Baseline Performance on Calibration Split...")
    report_calib_lex = runner.run_evaluation(dataset, mode="lexical", split=SplitPartition.CALIBRATION, thresholds=lex_thresholds)
    report_calib_sem = runner.run_evaluation(dataset, mode="semantic", split=SplitPartition.CALIBRATION, thresholds=sem_thresholds)
    report_calib_hyb = runner.run_evaluation(dataset, mode="hybrid", split=SplitPartition.CALIBRATION, thresholds=hybrid_thresholds)

    print(f"  Calibration Lexical  -> Precision: {report_calib_lex.classification.precision:.2%}, Recall: {report_calib_lex.classification.recall:.2%}, F1: {report_calib_lex.classification.f1:.2%}")
    print(f"  Calibration Semantic -> Precision: {report_calib_sem.classification.precision:.2%}, Recall: {report_calib_sem.classification.recall:.2%}, F1: {report_calib_sem.classification.f1:.2%}")
    print(f"  Calibration Hybrid   -> Precision: {report_calib_hyb.classification.precision:.2%}, Recall: {report_calib_hyb.classification.recall:.2%}, F1: {report_calib_hyb.classification.f1:.2%}")

    # =========================================================================
    # Step 4: Run Held-Out Evaluation with Frozen Thresholds
    # =========================================================================
    print("\n[Step 4] Evaluating Performance on Held-Out Split with FROZEN Thresholds...")
    t0_eval = time.perf_counter()

    report_held_lex = runner.run_evaluation(dataset, mode="lexical", split=SplitPartition.HELD_OUT_EVALUATION, thresholds=lex_thresholds)
    report_held_sem = runner.run_evaluation(dataset, mode="semantic", split=SplitPartition.HELD_OUT_EVALUATION, thresholds=sem_thresholds)
    report_held_hyb = runner.run_evaluation(dataset, mode="hybrid", split=SplitPartition.HELD_OUT_EVALUATION, thresholds=hybrid_thresholds)

    eval_duration = round(time.perf_counter() - t0_eval, 2)
    print(f"  Held-out evaluation completed in {eval_duration}s.")

    print(f"  Held-Out Lexical  -> Precision: {report_held_lex.classification.precision:.2%}, Recall: {report_held_lex.classification.recall:.2%}, F1: {report_held_lex.classification.f1:.2%}")
    print(f"  Held-Out Semantic -> Precision: {report_held_sem.classification.precision:.2%}, Recall: {report_held_sem.classification.recall:.2%}, F1: {report_held_sem.classification.f1:.2%}")
    print(f"  Held-Out Hybrid   -> Precision: {report_held_hyb.classification.precision:.2%}, Recall: {report_held_hyb.classification.recall:.2%}, F1: {report_held_hyb.classification.f1:.2%}")

    # =========================================================================
    # Step 5: Candidate Retrieval Ranking Benchmark
    # =========================================================================
    print("\n[Step 5] Benchmarking Candidate Source Retrieval Rankings...")
    retrieval_lex = runner.run_retrieval_benchmark(held_examples, mode="lexical")
    retrieval_sem = runner.run_retrieval_benchmark(held_examples, mode="semantic")
    retrieval_hyb = runner.run_retrieval_benchmark(held_examples, mode="hybrid")

    print(f"  Retrieval Lexical  -> Recall@1: {retrieval_lex.recall_at_1:.2%}, Recall@5: {retrieval_lex.recall_at_5:.2%}, MRR: {retrieval_lex.mrr:.4f}")
    print(f"  Retrieval Semantic -> Recall@1: {retrieval_sem.recall_at_1:.2%}, Recall@5: {retrieval_sem.recall_at_5:.2%}, MRR: {retrieval_sem.mrr:.4f}")
    print(f"  Retrieval Hybrid   -> Recall@1: {retrieval_hyb.recall_at_1:.2%}, Recall@5: {retrieval_hyb.recall_at_5:.2%}, MRR: {retrieval_hyb.mrr:.4f}")

    # =========================================================================
    # Step 6: Export Comprehensive JSON Results
    # =========================================================================
    print("\n[Step 6] Compiling Master Results and Failure Taxonomy...")

    all_errors = (
        report_calib_hyb.error_records
        + report_held_hyb.error_records
        + report_held_lex.error_records
        + report_held_sem.error_records
    )
    # Deduplicate error records by (example_id, detector_mode)
    unique_errors = []
    seen = set()
    for err in all_errors:
        key = (err.example_id, err.error_type, err.failure_mode)
        if key not in seen:
            seen.add(key)
            unique_errors.append(err.model_dump())

    with open("data/evaluation/error_analysis.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "dataset_version": dataset.version,
                "total_unique_errors": len(unique_errors),
                "error_records": unique_errors,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    master_results = {
        "metadata": {
            "dataset_id": dataset.dataset_id,
            "version": dataset.version,
            "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_examples": len(dataset.examples),
            "calibration_examples": len(calib_examples),
            "held_out_examples": len(held_examples),
        },
        "thresholds": {
            "lexical": lex_thresholds,
            "semantic": sem_thresholds,
            "hybrid": hybrid_thresholds,
        },
        "calibration_results": {
            "lexical": report_calib_lex.model_dump(),
            "semantic": report_calib_sem.model_dump(),
            "hybrid": report_calib_hyb.model_dump(),
        },
        "held_out_results": {
            "lexical": report_held_lex.model_dump(),
            "semantic": report_held_sem.model_dump(),
            "hybrid": report_held_hyb.model_dump(),
        },
        "retrieval_benchmarks": {
            "lexical": retrieval_lex.model_dump(),
            "semantic": retrieval_sem.model_dump(),
            "hybrid": retrieval_hyb.model_dump(),
        },
    }

    with open("data/evaluation/evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(master_results, f, indent=2, ensure_ascii=False)

    print(f"\n[DONE] Saved evaluation results to data/evaluation/evaluation_results.json")
    print(f"[DONE] Saved error taxonomy to data/evaluation/error_analysis.json")
    print(f"[DONE] Saved calibration report to data/evaluation/calibration_report.json")
    print("=" * 80)


if __name__ == "__main__":
    run_full_evaluation()
