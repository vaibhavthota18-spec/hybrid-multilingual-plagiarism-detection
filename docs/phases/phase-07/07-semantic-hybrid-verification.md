# Phase 7 — Multilingual Semantic AI & Hybrid Scoring Verification

## 1. Dense Embedding Model
- **Model:** `intfloat/multilingual-e5-small` (384-dimensional dense vectors).
- **Execution:** Native CPU inference using PyTorch (`torch.no_grad()`).
- **Prefix Conditioning:** Enforces mandatory E5 query and passage prefixes:
  - Query passages: `"query: "`
  - Reference passages: `"passage: "`
- **L2 Normalization:** All vectors are $L_2$-normalized ($||\mathbf{v}||_2 = 1.0$), reducing cosine similarity to Euclidean dot product:
  $$\text{sim}(\mathbf{u}, \mathbf{v}) = \mathbf{u} \cdot \mathbf{v}$$

## 2. Calibrated Decision Thresholds (Phase 5 Empirically Validated)
| Category | Metric | Calibrated Threshold ($\tau$) | Evidence Class |
| :--- | :--- | :--- | :--- |
| **Exact Copy** | Winnowing match | Token span $\ge 25$ tokens | High Confidence Verbatim |
| **Near-Exact Copy** | Lexical similarity | $\ge 0.85$ token overlap | Moderate-High Overlap |
| **Paraphrase** | Dense Cosine Sim | $\tau_{\text{para}} = 0.82$ | Semantic Equivalence |
| **Cross-Lingual** | Dense Cosine Sim | $\tau_{\text{trans}} = 0.80$ | Potential Translation |
| **Lexical Filter** | Lexical Coverage | $\tau_{\text{lex}} = 5.0\%$ | Anti-Noise Filter |

## 3. Hybrid Non-Overlapping Token Union
- Rather than summing per-source percentages (which causes double-counting), the engine computes the 1D interval union of all verified matching token spans across both lexical and semantic detections:
  $$\text{Coverage}_{\text{hybrid}} = \frac{\left| \bigcup_{i} [s_i, e_i] \right|}{N_{\text{total}}} \times 100\%$$
- Mathematical guarantee: $\text{Coverage}_{\text{hybrid}} \in [0.0\%, 100.0\%]$.
