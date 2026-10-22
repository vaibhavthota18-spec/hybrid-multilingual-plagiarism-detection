# ADR-0003: Two-Stage Hybrid Detection Pipeline (Lexical + Semantic)

- **Status:** Accepted
- **Deciders:** Principal Software Architect, Information Retrieval Engineer, NLP/AI Engineer
- **Date:** October 2026
- **Technical Story:** Core detection architecture combining lexical and neural models

---

## Context
Purely lexical systems (e.g., n-grams, string matching) are fast ($O(1)$ index lookups) and pinpoint exact verbatim copies, but fail completely when text is paraphrased, synonym-substituted, or translated into another language. Conversely, purely neural embedding systems capture cross-lingual and semantic meaning, but are computationally expensive ($O(D \cdot N)$), lack exact word boundary precision, and produce false positives on short standard phrases.

## Decision
We implement a **Two-Stage Hybrid Detection Pipeline**:
- **Stage 1 (Coarse Candidate Retrieval):** High-recall parallel retrieval combining:
  1. *Lexical Channel:* Winnowing rolling-hash fingerprint matches (provisional character $k$-gram $k_{\text{char}}=25$ characters, window $w_{\text{hashes}}=16$ consecutive hashes covering $k+w-1=40$ characters with guarantee $t \ge 40$, rightmost tie-break, tuned across $k \in [15, 35]$ and $w \in [8, 32]$ in development) and Okapi BM25 token scores.
  2. *Semantic Channel:* Dense vector nearest-neighbor search (`multilingual-e5-base` via PostgreSQL `pgvector` negative inner product `<#>`).
  Candidates are merged, deduplicated, and ranked.
- **Stage 2 (Granular Verification & Alignment):** High-precision verification applying:
  1. *Token-Level Local Alignment:* Modified Smith-Waterman sequence alignment (matching spans $\ge 6$ tokens) to pinpoint exact start/end character offsets.
  2. *Evidence Aggregation:* Three-tier classification and separate calculation of Lexical Coverage (exact) and Potential Semantic Coverage (paraphrase/translation).

## Alternatives Considered
1. **Single-Stage Exhaustive Neural Alignment:** Running transformer cross-encoders across every passage pair in a 1,000-document corpus. Rejected due to combinatorial explosion and extreme latency ($>30$ minutes per document).
2. **Lexical-Only Detection:** Rejected as it completely fails to meet the core project requirement of cross-lingual plagiarism detection (English $\leftrightarrow$ Hindi $\leftrightarrow$ Telugu).

## Rationale
The two-stage design provides optimal balance: Stage 1 filters millions of candidate pairs down to the top 20–50 relevant passages in $<500$ ms, allowing Stage 2 to execute computationally rigorous token alignment within seconds.

## Consequences & Trade-offs
- **Positive:** Robust against verbatim copying, light rewriting, heavy paraphrasing, and cross-lingual translation.
- **Negative:** Requires maintaining two indexing pipelines (Winnowing hashes and dense vectors).

## Validation Requirements
Recall@20 of Stage 1 on the benchmark suite must achieve $\ge 90\%$ for lexical copies and $\ge 80\%$ for cross-lingual translations.
