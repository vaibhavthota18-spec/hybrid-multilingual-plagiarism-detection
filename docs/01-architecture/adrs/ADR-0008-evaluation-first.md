# ADR-0008: Evaluation-First Methodology & Held-Out Test Protection

- **Status:** Accepted
- **Deciders:** Principal Software Architect, Machine Learning Evaluation Engineer, NLP/AI Engineer
- **Date:** October 2026
- **Technical Story:** Empirical verification methodology, benchmark design, and data leak prevention

---

## Context
Commercial and academic plagiarism detection systems often suffer from inflated accuracy claims due to flawed evaluation practices: tuning detection thresholds directly on the test set, testing on toy synthetic sentences rather than realistic multi-page documents, and evaluating English while making unproven claims about Indic language performance (Hindi and Telugu).

## Decision
1. **Evaluation-First Discipline:** No algorithm (Winnowing, BM25, E5, local alignment) or threshold will be considered "production-ready" without documented benchmark evaluation across standardized datasets in Phase 5.
2. **Three-Way Data Split (60 / 20 / 20):**
   - *Development Set (60%):* Used for algorithm prototyping and parameter exploration.
   - *Validation Set (20%):* Used for threshold calibration (e.g., setting cosine similarity cutoff $\ge 0.82$, k-gram length $k=25$).
   - *Held-Out Test Set (20%):* Strictly locked. Evaluated exactly once for final reported metrics. No model hyperparameter or threshold may be tuned on this set.
3. **Source-Grouped Splitting:** All derivative passages (paraphrases, translations, near-copies) derived from the same root source document must reside in the SAME partition to prevent cross-split data leakage.
4. **Honest Multilingual Reporting:** Language-pair metrics (EN-EN, HI-HI, TE-TE, EN-HI, EN-TE, HI-TE) must be reported separately. No aggregate metric may mask degraded Telugu or Hindi performance.

## Alternatives Considered
1. **Random Token-Level Cross-Validation:** Rejected because sentences from the same source paper leaking across train and test partitions causes severe data leakage and artificially high accuracy scores.
2. **Evaluation Post-Deployment:** Rejected. Verifying accuracy after shipping leads to major architecture rework and user distrust.

## Rationale
Adhering to strict scientific ML evaluation standards ensures that reported accuracy and latency numbers are genuine, reproducible, and robust in academic production environments.

## Consequences & Trade-offs
- **Positive:** Scientifically defensible results; reliable threshold calibrations; zero overfitting to benchmark datasets.
- **Negative:** Requires rigorous curation of ~360 pilot pairs and ~900 full benchmark pairs with professional annotation before Phase 5 sign-off.

## Validation Requirements
Automated verification script asserting zero source document ID overlap between development, validation, and held-out test splits.
