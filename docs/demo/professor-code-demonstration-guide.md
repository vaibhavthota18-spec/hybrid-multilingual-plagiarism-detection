# University Professor Demonstration Guide: Architecture & Algorithms

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Presentation Time:** 5 to 7 Minutes  
**Demonstration Tool:** Visual Studio Code & Native Terminal  

---

## 1. Executive Summary for the Professor

The system is a production-grade, hybrid lexical and semantic multilingual plagiarism engine supporting **English, Hindi, and Telugu**. It solves the two classic failure modes in plagiarism detection:
1. **Lexical evasion:** Paraphrasing, word substitution, and translation across languages that defeat pure string matching.
2. **Semantic false positives:** High semantic similarity on common topical prose that lacks verbatim overlap.

The system combines **Winnowing with Rolling Hashes** and **BM25 retrieval** for lexical matches with **Multilingual E5 Small Embeddings (384-dimensional)** and **Cosine Vector Search** for semantic and cross-lingual matches. The findings are unified via an **Interval Union algorithm** that guarantees mathematical defensibility ($0.0\% \le \text{coverage} \le 100.0\%$), and dynamic **human reviewer adjustments** preserve raw AI scores while producing transparent audit reports.

---

## 2. 5–7 Minute Step-by-Step Demonstration Flow

### Minute 1: Lexical Ingestion & Rolling Hash Fingerprinting
- **What to say:**
  > "Professor, let's look at the lexical detection layer. First, documents are normalized to Unicode NFC while preserving Indic combining marks (matras and halants). We tokenize the text and generate a deterministic 64-bit FNV-1a hash for each token. We then apply an $O(1)$ polynomial rolling hash over token $k$-grams using a Mersenne prime modulus ($M_{61} = 2^{61}-1$)."
- **Code to show:**
  - `apps/backend/src/plagiarism/services/lexical/rolling_hash.py`, line 65 (`RollingHash.compute_all`)
  - Highlight the $O(1)$ window sliding formula on lines 90–103:
    $$\text{Hash}_{\text{new}} = \left( \left( \text{Hash}_{\text{old}} - h_{\text{out}} \cdot \text{base}^{k-1} \right) \cdot \text{base} + h_{\text{in}} \right) \pmod{M_{61}}$$

---

### Minute 2: Winnowing Guarantee ($k=25, w=16$)
- **What to say:**
  > "Next is the Schleimer, Wilkerson, and Aiken (2003) Winnowing algorithm. With $k=25$ tokens and window $w=16$, any shared sequence of length at least $t = k + w - 1 = 40$ tokens is mathematically guaranteed to share at least one fingerprint. To achieve $O(N)$ linear complexity, I implemented a monotonic double-ended queue (deque) with rightmost tie-breaking."
- **Code to show:**
  - `apps/backend/src/plagiarism/services/lexical/winnowing.py`, line 106 (`fingerprint_tokens`)
  - Point out lines 116–135 where the monotonic deque maintains minimum hashes and breaks ties in favor of the rightmost position.

---

### Minute 3: Rapid Candidate Filtering with Okapi BM25
- **What to say:**
  > "When comparing a document against a large corpus, running fine-grained alignment against every document is computationally wasteful. We index reference documents using Okapi BM25 with standard parameters $k_1 = 1.2$ and $b = 0.75$, using Robertson-Spärck Jones IDF smoothing to prevent negative weights. This retrieves the top $K$ candidate documents in milliseconds."
- **Code to show:**
  - `apps/backend/src/plagiarism/services/lexical/bm25.py`, line 57 (`score_document`) and line 49 (`idf`)

---

### Minute 4: AI Semantic Engine & Cross-Language Detection
- **What to say:**
  > "For semantic and cross-language plagiarism (such as an English passage translated to Telugu or Hindi, or heavy paraphrasing), we integrate Microsoft's `intfloat/multilingual-e5-small` model. Passages are segmented into token budgets of 128 tokens. Following E5 architecture, query passages are prefixed with `query: ` and reference passages with `passage: `, producing 384-dimensional L2-normalized dense embeddings. Cosine similarity is computed via dot products:
  > $$\text{sim}(\mathbf{q}, \mathbf{r}) = \mathbf{q} \cdot \mathbf{r}^T$$
  > We evaluate findings against calibrated thresholds: $\ge 0.82$ for monolingual paraphrasing and $\ge 0.78$ for cross-language translation."
