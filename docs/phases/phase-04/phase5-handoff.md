# Phase 5 Handoff: Citation Attribution, Quoted Span Exclusion & Authorship Verification

## 1. Context & Starting Baseline for Phase 5

With Phase 4 complete, the system boasts a robust hybrid plagiarism detection pipeline:
- Lexical exact/near-exact matching (Winnowing $k=25, w=16$, BM25Okapi).
- Semantic paraphrase and cross-language detection (`multilingual-e5-small`, 384-dim).
- Local SQLite vector repository with float32 binary BLOBs.
- Non-overlapping union coverage and composite scoring.
- Comprehensive React dashboard with category-based highlights and evidence inspection.

---

## 2. Phase 5 Objectives & Scope

Phase 5 introduces academic attribution intelligence to distinguish legitimate scholarly citation from unauthorized plagiarism:

1. **Citation & Reference List Parsing**:
   - Extraction and parsing of inline academic citations (e.g. `(Smith et al., 2023)`, `[12]`, superscript numbers).
   - Extraction of terminal reference sections / bibliographies (APA, IEEE, Chicago, Harvard, MLA formats).
2. **Quoted Passage Detection & False Positive Exclusion**:
   - Detection of quotation marks (`"..."`, `“...”`, `‘...’`, block quotes).
   - Linking quoted passages to proximate citation markers.
   - Enabling institutional policy toggle to exclude properly attributed quotations from the net plagiarism score (`is_quoted`, `is_excluded`).
3. **Authorship & Stylometric Feature Extraction**:
   - Extraction of stylometric signals (sentence length distributions, type-token ratios, punctuation density, stopword profiles).
   - Detection of sudden stylistic anomalies within a single document suggesting multi-author copy-pasting.

---

## 3. Interfaces & Extension Points Prepared in Phase 4

- `SimilarityFinding` model includes `is_quoted: bool` and `is_excluded: bool` flags ready for citation logic.
- `AnalysisResult` includes placeholder structures for `citation_coverage_percent` and `stylometric_metadata`.
- Frontend finding inspector already includes `is_quoted` badge placeholders.
- OpenAPI contract (`contracts/openapi.yaml`) defines `/analyses/{analysis_id}/findings/{finding_id}/reviews` for manual attribution auditing.

---

## 4. Invariant Rules for Phase 5 Implementation

1. Continue native Windows 11 localhost execution (no Docker/WSL2 until explicit user directive).
2. Maintain zero-cloud privacy: citation parsing must run locally using regex/NER, without sending documents to third-party APIs.
3. Preserve existing Phase 1–4 tests and functionality without regressions.
