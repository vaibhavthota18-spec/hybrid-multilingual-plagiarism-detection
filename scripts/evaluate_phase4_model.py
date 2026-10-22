"""
Phase 4 Model Evaluation & Threshold Calibration Script.
Evaluates local embedding model (intfloat/multilingual-e5-small) across the 20 gold-standard
multilingual pairs (English, Hindi, Telugu, paraphrases, translations, hard negatives, and unrelated).
Computes exact empirical cosine similarities, confusion matrix, precision, recall, and F1 score.
"""

import json
import os
import sys
from pathlib import Path
import numpy as np

# Add apps/backend/src to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "apps" / "backend" / "src"))

from plagiarism.services.semantic.provider import get_embedding_provider
from plagiarism.core.config import get_settings


def main():
    benchmark_path = root_dir / "data" / "phase4_calibration_multilingual.json"
    if not benchmark_path.exists():
        print(f"Error: {benchmark_path} does not exist!")
        sys.exit(1)

    with open(benchmark_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    settings = get_settings()
    provider = get_embedding_provider()
    model_info = provider.get_model_info()

    print("=" * 80)
    print("PHASE 4 MULTILINGUAL SEMANTIC MODEL BENCHMARK EVALUATION")
    print("=" * 80)
    print(f"Model Name        : {model_info['model_name']}")
    print(f"Embedding Dim     : {model_info['embedding_dimension']}")
    print(f"Runtime Device    : {model_info['device']}")
    print(f"Paraphrase Thresh : {settings.SEMANTIC_PARAPHRASE_THRESHOLD}")
    print(f"Translation Thresh: {settings.SEMANTIC_TRANSLATION_THRESHOLD}")
    print(f"Benchmark Pairs   : {len(data['pairs'])}")
    print("-" * 80)

    results = []
    tp, fp, tn, fn = 0, 0, 0, 0

    for item in data["pairs"]:
        pair_id = item["pair_id"]
        category = item["category"]
        gt_plag = item["ground_truth_plagiarized"]
        l1, l2 = item["language_1"], item["language_2"]
        t1, t2 = item["text_1"], item["text_2"]

        is_cross_lingual = (l1 != l2)
        threshold = (
            settings.SEMANTIC_TRANSLATION_THRESHOLD
            if is_cross_lingual
            else settings.SEMANTIC_PARAPHRASE_THRESHOLD
        )

        # Encode query and passage
        q_vec = provider.encode_queries([t1])[0]
        p_vec = provider.encode_passages([t2])[0]

        # Cosine similarity
        cosine_sim = float(np.dot(q_vec, p_vec))
        predicted_plag = bool(cosine_sim >= threshold)

        if gt_plag and predicted_plag:
            tp += 1
            verdict = "TP (HIT)"
        elif not gt_plag and not predicted_plag:
            tn += 1
            verdict = "TN (CORRECT REJECTION)"
        elif not gt_plag and predicted_plag:
            fp += 1
            verdict = "FP (FALSE ALARM)"
        else:
            fn += 1
            verdict = "FN (MISSED)"

        results.append({
            "pair_id": pair_id,
            "category": category,
            "languages": f"{l1}-{l2}",
            "cosine_similarity": round(cosine_sim, 4),
            "threshold": threshold,
            "ground_truth": gt_plag,
            "predicted": predicted_plag,
            "verdict": verdict,
        })

        print(f"[{pair_id}] {category:25} | {l1}-{l2} | Cos: {cosine_sim:.4f} | Thresh: {threshold:.2f} | {verdict}")

    total = len(results)
    accuracy = (tp + tn) / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print("-" * 80)
    print("EVALUATION SUMMARY METRICS:")
    print(f"Total Evaluated     : {total}")
    print(f"True Positives (TP) : {tp}")
    print(f"True Negatives (TN) : {tn}")
    print(f"False Positives (FP): {fp}")
    print(f"False Negatives (FN): {fn}")
    print(f"Accuracy            : {accuracy * 100:.2f}%")
    print(f"Precision           : {precision * 100:.2f}%")
    print(f"Recall              : {recall * 100:.2f}%")
    print(f"F1 Score            : {f1 * 100:.2f}%")
    print("=" * 80)

    # Save evaluation report json
    eval_report = {
        "model_name": model_info["model_name"],
        "device": model_info["device"],
        "summary": {
            "total_pairs": total,
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        },
        "pair_results": results,
    }

    report_path = root_dir / "data" / "phase4_evaluation_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2, ensure_ascii=False)

    print(f"Saved evaluation report to {report_path}")


if __name__ == "__main__":
    main()
