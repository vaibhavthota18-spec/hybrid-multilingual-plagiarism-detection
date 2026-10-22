# Phase 4 Hybrid Scoring: Evidence Reconciliation & Coverage Formulas

## 1. Challenge of Overlapping Evidence Spans

When combining exact lexical matching (Winnowing) with semantic embeddings (Multilingual E5), a plagiarized passage frequently triggers both detectors:
- A student copies a paragraph verbatim: Winnowing marks it as `exact_copy` ($100\%$ match).
- The semantic embedder also flags the same paragraph with a high cosine similarity ($>0.90$).

Simply summing lexical and semantic percentages would exceed $100\%$ and inflate plagiarism estimates.

---

## 2. Token Interval Projection & Deduplication

In `HybridAnalysisService._integrate_and_score`, all findings are reconciled onto a unified token coordinate system:

1. **Submission Token Baseline**: The submission document is tokenized into $N$ ordered tokens:
   $$T = [t_0, t_1, \dots, t_{N-1}]$$
2. **Lexical Intervals**: Each lexical finding maps directly to a token range $[start_{tok}, end_{tok})$.
3. **Semantic Intervals**: Semantic character offsets $[start_{char}, end_{char})$ are mapped to token indices:
   $$start_{tok} = \min \{ i \mid t_i.start\_char \ge start_{char} \}$$
   $$end_{tok} = \max \{ i \mid t_i.end\_char \le end_{char} \} + 1$$
4. **Subsumption Deduplication**: If a semantic passage interval is largely contained within or contains an exact verbatim match, the findings are categorized separately (allowing evidence review) while their coverage masks are merged into a non-overlapping boolean union.

---

## 3. Coverage Metrics & Mathematical Formulations

### A. Overall Lexical Coverage
The proportion of submission tokens matched by exact or near-exact lexical fingerprints:
$$\text{Lexical Coverage (\%)} = \frac{|\bigcup_{l \in \text{Lexical}} [start_{l}, end_{l})|}{N} \times 100$$

### B. Overall Semantic Coverage
The proportion of submission tokens matched by paraphrased or translated semantic passages:
$$\text{Semantic Coverage (\%)} = \frac{|\bigcup_{s \in \text{Semantic}} [start_{s}, end_{s})|}{N} \times 100$$

### C. Hybrid Evidence Coverage (Union Coverage)
The non-overlapping union of all flagged tokens across both detectors:
$$\text{Hybrid Evidence Coverage (\%)} = \frac{|\bigcup_{f \in \text{Lexical} \cup \text{Semantic}} [start_{f}, end_{f})|}{N} \times 100$$
By construction:
$$\text{Hybrid Evidence Coverage} \ge \max(\text{Lexical Coverage}, \text{Semantic Coverage})$$
$$\text{Hybrid Evidence Coverage} \le 100\%$$

### D. Net Adjusted Plagiarism Score
The primary institutional indicator combines verbatim copying and conceptual rewriting:
$$\text{Net Score} = 0.40 \times \text{Lexical Coverage} + 0.60 \times \text{Semantic Coverage}$$
For pure lexical mode, $\text{Net Score} = \text{Lexical Coverage}$. For pure semantic mode, $\text{Net Score} = \text{Semantic Coverage}$.
