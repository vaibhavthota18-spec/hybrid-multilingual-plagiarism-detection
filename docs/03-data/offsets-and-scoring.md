# Offsets Mathematics & Similarity Scoring Formulas

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Canonical Text Offset Model

All textual positions in this platform are defined using **zero-based, half-open Unicode code-point intervals**:
$$\text{Span} = [s, e) = \{ i \in \mathbb{N} \mid s \le i < e \}$$
where $s$ is the inclusive start index and $e$ is the exclusive end index into the raw extracted string $T_{\text{orig}}$.

### Invariants
1. **Length:** The number of Unicode characters in span $[s, e)$ is $\Delta = e - s$.
2. **Adjacency:** Two contiguous spans $[s_1, m)$ and $[m, e_2)$ join seamlessly into $[s_1, e_2)$.
3. **Empty Span:** If $s = e$, the span contains 0 characters.

---

## 2. Eligible Text Positions & Exclusions

In academic text evaluation, counting trailing bibliography sections or excluded direct quotes against the author skews similarity measurements. Therefore, we define the **Eligible Text Positions** set $E \subseteq \mathbb{N}$:

Let $L = |T_{\text{orig}}|$ be the total code-point length of the raw extracted submission text.
Let $W \subset \{0, \dots, L-1\}$ be the set of whitespace or non-printable character positions.
Let $X \subset \{0, \dots, L-1\}$ be the set of positions covered by active exclusions (e.g., properly formatted block quotations or bibliography lists).

The set of eligible positions is:
$$E = \{ i \in \{0, \dots, L-1\} \setminus W \mid i \notin X \}$$

The count of eligible positions is $N_{\text{eligible}} = |E|$.

### Edge Case Guardrail
If $N_{\text{eligible}} = 0$ (e.g., an empty file, a document containing only spaces, or an entire document marked excluded), the system defines:
$$\text{Lexical Coverage} = 0.00\%$$
$$\text{Semantic Coverage} = 0.00\%$$
$$\text{Net Score} = 0.00\%$$
Division-by-zero is strictly intercepted in backend scoring logic.

---

## 3. Geometric Interval Union & Overlap Deduplication

When multiple reference documents (or multiple passages from the same source) match overlapping sections of the submission text, a naive summation of matched lengths produces mathematically impossible coverage values exceeding 100%.

### Mathematical Deduplication Rule
Let $\{ [s_1, e_1), [s_2, e_2), \dots, [s_m, e_m) \}$ be the collection of verified matching intervals in the submission text.
The **Unique Matched Interval Union** $\mathcal{U}$ is the geometric union of all active intervals:
$$\mathcal{U} = \bigcup_{k=1}^m [s_k, e_k)$$

The count of unique matched positions is:
$$M_{\text{matched}} = |\{ i \in \mathcal{U} \cap E \}|$$

### Coverage Formula
$$\text{Coverage (\%)} = 100 \times \frac{M_{\text{matched}}}{N_{\text{eligible}}}$$

> **Mandatory Rule:** Never sum overlapping source matches twice. The aggregate coverage is strictly bounded by $[0.00\%, 100.00\%]$.

---

## 4. Dual Coverage Metrics

The platform reports two distinct, un-conflated coverage percentages:

### 4.1 Lexical Coverage (Verbatim & Near-Verbatim)
Calculated strictly over findings classified as:
- `EXACT_COPY` (token overlap $\ge 90\%$, token-level edit distance $\le 2$)
- `NEAR_EXACT_REWRITE` (token overlap $\ge 70\%$, high lexical winnowing agreement)

$$\text{Lexical Coverage (\%)} = 100 \times \frac{|\mathcal{U}_{\text{lexical}} \cap E|}{N_{\text{eligible}}}$$

### 4.2 Potential Semantic Coverage (Paraphrases & Translations)
Calculated strictly over findings classified as:
- `PARAPHRASE` (cosine similarity $\ge \tau_{\text{lang}}$, token overlap $< 70\%$)
- `POTENTIAL_TRANSLATION` (multilingual cosine similarity $\ge \tau_{\text{cross}}$, cross-language flag detected)

$$\text{Semantic Coverage (\%)} = 100 \times \frac{|\mathcal{U}_{\text{semantic}} \cap E|}{N_{\text{eligible}}}$$

### Ethical Warning on Semantic Similarity
> **CRITICAL ETHICAL DIRECTIVE:**  
> Dense vector cosine similarity ($\text{sim}(u, v) = u \cdot v$) measures conceptual proximity in high-dimensional embedding space. **Cosine similarity is NOT a probability of plagiarism.** A high semantic score indicates that two passages discuss closely related concepts or use equivalent translated terminology. It requires human academic verification to determine whether copying, paraphrasing, or independent scholarly consensus occurred.

---

