# Multilingual Semantic AI Evaluation

## 1. Algorithmic Overview

The Phase 4 Semantic AI engine leverages:
- **Base Embedding Model**: `intfloat/multilingual-e5-small` (384-dimensional dense vectors, 12 layers).
- **Asymmetric Prefix Conditioning**: `"query: "` prepended to submission queries, `"passage: "` prepended to reference documents.
- **Calibrated Semantic Thresholds**:
  - `semantic_paraphrase_threshold = 0.82` (same-language semantic similarity).
  - `semantic_translation_threshold = 0.80` (cross-lingual semantic alignment).

---

## 2. Empirical Performance on Benchmark Splits

Evaluated with calibrated thresholds frozen from calibration sweep:

| Partition | Total | TP | FP | TN | FN | Precision | Recall | $F_1$ Score | Specificity | Balanced Acc |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Calibration** | 20 | 11 | 6 | 3 | 0 | **64.71%** | **100.0%** | **78.57%** | 33.33% | 66.67% |
| **Held-Out** | 20 | 11 | 4 | 5 | 0 | **73.33%** | **100.0%** | **84.61%** | 55.56% | 77.78% |

### 2.1 Wilson Score Confidence Intervals (Held-Out)
- **Precision**: 73.33% (95% CI: `[48.05%, 89.10%]`)
- **Recall**: 100.00% (95% CI: `[74.12%, 100.00%]`)
- **$F_1$ Score**: 84.61% (95% CI: `[58.55%, 94.23%]`)

### 2.2 Bootstrap 95% Confidence Intervals (1000 Resamples, Seed 42)
- **$F_1$**: Point = 0.8461, 95% CI = `[0.6957, 0.9565]`
- **Precision**: Point = 0.7333, 95% CI = `[0.5333, 0.9231]`
- **Recall**: Point = 1.0000, 95% CI = `[1.0000, 1.0000]`

---

## 3. Semantic Strengths & Boundary Limitations

### 3.1 Strengths: 100% Sensitivity across Languages
The semantic model achieves a **100% Recall ($FN = 0$)** on both calibration and held-out evaluation sets:
- It correctly flags all structural paraphrases in English, Hindi, and Telugu.
- It bridges the vocabulary gap in cross-lingual translations (`en-hi`, `en-te`, `hi-te`).

### 3.2 Limitations: Domain-Adjacent Hard Negatives
Dense semantic embeddings map texts sharing domain vocabulary into close vector proximity. As a result, hard negatives with contrary propositions (such as Supervised vs. Reinforcement learning, or policy negation shifts) scored between $0.80$ and $0.84$, producing 4 false positives on held-out data.
