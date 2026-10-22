# Phase 7 — Lexical Engine Final Verification

## 1. Algorithmic Baseline & Mathematical Parameters
- **Algorithm:** Winnowing with deterministic Karp-Rabin rolling hashes over token $k$-grams.
- **Parameters:**
  - $k = 25$ tokens (gram size)
  - $w = 16$ hashes (sliding window size)
  - Minimum guaranteed match threshold: $t = k + w - 1 = 40$ tokens.
- **Guarantee:** Any substring match of length $\ge t$ tokens is mathematically guaranteed to be detected.

## 2. BM25 Candidate Retrieval
- **Formula:** Okapi BM25 with standard Robertson-Spärck Jones weighting:
  $$\text{IDF}(q_i) = \ln \left( \frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1 \right)$$
- **Candidate Pool Cap:** Bounded to top $K=50$ candidates to prevent exponential comparison cost in multi-document collections.

## 3. Verified Passage Alignment
- **Method:** Local dynamic programming alignment (Smith-Waterman variant) over tokenized text.
- **Loop-Counter Safety:** Enforces bounded forward iteration in `PassageAligner` to prevent infinite loops on repetitive text sequences.
- **Code-Point Alignment:** Exact Unicode character offsets (`start_offset`, `end_offset`) verified across English, Hindi, and Telugu documents.
