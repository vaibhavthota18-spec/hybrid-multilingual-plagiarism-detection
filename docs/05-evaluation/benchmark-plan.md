# Empirical Benchmark Plan & Ablation Experiments

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Target Execution Phase:** Phase 5 (Multilingual Evaluation)  
> **Date:** October 2026  

---

## 1. Evaluation Philosophy

In accordance with ADR-0008, no algorithm, retrieval channel, or threshold calibration will be declared ready for production without documented empirical benchmarking across standardized evaluation splits. Every performance claim must be verifiable through reproducible scripts in `evaluation/scripts/`.

---

## 2. Comprehensive Ablation Experiment Matrix

To quantify the independent and synergistic contributions of each retrieval channel, the evaluation framework executes twelve systematic experiments:

| Experiment ID | Pipeline Configuration | Primary Metric Evaluated | Purpose & Architectural Question |
|---|---|---|---|
| **EXP-01** | Winnowing Only ($k=25, w=16$) | Precision, Exact Match Recall | Establish baseline verbatim copy detection and compute hash collision rates. |
| **EXP-02** | Okapi BM25 Only | Keyword Recall@20, MAP | Evaluate keyword-based near-duplicate candidate retrieval without embeddings. |
| **EXP-03** | Semantic Embeddings Only (`multilingual-e5-base`) | Semantic Recall@20, MRR | Evaluate dense retrieval quality on paraphrases and translations without lexical cues. |
| **EXP-04** | Lexical Pipeline (Winnowing + BM25) | Combined Lexical Recall@20 | Measure candidate retrieval when combining rolling hashes with keyword indexing. |
| **EXP-05** | Semantic Pipeline (Dense Vector + Threshold Filtering) | Paraphrase F1, False Discovery Rate | Evaluate dense vector performance on hard negative academic passages. |
| **EXP-06** | Full Hybrid Retrieval (Stage 1: Lexical + Dense) | Overall Recall@20, Stage 1 Latency | Quantify recall gains from unifying lexical and semantic channels. Target: $\ge 90\%$. |
| **EXP-07** | Conditional Cross-Encoder Reranking (`bge-reranker-v2-m3`) | Precision@10, NDCG@10, Latency Overhead | Determine if reranking top-20 candidates justifies additional worker inference time. |
| **EXP-08** | Exact Vector Search vs. HNSW Indexing | ANN Recall Degradation, Query Latency | Measure if HNSW achieves $\ge 98\%$ recall relative to exact search at varying corpus scales. |
| **EXP-09** | Token-Level Local Alignment vs. Sentence Bounding | Mean Span IoU, Boundary Precision | Verify that modified Smith-Waterman alignment outperforms coarse sentence bounding. |
| **EXP-10** | Monolingual vs. Cross-Lingual Evaluation | Cross-lingual Recall@20 (EN-HI, EN-TE, HI-TE) | Measure translation similarity detection across all six language pairs. |
| **EXP-11** | Scalability & Latency Stress Test | p50, p95, p99 Latency at 1k, 5k, 10k Corpus Docs | Profile memory and throughput on 8 CPU cores / 16 GB RAM to verify 180s target. |
| **EXP-12** | Failure Analysis & Hard-Negative Profiling | Hard-Negative False Positive Rate | Profile false positive triggers on textbook definitions, standard formulas, and citations. |

---

## 3. Detailed Experimental Procedures

### 3.1 Stage 1 Candidate Retrieval Evaluation
- **Procedure:** Input query passages from the validation and test splits into Stage 1 retrieval modules. Measure how frequently the true matching reference passage appears in the top-$K$ candidate list ($K \in \{5, 10, 20, 50\}$).
- **Target:** Source Recall@20 $\ge 90\%$ for same-language pairs; $\ge 80\%$ for cross-language pairs.

### 3.2 Stage 2 Passage Alignment & Boundary Precision
- **Procedure:** For candidate passage pairs with known ground-truth character boundaries, run token-level local sequence alignment. Calculate the Intersection-over-Union (IoU) between predicted span $[s_{\text{pred}}, e_{\text{pred}})$ and gold span $[s_{\text{gold}}, e_{\text{gold}})$:
  $$\text{IoU} = \frac{|[s_{\text{pred}}, e_{\text{pred}}) \cap [s_{\text{gold}}, e_{\text{gold}})|}{|[s_{\text{pred}}, e_{\text{pred}}) \cup [s_{\text{gold}}, e_{\text{gold}})|}$$
- **Target:** Mean span IoU $\ge 0.80$; Highlight boundary accuracy on test fixtures $\ge 99\%$.

### 3.3 Scalability & Resource Profiling (EXP-11)
- **Infrastructure:** Standard containerized environment (8 CPU cores, 16 GB RAM, no GPU).
- **Workload:** 10-page submission document (approx. 3,500 words / 45 passages) queried against a pre-indexed 1,000-document reference corpus (approx. 25,000 passages).
- **Timing Boundaries:**
  - *Included:* Text extraction, Unicode normalization, passage segmentation, query fingerprinting, query embedding generation, pgvector search, candidate fusion, local alignment, deduplicated scoring, and result serialization.
  - *Excluded:* Client-to-server network file transfer time, browser DOM rendering.
- **Target:** p95 latency $\le 180$ seconds.

### 3.4 Failure Analysis & Error Categorization (EXP-12)
Every false positive and false negative generated on the evaluation set must be tagged into one of six error classes:
1. `ERR_INDIC_TOKENIZATION`: Script ligatures or compound word splits in Hindi/Telugu corrupted tokens.
2. `ERR_SEMANTIC_DRIFT`: High vector similarity on topically related but non-plagiarized academic arguments.
3. `ERR_SHORT_FRAGMENT`: Verbatim match below the 10-token threshold ignored by Winnowing.
4. `ERR_TRANSLATION_IDIOM`: Idiomatic regional translation unaligned in Multilingual E5 vector space.
5. `ERR_CITATION_MISSED`: Malformed quotation mark format prevented automated exclusion.
6. `ERR_INDEX_TRUNCATION`: True source ranked at position 21+ in Stage 1 and missed by top-20 Stage 2 gate.
