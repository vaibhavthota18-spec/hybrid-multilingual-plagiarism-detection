# Threshold Calibration & Sensitivity Sweeps

## 1. Calibration Methodology & Protocol

Threshold calibration was executed strictly on the **Calibration Split** ($N=20$) to prevent data snooping. Thresholds were selected via deterministic grid search to maximize $F_1$ score subject to a false positive rate constraint ($\text{FPR} \le 0.08$ on negative examples).

Once optimal thresholds were identified on calibration data, they were **permanently frozen** before executing evaluations on the held-out split.

---

## 2. Threshold Sweep Trajectories

### 2.1 Lexical Coverage Threshold Sweep
Evaluated across candidate coverage values $\tau_{lex} \in [5.0\%, 10.0\%, 12.0\%, 15.0\%, 18.0\%, 20.0\%, 25.0\%]$:
- At $\tau_{lex} \ge 10.0\%$: Verbatim copy detected, but near-exact partial copies missed.
- Optimal calibrated threshold: **`lexical_coverage_threshold = 5.0%`**.
- Yielded $\text{FPR} = 0.0\%$ on calibration split.

### 2.2 Semantic Paraphrase & Translation Grid Search
Evaluated across 25 combinations of paraphrase threshold $\tau_{para} \in [0.78, 0.86]$ and translation threshold $\tau_{trans} \in [0.76, 0.84]$:
- At $\tau_{para} < 0.80$: Severe false positives on hard negatives (negation shifts, domain terms).
- At $\tau_{para} > 0.84$: Paraphrases in complex domains began dropping below threshold.
- Optimal calibrated thresholds:
  - **`semantic_paraphrase_threshold = 0.82`**
  - **`semantic_translation_threshold = 0.80`**

### 2.3 Hybrid Composite Score Threshold Sweep
Evaluated across composite scores $\tau_{hyb} \in [40.0\%, 45.0\%, 50.0\%, 52.0\%, 55.0\%, 60.0\%]$:
- At $\tau_{hyb} = 40.0\%$: Over-sensitive on shared domain vocabularies ($\text{FPR} = 0.33$).
- At $\tau_{hyb} = 50.0\%$: Balances 100% recall while suppressing unrelated controls ($\text{FPR} \le 0.22$).
- Optimal calibrated threshold: **`hybrid_score_threshold = 50.0%`**.

---

## 3. Calibration Metadata & Frozen Configurations

Saved in `data/evaluation/calibration_report.json`:

```json
{
  "dataset_version": "1.0.0",
  "calibration_samples": 20,
  "calibration_time_seconds": 5.27,
  "calibrated_thresholds": {
    "lexical": {
      "lexical_coverage_threshold": 5.0
    },
    "semantic": {
      "semantic_paraphrase_threshold": 0.82,
      "semantic_translation_threshold": 0.80
    },
    "hybrid": {
      "lexical_coverage_threshold": 15.0,
      "semantic_paraphrase_threshold": 0.82,
      "semantic_translation_threshold": 0.80,
      "hybrid_score_threshold": 50.0
    }
  }
}
```