## 5. Finding Categorization Decision Matrix & Parameter Calibration

### 5.1 Winnowing Parameter Definitions & Algorithm Invariants
The lexical fingerprinting pipeline relies on the Winnowing algorithm over normalized character sequences. The parameter semantics are rigorously defined as follows:

- **Character $k$-Gram Size ($k_{\text{char}}$):** Substring length of consecutive normalized Unicode code points. Baseline setting is $k_{\text{char}} = 25$ characters.
- **Window Size ($w_{\text{hashes}}$):** The sliding window size is defined as **$w_{\text{hashes}} = 16$ consecutive $k$-gram hashes**, NOT raw characters.
- **Window Text Span:** Because each of the 16 consecutive hashes represents a 25-character $k$-gram offset by 1 character, a window of $w_{\text{hashes}} = 16$ spans:
  $$\text{Window Span} = k + w - 1 = 25 + 16 - 1 = 40 \text{ characters}$$
- **Theoretical Match Guarantee ($t$):** Subject to standard algorithm assumptions and preprocessing normalization, any shared verbatim sequence of length:
  $$t \ge k + w - 1 = 40 \text{ characters}$$
  is mathematically guaranteed to share at least one identical fingerprint hash.
- **Fingerprint Selection & Tie-Breaking:** In each sliding window of $w$ hashes, the minimum hash value is selected. If multiple positions within the window contain the identical minimum hash value, the algorithm selects the **rightmost minimum hash** (the standard convention to maximize the forward leap of subsequent windows and minimize total index volume).
- **Hash Collision Verification:** 64-bit rolling hashes reduce storage footprint. Hash matches in Stage 1 coarse retrieval are strictly verified in Stage 2 against raw text tokens and character offsets, discarding any spurious hash collisions.
- **Provisional Engineering Status:** The values $k_{\text{char}} = 25, w_{\text{hashes}} = 16$ are provisional baselines. During Phase 3 and Phase 5 development, parameter sweeps across $k \in [15, 35]$ characters and $w \in [8, 32]$ hashes on development splits will evaluate the trade-off between index storage density, query throughput, and false-discovery rate across English, Hindi, and Telugu scripts.

### 5.2 Similarity Threshold Policy & Development Calibration
Preliminary cosine similarity figures are **provisional engineering baselines**, not mandatory production minimum cutoffs. Universal similarity cutoffs are strictly prohibited because dense vector representation geometry differs substantially across scripts and language families.

#### Calibration Procedure (Development Data):
1. **Calibration Sets:** Calibration is performed exclusively on the development and validation partitions (`docs/05-evaluation/dataset-and-annotation.md`), utilizing both positive match pairs (verbatim, rewrites, paraphrases, translations) and hard-negative academic examples (topical similarity, standard definitions, properly formatted quotes).
2. **Optimization Objective:** Threshold sweeps ($\tau \in [0.70, 0.95]$ in $0.01$ increments) select operating points that maximize Paraphrase/Translation F1 while strictly constraining the Hard-Negative False-Positive Rate to $\le 5.0\%$.
3. **Threshold Freezing Rule:** All calibrated thresholds MUST be formally frozen on the validation split prior to running final evaluations on the held-out test split.
4. **Independent Language-Pair Calibration:** Thresholds are calibrated and evaluated separately across all six supported language relationships:
   - **Monolingual English ($\tau_{\text{EN-EN}}$):** Provisional baseline target $\ge 0.84$.
   - **Monolingual Hindi ($\tau_{\text{HI-HI}}$):** Provisional baseline target $\ge 0.82$.
   - **Monolingual Telugu ($\tau_{\text{TE-TE}}$):** Provisional baseline target $\ge 0.80$.
   - **Cross-Lingual English $\leftrightarrow$ Hindi ($\tau_{\text{EN-HI}}$):** Provisional baseline target $\ge 0.79$.
   - **Cross-Lingual English $\leftrightarrow$ Telugu ($\tau_{\text{EN-TE}}$):** Provisional baseline target $\ge 0.77$.
   - **Cross-Lingual Hindi $\leftrightarrow$ Telugu ($\tau_{\text{HI-TE}}$):** Provisional baseline target $\ge 0.78$.

### 5.3 Reconciled Three-Tier Short-Passage Rules
To eliminate contradictory passage-length thresholds between candidate retrieval and local sequence alignment, the platform enforces three distinct pipeline rules:

1. **Tier 1: Candidate Retrieval Eligibility (Stage 1 Segmentation)**
   - Short text fragments ($<30$ words or $<150$ characters, such as section sub-headings or single-sentence paragraphs) MUST NOT be discarded during segmentation. They are merged with the subsequent adjacent passage, ensuring zero unindexed text gaps.
   - Standalone short documents ($<100$ words) are indexed as a single self-contained passage rather than filtered out.
