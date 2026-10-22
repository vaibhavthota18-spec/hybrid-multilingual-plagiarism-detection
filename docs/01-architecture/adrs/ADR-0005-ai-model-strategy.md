# ADR-0005: AI Model Selection & Strict Embedding Versioning Strategy

- **Status:** Accepted
- **Deciders:** Principal Software Architect, NLP/AI Engineer, Machine Learning Evaluation Engineer
- **Date:** October 2026
- **Technical Story:** Multilingual embedding foundation, revision locking, and model deprecation

---

## Context
The platform requires multilingual sentence representation across English, Hindi, and Telugu. Furthermore, embeddings from different transformer models or different checkpoint revisions inhabit incompatible vector spaces. Calculating cosine similarity between a vector from Model A and a vector from Model B generates meaningless numbers.

## Decision
1. **Initial Baseline Model:** We adopt **`intfloat/multilingual-e5-base`** (768 dimensions, 512 max tokens).
   - Prefix Protocol: Passage texts must be prefixed with `"passage: "` during indexing; query texts must be prefixed with `"query: "` during retrieval.
   - Token Length & Stride: Text windows targeting 100–300 words; any long passage exceeding 512 tokens must use sliding-window chunking (e.g., 256 tokens with 32-token overlap) to prevent silent truncation.
   - Normalization: All output vectors must be explicitly L2 unit-normalized ($||v||_2 = 1.0$).
2. **Strict Embedding Versioning:** Every record in the `embeddings` table must store:
   - `model_identifier` (e.g., `intfloat/multilingual-e5-base`)
   - `model_revision` (exact pinned Git commit SHA from Hugging Face Hub, e.g. `d13111c57...`, never floating tags)
   - `dimensions` (768)
   All vector similarity SQL queries MUST include `WHERE model_identifier = :current_model AND model_revision = :current_revision`.
3. **Language-Pair Threshold Calibration:** Similarity cutoffs are NOT universal; they must be calibrated independently for monolingual pairs ($\tau_{\text{EN-EN}}, \tau_{\text{HI-HI}}, \tau_{\text{TE-TE}}$) and cross-lingual pairs ($\tau_{\text{cross}}$) using development split ROC curves to keep false positives $\le 5\%$.
4. **Model Upgrades:** If a new model is selected in Phase 5 evaluations (e.g., `BAAI/bge-m3` or `LaBSE`):
   - A new model configuration row is created.
   - The reference corpus must be re-indexed under the new revision before the switch.
   - Cross-version distance queries are strictly prevented by database constraints.
5. **Conditional Cross-Encoder Reranker:** `BAAI/bge-reranker-v2-m3` is reserved as a conditional optimization only if Stage 1 semantic precision on paraphrased benchmarks falls below 70%.

## Alternatives Considered
1. **OpenAI / Proprietary Embeddings:** Rejected due to data privacy violations (sending unpublished student work to third parties), latency fluctuations, and recurring cost.
2. **LaBSE as Baseline:** Considered. Excellent cross-lingual alignment, but higher parameter count and slower CPU inference compared to Multilingual E5. Retained for benchmark comparison in Phase 5.

## Rationale
Multilingual E5 achieves top-tier performance on multilingual retrieval benchmarks, fits within ~1.1 GB memory, supports fast CPU batching, and covers English, Hindi, and Telugu.

## Consequences & Trade-offs
- **Positive:** Air-gapped offline capability, zero third-party API costs, guaranteed vector space consistency.
- **Negative:** Upgrading models requires re-computing embeddings across the entire indexed corpus.

## Validation Requirements
Unit tests asserting strict enforcement of L2 unit norm ($||v|| = 1.0 \pm 10^{-5}$) and failure of queries matching mismatched model revisions.
