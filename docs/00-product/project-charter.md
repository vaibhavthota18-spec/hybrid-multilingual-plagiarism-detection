# Project Charter

> **Project Title:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Version:** 3.0 Master Specification Baseline  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Problem Statement

Academic dishonesty, unauthorized text reuse, and uncredited intellectual copying undermine research integrity and education globally. While commercial plagiarism detection systems exist for English, institutions and researchers in linguistically diverse environments—particularly in India and multilingual educational bodies—face three critical deficiencies:

1. **Failure on Non-English Languages:** Mainstream tools perform poorly on Indic languages such as Hindi and Telugu due to complex scripts (Devanagari, Telugu aksharas), agglutinative morphology, and lack of specialized tokenizers.
2. **Blindness to Cross-Language Copying:** Students and authors frequently translate passages from English sources into regional languages (or vice-versa), evading standard keyword or n-gram matching tools entirely.
3. **Black-Box Disciplinary Accusations:** Traditional tools generate a single opaque "similarity percentage" without distinguishing between legitimate scholarly citations, common technical definitions, and uncredited paraphrasing. This leads to unfair disciplinary accusations and high reviewer burden.

---

## 2. Project Vision & Objectives

The platform provides a modern, transparent, and approachable AI-powered document similarity analysis web application. Designed with the intuitive usability of tools like iLovePDF, users can upload documents and receive rich, evidence-grounded similarity reports with source attribution and human-review workflows.

### Core Objectives
1. **Hybrid Retrieval Architecture:** Combine high-throughput lexical fingerprinting (Winnowing rolling hashes and BM25) with multilingual dense vector semantic search (`multilingual-e5-base` via `pgvector`).
2. **Multilingual & Cross-Lingual Detection:** Accurately evaluate exact matches, paraphrases, and cross-lingual translation similarities across **English, Hindi, and Telugu**.
3. **Evidentiary Attribution & Explainability:** Isolate lexical coverage from potential semantic coverage, visualize side-by-side aligned spans, and provide quotation and citation filtering.
4. **Ethical Academic Guardrails:** Emphasize that text similarity is not an automatic declaration of plagiarism, providing academic reviewers with tools to verify intent and context.

---

## 3. Social Usefulness & Impact

- **Democratizing Academic Integrity:** Providing regional language universities, schools, and independent researchers with accessible, high-performance similarity tools.
- **Fairness for Scholars:** Preventing wrongful allegations through granular citation exclusions, hard-negative filtering, and uncertainty scoring.
- **Multilingual Research Advancement:** Establishing rigorous evaluation benchmarks and open methodologies for Indic language text reuse detection.

---

## 4. Target Users & Stakeholders

| User Role | Description & Primary Use Case |
|---|---|
| **Students** | Pre-submission originality checks for term papers, theses, and essays; self-correction of missing citations. |
| **Researchers & Authors** | Verifying proper attribution and literature review boundaries prior to journal submission. |
| **Educators & Evaluators** | Assessing student assignments with granular evidence, side-by-side span comparisons, and citation filtering. |
| **Institutional Administrators** | Maintaining private departmental reference collections and enforcing academic honesty policies. |
| **Academic Reviewers** | Peer reviewers evaluating manuscripts against conference archives and reference corpora. |

---

## 5. Expected Outcomes & Deliverables

1. **Production-Ready Web Application:** Modern, responsive React + TypeScript interface with drag-and-drop document upload, real-time job tracking, and interactive side-by-side passage viewers.
2. **Robust Backend API:** Modular FastAPI backend running asynchronous processing workers backed by Redis and PostgreSQL/pgvector.
3. **Multi-Format Ingestion Engine:** Extraction pipelines for PDF, DOCX, and TXT with resilient Unicode normalization and code-point offset preservation.
4. **Downloadable PDF Reports:** Institutional-quality exportable PDF reports showing coverage metrics, matched sources, side-by-side comparisons, and review status.
5. **Empirical Evaluation Benchmark:** Annotated benchmark suite covering ~360 pilot pairs and ~900 expanded pairs across English, Hindi, and Telugu.

---

## 6. Scope Boundaries

### In-Scope (Phase 0–7)
- Text document formats: PDF, DOCX, TXT (up to 30 MB / 100 pages per document).
- Three operational comparison modes: Mode A (Direct), Mode B (One-to-Many), Mode C (Corpus).
- Language support: English, Hindi, Telugu.
- Verbatim, near-verbatim, paraphrased, and translated text similarity.
- Quotation and bibliographic citation exclusion engine.
- Human review markup and downloadable PDF reporting.
- Complete containerized deployment architecture (Docker Compose).

### Out-of-Scope (Deferred to Future Versions)
- Optical Character Recognition (OCR) for scanned image-only PDFs.
- Source-code plagiarism detection (e.g., Python, Java, C++ syntax trees).
- AI-generated text detection (watermarking / synthetic style detection).
- Live web crawling or internet-scale scraping.
- Native LMS integrations (Canvas, Moodle, Blackboard LTI plugins).
- Pre-trained model fine-tuning from scratch (the platform uses pre-trained open models with frozen embeddings and evaluation tuning).

---

## 7. Research Objectives

- Evaluate cross-lingual sentence embedding retrieval quality between English, Hindi, and Telugu using zero-shot multilingual encoders (`intfloat/multilingual-e5-base` vs. `LaBSE` vs. `BAAI/bge-m3`).
- Quantify the trade-off between Winnowing fingerprint granularity (window size $w$, k-gram size $k$) and false-discovery rate in morphologically rich Indic languages.
- Measure passage alignment accuracy using token-level Smith-Waterman local alignment versus sentence-level bounding.

---

## 8. Engineering Success Criteria

1. **Correctness & Precision:** High-confidence exact-copy precision $\ge 95\%$; exact/near-exact recall $\ge 85\%$.
2. **Alignment Quality:** Mean Intersection-over-Union (IoU) of matched character spans $\ge 0.80$.
3. **Retrieval Recall:** Source Recall@20 $\ge 90\%$ for monolingual collections; Cross-language Recall@20 $\ge 80\%$.
4. **Performance & Latency:** For a warmed 10-page document evaluated against 1,000 indexed reference documents, p95 analysis latency $\le 180$ seconds on 8 CPU cores / 16 GB RAM.
5. **Reliability & Portability:** 100% automated test coverage on core offset, scoring, and alignment algorithms; zero cross-tenant data leakage; clean containerized deployment via Docker Compose.
