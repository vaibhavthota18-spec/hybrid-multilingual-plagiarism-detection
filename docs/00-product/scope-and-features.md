# Scope Management & Feature Taxonomy

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Version:** 3.0 Master Specification Baseline  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Feature Classification Framework

To ensure disciplined execution, prevent scope creep, and maintain architectural integrity across the eight-phase development roadmap, all proposed product capabilities are classified into three strict categories:

1. **Mandatory Core Product:** Features that must be fully implemented, tested, and verified by Phase 7.
2. **Conditional Optimizations:** Architecturally anticipated enhancements that are implemented only if experimental benchmarks or performance bottlenecks justify their operational complexity.
3. **Deferred Capabilities:** Explicitly excluded from Versions 3.0/4.0. Extension hooks are preserved, but no implementation occurs within the current roadmap.

---

## 2. Mandatory Core Product (Phases 1–7)

The core product comprises 24 mandatory subsystems and capabilities:

1. **Modern Frontend Website:** High-usability React + TypeScript SPA with Tailwind CSS, supporting drag-and-drop document uploads, comparison mode selection, progress indicators, and interactive finding inspection.
2. **Secure Document Upload:** Validated multi-part file ingestion enforcing strict MIME type checking, magic-byte inspection, size limits (up to 30 MB), and path sanitization.
3. **Multi-Format Document Ingestion:** Text extraction pipelines supporting PDF (PyMuPDF), DOCX (python-docx), and UTF-8 plain text (`.txt`).
4. **Direct Comparison Mode (Mode A):** Real-time side-by-side comparison between one submitted document and one reference document without requiring pre-indexed collections.
5. **One-to-Many Comparison Mode (Mode B):** Simultaneous comparison between one submitted document and an ad-hoc batch of user-supplied reference files.
6. **Authorized Corpus Search Mode (Mode C):** Persistent querying of submissions against an access-controlled, pre-indexed institutional document repository.
7. **Winnowing Fingerprinting:** Robust rolling-hash algorithm extracting bounded fingerprint sets for exact verbatim sequence discovery.
8. **Inverted Index & BM25 Retrieval:** Token-based lexical indexing using Okapi BM25 for keyword-dense near-duplicate passage retrieval.
9. **Multilingual Semantic Embeddings:** Dense vector representation using `intfloat/multilingual-e5-base` generating 768-dimensional normalized embeddings for semantic and cross-lingual analysis.
10. **Exact Vector Retrieval:** Deterministic nearest-neighbor cosine distance search powered by PostgreSQL `pgvector` (`<#>` inner product on unit-normalized vectors).
11. **Candidate Fusion & Deduplication:** Multi-stage candidate merging that combines lexical and vector candidates with metadata-driven access filtering.
12. **Token-Level Local Alignment:** Smith-Waterman-inspired local alignment to determine exact matching character boundaries, handling deletions, insertions, and word substitutions.
13. **Tri-Lingual Evaluation Suite:** Ground-truth benchmarking across English, Hindi, and Telugu, evaluating monolingual and cross-lingual language pairs.
14. **Source-Attributed Findings:** Clear provenance tracking linking every detected similarity back to specific source document pages, paragraphs, and metadata.
15. **Explainable Similarity Reporting:** Transparent categorization of findings into Exact Match, Near-Exact Rewrite, Paraphrase, and Potential Translation.
16. **Dual Coverage Metrics:** Mathematically rigorous, non-overlapping Lexical Coverage and Potential Semantic Coverage percentages.
17. **Citation and Quotation Handling:** Automated and toggleable exclusion of properly quoted text (e.g., within quotation marks) and bibliographic reference sections.
18. **Human Review Workflow:** Status tagging (Confirmed Plagiarism, Valid Citation, False Positive, Ignored) with reviewer notes for academic evaluators.
19. **Downloadable PDF Reports:** Comprehensive, publication-grade PDF report generation capturing match statistics, document metadata, and highlighted side-by-side excerpts.
20. **Secure Storage and Hard Deletion:** Tenant-isolated document storage with guaranteed cascading deletion of raw files, extracted text, embeddings, fingerprints, and reports.
21. **Automated Testing & Quality Gates:** Rigorous unit, integration, and contract tests across backend services and frontend components.
22. **Benchmarking & Evaluation Framework:** Reproducible scripts for running recall, precision, IoU, and latency evaluations on standardized test splits.
23. **Container-Based Deployment:** Production-grade Docker Compose architecture encapsulating web, API, background worker, PostgreSQL/pgvector, and Redis.
24. **Complete Technical Documentation:** Exhaustive architecture records, API schemas, user guides, and operational runbooks.

