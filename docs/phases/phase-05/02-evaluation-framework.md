# Evaluation Subsystem Architecture & Modular Design

## 1. Modular Subsystem Design

To prevent evaluation code from polluting user-facing production APIs or persisting scratch records into user document metadata tables, the Phase 5 evaluation engine was engineered as a self-contained, modular package:

`apps/backend/src/plagiarism/evaluation/`

```
apps/backend/src/plagiarism/evaluation/
├── __init__.py                  # Public exports
├── schemas.py                   # Pydantic v2 schemas and dataclasses
├── dataset_loader.py            # Dataset parser, span integrity, and split leakage validator
├── classification_metrics.py    # TP/FP/TN/FN, Precision, Recall, F1, Wilson intervals
├── retrieval_metrics.py         # Candidate ranking (Recall@K, MRR, MAP, latency)
├── localization_metrics.py      # Token & Character IoU, span F1, boundary error
├── statistical.py               # Seed-fixed non-parametric bootstrap resampling
└── runner.py                    # Multi-mode evaluation coordinator & calibration sweep
```

---

## 2. Mathematical Metric Formulations

### 2.1 Classification Metrics
Given binary ground truth $y \in \{0, 1\}^N$ and detector decision $\hat{y} \in \{0, 1\}^N$:
- **True Positives ($TP$)**: $\sum_{i=1}^N \mathbb{I}(y_i = 1 \land \hat{y}_i = 1)$
- **False Positives ($FP$)**: $\sum_{i=1}^N \mathbb{I}(y_i = 0 \land \hat{y}_i = 1)$
- **True Negatives ($TN$)**: $\sum_{i=1}^N \mathbb{I}(y_i = 0 \land \hat{y}_i = 0)$
- **False Negatives ($FN$)**: $\sum_{i=1}^N \mathbb{I}(y_i = 1 \land \hat{y}_i = 0)$

$$\text{Precision} = \frac{TP}{TP + FP}, \quad \text{Recall} = \frac{TP}{TP + FN}$$
$$F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
$$\text{Specificity} = \frac{TN}{TN + FP}, \quad \text{Balanced Accuracy} = \frac{\text{Recall} + \text{Specificity}}{2}$$
$$\text{FPR} = \frac{FP}{FP + TN} = 1 - \text{Specificity}, \quad \text{FNR} = \frac{FN}{FN + TP} = 1 - \text{Recall}$$

### 2.2 Wilson Score Confidence Interval
For observed success proportion $\hat{p} = \frac{k}{n}$ under confidence level $1 - \alpha$ ($z = 1.95996$ for $95\%$):

$$\tilde{p} = \frac{k + \frac{z^2}{2}}{n + z^2}, \quad \text{Spread} = \frac{z}{1 + \frac{z^2}{n}} \sqrt{\frac{\hat{p}(1 - \hat{p})}{n} + \frac{z^2}{4n^2}}$$
$$CI_{95\%} = \left[ \max(0.0, \tilde{p} - \text{Spread}), \, \min(1.0, \tilde{p} + \text{Spread}) \right]$$

### 2.3 Information Retrieval Metrics
Given a pool of reference documents $D$ and query $q$:
- **Recall@K**: Proportion of queries where the ground-truth reference appears at $\text{rank} \le K$.
- **Mean Reciprocal Rank (MRR)**:
  $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
- **Mean Average Precision (MAP)**:
  $$\text{MAP} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \text{AP}_i$$

### 2.4 Localization Intersection-over-Union (IoU)
Given merged ground truth intervals $D_{gt}$ and predicted intervals $D_{pred}$:

$$\text{IoU} = \frac{|D_{gt} \cap D_{pred}|}{|D_{gt} \cup D_{pred}|} = \frac{\sum \text{overlap}}{\sum D_{gt} + \sum D_{pred} - \sum \text{overlap}}$$

---

## 3. Separation of Concerns & Isolation Guard

1. The evaluation module loads benchmark JSON records independently.
2. It interacts with `LexicalTokenizer`, `WinnowingEngine`, `PassageAligner`, and `SemanticEmbeddingProvider` in a stateless manner.
3. No dummy records are inserted into `storage/local_metadata.db`.
4. The user's private document storage remains completely unpolluted.