2. **Tier 2: Verification & Alignment Behavior (Stage 2)**
   - Token-level local alignment (modified Smith-Waterman) operates across candidate passage pairs, aligning matching token spans down to a minimum alignment span of **$\ge 6$ tokens**. This captures short sentences, technical definitions, and idiomatic phrases.
3. **Tier 3: Final Reporting & Confidence Requirements (Stage 3 Scoring)**
   - **Long Verbatim Spans ($\ge 10$ tokens):** Classified as `EXACT_COPY` or `NEAR_EXACT_REWRITE` with `HIGH` confidence.
   - **Short Matching Spans (6–9 tokens):** Classified as `LOW_CONFIDENCE` and annotated with the label `"Short or Common-Text Overlap"` unless they form part of a multi-span cluster within the same passage, preventing standard academic idioms from skewing plagiarism assessments.
   - **Semantic Paraphrases & Translations ($\ge 12$ tokens):** Paraphrase and cross-lingual translation classifications require a minimum span length of $\ge 12$ tokens to prevent isolated shared concepts or common vocabulary from generating false-positive semantic flags.

| Category | Lexical Token Overlap | Dense Vector Cosine Sim | Minimum Token Span | Confidence / Classification Policy |
|---|---|---|---|---|
| `EXACT_COPY` | $\ge 90\%$ | N/A (or $\ge 0.90$) | $\ge 10$ tokens | High confidence verbatim text reuse. |
| `EXACT_COPY` (Short) | $\ge 90\%$ | N/A | 6–9 tokens | Low confidence; labeled as "Short or Common-Text Overlap". |
| `NEAR_EXACT_REWRITE` | $70\% \le \text{overlap} < 90\%$ | $\ge \tau_{\text{lang}} + 0.03$ | $\ge 10$ tokens | High/Moderate confidence minor word alterations or synonym shifts. |
| `PARAPHRASE` | $< 70\%$ | $\ge \tau_{\text{lang}}$ (calibrated) | $\ge 12$ tokens | Semantic idea reuse; requires human verification. |
| `POTENTIAL_TRANSLATION` | $< 30\%$ | $\ge \tau_{\text{cross}}$ (calibrated) | $\ge 12$ tokens | Cross-language semantic alignment; requires human verification. |

---

## 6. Comprehensive Worked Example

### Scenario Setup
- A submitted paper has $L = 1,000$ Unicode code points.
- Whitespace positions $|W| = 150$.
- Quotation exclusions: Span $[200, 300)$ is inside quotation marks ($100$ characters, of which 15 are spaces). Excluded non-whitespace positions = 85.
- **Eligible positions:** $N_{\text{eligible}} = 1000 - 150 - 85 = 765$ positions.

### Detected Findings
- **Finding 1 (Source A, Exact):** Span $[50, 150)$ (100 code points, 15 spaces $\rightarrow$ 85 eligible chars).
- **Finding 2 (Source B, Exact, Overlapping):** Span $[120, 250)$ (130 code points, 20 spaces).
  - Notice overlap: $[120, 150)$ overlaps with Finding 1!
  - Notice exclusion overlap: $[200, 250)$ overlaps with the excluded quote span $[200, 300)$!
- **Finding 3 (Source C, Paraphrase):** Span $[500, 650)$ (150 code points, 22 spaces $\rightarrow$ 128 eligible chars).

### Calculation
1. **Raw Interval Union for Lexical Matches:**
   $$\mathcal{U}_{\text{lex}} = [50, 150) \cup [120, 250) = [50, 250)$$
2. **Exclude Quoted Span $[200, 300)$:**
   $$\mathcal{U}_{\text{lex}} \setminus [200, 300) = [50, 200)$$
   Length of $[50, 200) = 150$ characters.
   Non-whitespace eligible positions in $[50, 200) = 128$ characters.
3. **Lexical Coverage:**
   $$\text{Lexical Coverage} = 100 \times \frac{128}{765} = 16.73\%$$
   *(If naively summed: Finding 1 (85) + Finding 2 (110) = 195 chars = 25.49% — an incorrect inflation of nearly 9 percentage points!)*
4. **Semantic Coverage (Finding 3):**
   $$\text{Semantic Coverage} = 100 \times \frac{128}{765} = 16.73\%$$
5. **Per-Source Attribution Breakdown:**
   - Source A: Attributed span $[50, 150) \cap E = 85$ chars ($11.11\%$).
   - Source B: Attributed span $[120, 200) \cap E = 68$ chars ($8.89\%$).
   - Note: The sum of per-source coverage ($11.11\% + 8.89\% = 20.00\%$) exceeds the deduplicated lexical coverage ($16.73\%$) because of the shared $[120, 150)$ span. Both numbers are reported transparently.