---

## 3. Conditional Optimizations

These enhancements have designated extension points in the architecture. They are prototyped only if specific criteria are met:

| Optimization | Trigger / Justification Metric | Implementation Strategy |
|---|---|---|
| **HNSW Vector Indexing** | Corpus size exceeds 10,000 documents OR exact vector search latency exceeds 500 ms p95. | Enable `pgvector` HNSW index with `m=16, ef_construction=64`. Requires verifying recall remains $\ge 98\%$. |
| **Cross-Encoder Reranking** | Baseline semantic retrieval precision on Paraphrase test split falls below $70\%$. | Integrate `BAAI/bge-reranker-v2-m3` on top-20 merged candidates. Worker must verify GPU availability or strict CPU timeout. |
| **Reciprocal Rank Fusion (RRF)** | BM25 and Dense retrieval candidate score distributions exhibit severe score calibration drift. | Replace linear weighted candidate merging with parameter-free RRF ($k=60$). |
| **MinHash & LSH** | Document-level pre-filtering needed for massive corpora ($>50,000$ documents). | Implement document-level MinHash signatures to bypass passage segmentation for non-matching sources. |
| **OCR Pipeline (Tesseract / EasyOCR)** | User demand indicates $>15\%$ of uploaded PDFs are scanned images with zero extractable text. | Introduce conditional fallback worker step triggering OCR if PyMuPDF extracts $<50$ characters from a page. |
| **ONNX Runtime / TensorRT** | Worker inference bottleneck prevents achieving 180s p95 analysis target on 10-page documents. | Export `multilingual-e5-base` to ONNX format with 8-bit quantization for CPU acceleration. |

---

## 4. Deferred Capabilities (Out-of-Scope)

The following features are formally excluded from Versions 3.0 and 4.0:

1. **Source Code Plagiarism Detection:** Program AST parsing, variable renaming detection, and logic graph comparison for programming languages (e.g., Python, C++, Java).
2. **AI-Generated Text Classification:** Statistical perplexity/burstiness or watermarking detectors claiming to identify ChatGPT/LLM output (empirically brittle and high false-positive rates).
3. **Image & Diagram Plagiarism Detection:** Visual perceptual hashing or computer vision analysis of diagrams, charts, and figures embedded in documents.
4. **Browser Extensions & Desktop Plugins:** Web extensions for real-time browser text checking or Microsoft Word add-ins.
5. **Native Learning Management System (LMS) Plugins:** LTI 1.3 integrations with Canvas, Moodle, or Blackboard.
6. **Live Internet-Wide Web Crawling:** Unrestricted scraping of the public web or unindexed paywalled publisher portals.
7. **Multi-Tenant Enterprise SaaS Administration:** Complex enterprise SSO (SAML/Okta), departmental billing, and multi-tier institutional quotas.
8. **Custom Foundation Model Pre-Training:** Training domain-specific transformer weights from scratch.

---

## 5. Scope-Control & Change Management Process

To protect project velocity and architectural integrity:
1. **No Scope Additions Without ADR:** Any request to move a capability from "Deferred" to "Mandatory" requires a formal Architecture Decision Record (ADR) justifying business need, engineering cost, and test strategy.
2. **Traceability Gate:** Every approved feature must maintain unbroken traceability in `docs/phases/phase-00/requirements-traceability.md`.
3. **Phase Containment:** No conditional optimization may be implemented before Phase 4 (Semantic Detection) or Phase 5 (Evaluation).
