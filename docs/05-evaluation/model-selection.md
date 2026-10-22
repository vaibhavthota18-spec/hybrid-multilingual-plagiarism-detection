# Multilingual AI Model Selection, Profiles & Evaluation Strategy

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Target Execution Phase:** Phase 4 (Semantic Detection) & Phase 5 (Evaluation)  
> **Date:** October 2026  

---

## 1. Candidate Model Profiles & Specifications

The evaluation framework profiles four open-weights transformer models for embedding generation and cross-encoder reranking:

| Model ID | Architecture | Dimensions | Max Tokens | License | Checkpoint Revision | Primary Role in Platform |
|---|---|---|---|---|---|---|
| **`intfloat/multilingual-e5-base`** | XLM-RoBERTa Base | 768 | 512 | MIT | Locked Git Commit SHA | **Primary Baseline Embedding Model** |
| **`sentence-transformers/LaBSE`** | BERT-based LaBSE | 768 | 512 | Apache 2.0 | Locked Git Commit SHA | Benchmark Comparison Model (Cross-Lingual) |
| **`BAAI/bge-m3`** | XLM-RoBERTa Multi-Lingual | 1024 | 8192 | MIT | Locked Git Commit SHA | Benchmark Comparison Model (Dense/Multi-Granular) |
| **`BAAI/bge-reranker-v2-m3`** | Cross-Encoder Reranker | N/A (Score) | 512 | MIT | Locked Git Commit SHA | **Conditional Stage 2 Reranker** |

> **Neutrality Directive:** No model is assumed to be superior prior to empirical benchmark execution in Phase 5. `multilingual-e5-base` is chosen as the operational baseline due to its balanced inference speed and parameter size (~1.1 GB memory).

---

## 2. Baseline Model Specification: `intfloat/multilingual-e5-base`

### 2.1 Input Prefix Protocol
E5 models are pre-trained with asymmetric task prefixes:
- **Index Documents (Reference Passages):** MUST be prefixed with `"passage: "`:
  ```python
  formatted_text = f"passage: {passage_text.strip()}"
  ```
- **Query Documents (Submission Passages):** MUST be prefixed with `"query: "`:
  ```python
  formatted_text = f"query: {query_text.strip()}"
  ```
*Failure to include prefixes degrades embedding retrieval accuracy by up to 15%.*

### 2.2 L2 Vector Normalization Invariant
All embeddings output by the model must be explicitly unit-normalized:
$$v_{\text{norm}} = \frac{v}{||v||_2} = \frac{v}{\sqrt{\sum_{i=1}^{768} v_i^2}}$$
This ensures that Euclidean inner product in `pgvector` (`v1 <#> v2`) is mathematically identical to cosine similarity:
$$\text{sim}(u, v) = u \cdot v$$

### 2.3 Hardware & Batching Strategy
- **Baseline Deployment:** 8 CPU cores (Intel/AMD x86_64 or ARM64).
- **Batch Size:** 16 passages per forward pass under CPU inference.
- **Quantization:** FP32 baseline; INT8 dynamic quantization evaluated conditionally if CPU latency exceeds targets.

---

## 3. Benchmark Comparison Models (Phase 5 Ablation)

### 3.1 `sentence-transformers/LaBSE` (Language-Agnostic BERT Sentence Embeddings)
- **Strengths:** Optimized specifically for bitext sentence translation mining across 109 languages; exceptional cross-lingual alignment.
- **Weaknesses:** Slightly larger parameter footprint, slower tokenization, lacks asymmetric query/passage training.
- **Role:** Direct competitor to E5 on cross-lingual EN-HI, EN-TE, and HI-TE translation pairs.

### 3.2 `BAAI/bge-m3`
- **Strengths:** Supports multi-functionality (dense, sparse, multi-vector), longer context window (up to 8,192 tokens), top rankings on MTEB Indic benchmarks.
- **Weaknesses:** 1024-dimensional embeddings (33% higher vector storage in PostgreSQL), higher compute requirement.
- **Role:** High-capacity alternative if 768-dim models exhibit insufficient nuance on complex academic paraphrasing.

---

## 4. Conditional Cross-Encoder: `BAAI/bge-reranker-v2-m3`

A Cross-Encoder takes the concatenation of query passage and candidate passage `[CLS] query [SEP] candidate [EOS]` and outputs a direct similarity probability ($0.0 \dots 1.0$).
- **Deployment Status:** Disabled by default (`ENABLE_CROSS_ENCODER_RERANKING=false`).
- **Activation Gate:** Activated only if Stage 1 candidate retrieval provides sufficient recall ($\ge 85\%$) but Stage 2 alignment precision on paraphrased text is below 70%.
- **Operational Constraint:** Evaluated only over the top 20 fused candidates to protect worker processing time.

---

## 5. Model Versioning & Reindexing Schema

To ensure vector database safety:
1. Every embedding in `embeddings` references `model_configurations.id`.
2. Mismatched model cosine similarity computations are prevented at the database level.
3. Model weights are downloaded and pinned via frozen Git commit SHAs, never relying on floating tags (`latest` or `main`).
