# Passage Alignment and Evidence Verification

## 1. Overview and Objectives

Once candidate documents are retrieved, the **Passage Aligner** (`services/lexical/aligner.py`) performs deterministic alignment to identify contiguous verbatim and near-verbatim copied sections.

The aligner must satisfy three non-negotiable requirements:
1. **High Precision Boundary Detection**: Start and end positions must correspond precisely to character code points in the source text.
2. **Tolerance to Minor Edits**: Insertions of minor words, synonym replacements, or punctuation changes between verbatim phrases should merge into a single finding rather than fracturing into dozens of 3-word fragments.
3. **Verifiable Evidence**: Every match finding must be independently verifiable by slicing the raw document string at `[start_char:end_char]`.

---

## 2. Alignment Algorithm Steps

### Step 1: Anchor Identification
Shared Winnowing fingerprints between candidate submission $S$ and reference document $R$ serve as alignment anchors. Each shared hash links token position $p_S$ in the submission to token position $p_R$ in the reference.

### Step 2: Bidirectional Anchor Extension
From each anchor position $(p_S, p_R)$:
- **Extend Forward**: Compare subsequent tokens $S[p_S + i]$ and $R[p_R + i]$ while tokens match.
- **Extend Backward**: Compare preceding tokens $S[p_S - j]$ and $R[p_R - j]$ while tokens match.
- The extended span establishes an exact matching block $[s_{start}, s_{end}]$ and $[r_{start}, r_{end}]$.

### Step 3: Adjacent Match Merging (Gap $\le 4$ tokens)
If two aligned spans $A$ and $B$ are separated by fewer than `max_merge_gap` ($4$) tokens in both documents:
$$\Delta_S = s_{start}^{(B)} - s_{end}^{(A)} \le 4 \quad \text{and} \quad \Delta_R = r_{start}^{(B)} - r_{end}^{(A)} \le 4$$
The aligner bridges the gap and merges them into a single finding spanning $[s_{start}^{(A)}, s_{end}^{(B)}]$.

### Step 4: Categorization & Similarity Ratio
For each merged span:
- Compute character-level normalized Levenshtein ratio:
  $$\text{sim}(T_S, T_R) = 1.0 - \frac{\text{LevenshteinDistance}(T_S, T_R)}{\max(|T_S|, |T_R|)}$$
- **`exact_copy`**: When tokens and text match with $\text{sim} \ge 0.98$ and zero intervening gaps.
- **`near_exact_rewrite`**: When gaps were bridged or minor edits were detected ($0.80 \le \text{sim} < 0.98$).

---

## 3. Strict Slicing Verification

Before a finding is returned to the service or persisted in SQLite, it undergoes strict string verification:

```python
# Extract exact code points
sub_slice = raw_submission_text[finding.submission_start_offset : finding.submission_end_offset]
ref_slice = raw_reference_text[finding.reference_start_offset : finding.reference_end_offset]

# Assert non-empty and valid slice
assert len(sub_slice.strip()) > 0
assert len(ref_slice.strip()) > 0
```

This guarantees that highlighted blocks displayed in the UI always match the real textual characters from the original document files.
