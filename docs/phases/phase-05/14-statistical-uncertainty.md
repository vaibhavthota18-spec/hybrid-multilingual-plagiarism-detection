# Statistical Uncertainty, Wilson Intervals, and Bootstrap CIs

## 1. Scientific Need for Uncertainty Quantification

Point estimates (e.g., "$F_1 = 84.61\%$") without confidence intervals can be misleading on benchmark datasets with finite sample sizes ($N=20$).

Phase 5 implements two complementary statistical uncertainty frameworks:
1. **Parametric Wilson Score Intervals**: Closed-form binomial confidence intervals for proportions (Precision, Recall, Specificity).
2. **Non-Parametric Bootstrap Resampling**: 1,000 resamples with fixed pseudo-random seed (`seed=42`) for complex non-linear metrics like $F_1$.

---

## 2. Statistical Uncertainty Matrix (Held-Out Split)

Evaluated under the **Hybrid Engine** ($N=20$ examples):

| Metric | Point Estimate | Wilson 95% Confidence Interval | Bootstrap 95% Confidence Interval (1,000 Draws) |
| :--- | :---: | :---: | :---: |
| **Precision** | **73.33%** | `[48.05%, 89.10%]` | `[53.33%, 92.31%]` |
| **Recall** | **100.00%** | `[74.12%, 100.00%]` | `[100.00%, 100.00%]` |
| **$F_1$ Score** | **84.61%** | `[58.55%, 94.23%]` | `[69.57%, 95.65%]` |
| **Balanced Accuracy** | **77.78%** | — | `[60.00%, 93.33%]` |

---

## 3. Methodological Properties & Verification

### 3.1 Asymmetric Bounds
Unlike naive normal approximations ($\hat{p} \pm 1.96 \sqrt{\frac{p(1-p)}{n}}$) which produce impossible bounds below $0.0$ or above $1.0$, the **Wilson score interval** naturally remains bounded within $[0.0, 1.0]$:
- For Recall = 100.0% ($11/11$), the Wilson interval lower bound is $74.12\%$ and the upper bound is strictly $1.0000$.

### 3.2 Deterministic Bootstrap Reproducibility
In `plagiarism/evaluation/statistical.py`, `np.random.RandomState(42)` ensures that identical random index sequences are generated across any Python environment, guaranteeing exact bit-for-bit reproducibility of empirical results.