- **Code to show:**
  - `apps/backend/src/plagiarism/services/semantic/provider.py`, lines 128–173 (`encode_queries`, `encode_passages`)
  - `apps/backend/src/plagiarism/storage/vector_store.py`, line 292 (`np.dot(query_vectors, ref_matrix.T)`)
  - `apps/backend/src/plagiarism/services/semantic/matcher.py`, lines 197–215 (Cross-language classification logic)

---

### Minute 5: Hybrid Evidence Fusion & Interval Union Defensibility
- **What to say:**
  > "A major problem in existing plagiarism tools is score inflation caused by double-counting overlapping lexical and semantic matches. In our `HybridAnalysisService`, we project all matched spans onto token index intervals $[s_i, e_i)$ on the submission document. We run an Interval Union algorithm that merges overlapping intervals. The net score is bounded by the total unique token union:
  > $$\text{Coverage} = \frac{\left| \bigcup_{i} [s_i, e_i) \right|}{N_{\text{total}}} \times 100\%$$
  > In hybrid mode, the net score is weighted as:
  > $$\text{Net Score} = 0.40 \cdot \text{Lexical} + 0.60 \cdot \text{Semantic}$$"
- **Code to show:**
  - `apps/backend/src/plagiarism/services/lexical/coverage.py`, line 22 (`merge_token_intervals`)
  - `apps/backend/src/plagiarism/services/hybrid_service.py`, lines 354–370 (Deduplication) and lines 398–423 (Interval union scoring)

---

### Minute 6: Human Reviewer Audit & Dynamic Recalculation
- **What to say:**
  > "In academic and legal integrity investigations, automated AI scores cannot be arbitrary. When an instructor reviews findings and marks an excerpt as 'quoted/cited' or 'exclude', our system preserves the raw model scores in the database while dynamically recomputing the 'reviewer-adjusted coverage' in real time using the active interval union."
- **Code to show:**
  - `apps/backend/src/plagiarism/services/hybrid_service.py`, lines 475–552 (`recompute_reviewer_adjusted_coverage`)

---

### Minute 7: Live Execution & Test Suite
- **What to say:**
  > "Finally, let me demonstrate our automated test suite running against these exact mathematical invariants."
- **Action:**
  - Run in terminal:
    ```powershell
    apps\backend\.venv\Scripts\python.exe -m pytest apps/backend/tests/test_lexical_algorithms.py -v
    ```
  - Point out that all 7 lexical mathematical tests pass in **0.04 seconds**.
  - Show the frontend results at `http://localhost:5173` with side-by-side highlighting and PDF export.

---

## 3. Likely Professor Questions & Model Answers

| Question | Model Answer | Source Reference |
|---|---|---|
| **"Why did you choose Winnowing over standard Rabin-Karp or $n$-grams?"** | Standard $n$-grams generate $O(N)$ hashes and massive index sizes. Winnowing samples a bounded fraction ($\sim 2/w$) of hashes while providing a mathematical guarantee: any shared sequence of length $\ge k+w-1$ tokens is guaranteed to match at least one fingerprint. | `services/lexical/winnowing.py:25` |
| **"Why not use Python's built-in `hash()` function?"** | Python's `hash()` employs process-level salt randomization (`PYTHONHASHSEED`). Hashes computed during indexing would not match hashes computed during analysis in a different process. We implemented 64-bit FNV-1a for 100% platform-independent determinism. | `services/lexical/rolling_hash.py:18` |
| **"How do you handle Indian languages like Telugu and Hindi?"** | Standard tokenizers strip combining marks (matras and halants). We perform Unicode NFC normalization and use Unicode script block boundaries ($0x0900$–$0x097F$ for Devanagari, $0x0C00$–$0x0C7F$ for Telugu) to preserve character integrity, and use Multilingual E5 for cross-lingual vector embeddings. | `services/preprocessing.py:27` |
| **"How do you prevent plagiarism scores exceeding 100% when multiple sources overlap?"** | We convert all character spans into token intervals and run an interval union algorithm `merge_token_intervals()`. Overlapping regions are merged into disjoint spans so each token in the submission is counted at most once. | `services/lexical/coverage.py:22` |
