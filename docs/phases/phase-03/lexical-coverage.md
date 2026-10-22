# Lexical Coverage Calculation & Interval Unions

## 1. The Multi-Match Overlap Problem

In complex plagiarism cases (especially composite plagiarism where a student draws from multiple sources, or where overlapping sentences are cited), naive plagiarism engines simply sum the lengths of all detected matches.

### Failure Mode of Naive Summation:
If passage $A$ spans tokens $[10, 50]$ (length $40$) and passage $B$ spans tokens $[30, 70]$ (length $40$), summing their lengths yields $40 + 40 = 80$ tokens. In a document of 70 total tokens, this results in an impossible similarity score of $\frac{80}{70} = 114.2\%$.

---

## 2. Mathematical Interval Union Formulation

To guarantee mathematical integrity and strict bounds within $[0.0\%, 100.0\%]$, Phase 3 calculates **Lexical Coverage** using the **Union of Disjoint Intervals** across submission tokens.

Given $M$ matched spans on the candidate submission:
$$\mathcal{I} = \{ [s_1, e_1], [s_2, e_2], \dots, [s_M, e_M] \}$$

The merged non-overlapping interval set $\mathcal{U}$ is computed as:
$$\mathcal{U} = \bigcup_{i=1}^M [s_i, e_i]$$

The total matched unique token count is the sum of disjoint interval lengths:
$$L_{\text{matched}} = \sum_{[u_s, u_e] \in \mathcal{U}} (u_e - u_s + 1)$$

The **Overall Lexical Coverage Percentage** is defined as:
$$\text{Coverage}_{\text{overall}} = \left( \frac{L_{\text{matched}}}{N_{\text{submission tokens}}} \right) \times 100.0\%$$

Since $\mathcal{U} \subseteq [1, N_{\text{submission tokens}}]$, $L_{\text{matched}} \le N_{\text{submission tokens}}$, guaranteeing:
$$0.0\% \le \text{Coverage}_{\text{overall}} \le 100.0\%$$

---

## 3. Algorithm Implementation ($O(M \log M)$)

The interval union algorithm operates efficiently via sorting and linear scanning:

```python
def merge_token_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not intervals:
        return []
    
    # Sort intervals by start token index
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged = [sorted_intervals[0]]
    
    for current_start, current_end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        
        if current_start <= last_end:
            # Overlapping or contiguous intervals: merge
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            # Disjoint interval
            merged.append((current_start, current_end))
            
    return merged
```

---

## 4. Per-Source Breakdown Calculation

In addition to the global non-overlapping coverage, the system computes the specific lexical contribution of each matched reference document:

$$\text{Coverage}_{\text{source}}(R) = \left( \frac{\sum_{[s, e] \in \mathcal{U}_R} (e - s + 1)}{N_{\text{submission tokens}}} \right) \times 100.0\%$$

where $\mathcal{U}_R$ is the merged interval union of findings attributed solely to reference document $R$. This enables educators to see exactly which percentage of a paper came from Wikipedia, which came from a peer's thesis, and which came from an academic journal.
