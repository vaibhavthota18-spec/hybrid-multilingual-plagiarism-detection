# Component Architecture & Subsystem Design

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Overview

The backend application is structured as a **Modular Monolith**. Each subsystem possesses well-defined domain boundaries, explicitly typed interfaces, and dedicated data ownership. No subsystem may directly query or mutate internal database tables belonging to another subsystem without traversing published service contracts.

---

## 2. Logical Components Specification

### 2.1 Authentication & Authorization (`auth`)
- **Responsibility:** User identity verification, JWT lifecycle management, Role-Based Access Control (RBAC), and collection permission checks (`CollectionPermission`).
- **Inputs:** User credentials, refresh tokens, session cookies, incoming request headers (`Authorization: Bearer <token>`).
- **Outputs:** Authenticated `UserContext`, signed JWT claims, permission evaluation booleans.
- **Dependencies:** PostgreSQL `users` and `collection_permissions` tables.
- **Data Ownership:** `users`, `memberships`, `collection_permissions`.
- **Error Handling:** Returns HTTP 401 for invalid/expired tokens, HTTP 403 for unauthorized access.
- **Security Boundary:** Validates all request tokens before dispatching to downstream handlers; protects against timing attacks.

### 2.2 File Validation (`ingestion.validation`)
- **Responsibility:** Sanitizing and verifying uploaded files before filesystem storage or parsing.
- **Inputs:** Multipart file byte stream, client filename, declared MIME type.
- **Outputs:** Sanitized file descriptor, verified MIME type, SHA-256 checksum, generated storage UUID.
- **Dependencies:** `python-magic` / file signature table.
- **Data Ownership:** None (stateless pipe).
- **Error Handling:** Rejects corrupted files, mismatched headers, or payloads exceeding 30 MB with HTTP 400/413 (`INVALID_FILE_FORMAT`, `FILE_TOO_LARGE`).
- **Security Boundary:** Prevents polyglot file execution, directory traversal filenames (`../`), and denial-of-service via decompression bombs.

### 2.3 Text Extraction (`extraction`)
- **Responsibility:** Extracting textual content, paragraph boundaries, and page coordinate metadata from PDF, DOCX, and TXT files.
- **Inputs:** Validated file path on disk, document metadata.
- **Outputs:** `ExtractedDocument` containing full text, page index, and structural blocks.
- **Dependencies:** PyMuPDF (`fitz`), `python-docx`.
- **Data Ownership:** `documents.raw_text`, page mapping tables.
- **Error Handling:** Catches corrupted PDF objects, encrypted files, or empty text streams (`EXTRACTION_FAILED`, `EXTRACTION_EMPTY_TEXT`).
- **Security Boundary:** Runs inside sandboxed worker process with memory limits to prevent memory exhaustion from complex PDF trees.

### 2.4 Text Normalization & Offsets (`preprocessing.normalization`)
- **Responsibility:** Standardizing character representations (Unicode NFC), handling Indic script ligatures, stripping zero-width spaces, and maintaining a strict mapping to original code-point offsets.
- **Inputs:** Raw extracted text string.
- **Outputs:** `NormalizedDocument` containing normalized string and a bidirectional offset projection map (`orig_to_norm`, `norm_to_orig`).
- **Dependencies:** Python `unicodedata`, Indic NLP library helpers.
- **Data Ownership:** Ephemeral worker memory / stored offset projection.
- **Error Handling:** Gracefully handles malformed surrogate pairs; logs unmapped characters.
- **Security Boundary:** Prevents Unicode homoglyph spoofing and invisible character injection.

### 2.5 Language Identification (`preprocessing.language`)
- **Responsibility:** Detecting primary language and mixed-language passages (English, Hindi, Telugu, or Other).
- **Inputs:** Normalized text passages.
- **Outputs:** ISO 639-1/3 language code, confidence score ($0.0 \dots 1.0$), script classification.
- **Dependencies:** Language classification models (e.g., fasttext/pycld3/langdetect).
- **Data Ownership:** `documents.detected_language`, `passages.language`.
- **Error Handling:** Defaults to `und` (undetermined) if confidence $<0.60$; logs warning.
- **Security Boundary:** Stateless.

### 2.6 Passage Segmentation (`preprocessing.segmentation`)
- **Responsibility:** Splitting normalized document text into overlapping or paragraph-bounded passages optimized for indexing and embedding (target size: 100–300 words).
- **Inputs:** `NormalizedDocument`.
- **Outputs:** Ordered list of `Passage` records with start/end Unicode code-point offsets.
- **Dependencies:** Sentence tokenizers with Indic script boundary rules.
- **Data Ownership:** `passages` table in PostgreSQL.
- **Error Handling:** 
  - *Tier 1 Short-Passage Rule:* Standalone short fragments ($<30$ words or $<150$ characters, such as section sub-headings or single-sentence paragraphs) MUST NOT be discarded; they are merged with the subsequent adjacent passage, guaranteeing zero unindexed text gaps.
  - Standalone short documents ($<100$ words) are indexed as a single self-contained passage rather than dropped.
- **Security Boundary:** Restricts maximum passage count per document to prevent memory exhaustion.

### 2.7 Fingerprinting (`fingerprinting.winnowing`)
- **Responsibility:** Generating rolling hashes and extracting minimum window fingerprints via the Winnowing algorithm for exact verbatim matching.
- **Inputs:** Normalized character sequence with provisional parameters: character $k$-gram $k_{\text{char}}=25$ characters, window size $w_{\text{hashes}}=16$ consecutive $k$-gram hashes (window text span $k+w-1=40$ characters; match guarantee $t \ge 40$ characters; rightmost minimum tie-break; provisional baselines evaluated across $k \in [15, 35]$ characters and $w \in [8, 32]$ hashes on development splits).
- **Outputs:** List of `Fingerprint` records `(hash_value, passage_id, start_offset, end_offset)`.
- **Dependencies:** Polynomial rolling-hash implementation.
- **Data Ownership:** `fingerprints` table and inverted index structures.
- **Error Handling:** Bounded hash space; potential 64-bit rolling hash collisions are verified and filtered in Stage 2 against exact token offsets.
- **Security Boundary:** Deterministic calculation; no external data dependencies.

### 2.8 BM25 Retrieval (`retrieval.bm25`)
- **Responsibility:** Lexical keyword candidate retrieval across indexed passage collections.
- **Inputs:** Query passage tokens, target collection ID.
- **Outputs:** Ranked candidate passage IDs with BM25 relevance scores.
- **Dependencies:** Inverted index or PostgreSQL full-text search backend.
- **Data Ownership:** Inverted index metadata.
- **Error Handling:** Returns empty candidate set if no matching terms exist.
- **Security Boundary:** Filters candidates strictly by user's authorized collection permissions.

### 2.9 Semantic Embedding (`ml.embeddings`)
- **Responsibility:** Generating 768-dimensional L2-normalized dense vector representations for passages using `intfloat/multilingual-e5-base`.
- **Inputs:** Passage text with prefix (`"passage: "` or `"query: "`), model revision identifier (pinned Git commit SHA).
- **Outputs:** 768-dimensional float32 vector array ($||v||_2 = 1.0$).
- **Dependencies:** PyTorch, Hugging Face `transformers`, local model cache.
- **Data Ownership:** `embeddings` table (`vector(768)` column in PostgreSQL).
- **Error Handling:** Batches inputs to prevent OOM; falls back to CPU if GPU memory is saturated. Passages $>512$ tokens are split with stride overlap.
- **Security Boundary:** Model weights loaded exclusively from verified local checksums; no remote code execution (`trust_remote_code=False`).

### 2.10 Vector Retrieval (`retrieval.vector`)
- **Responsibility:** Exact nearest-neighbor search using PostgreSQL `pgvector` negative inner product operator (`<#>`).
- **Inputs:** Query embedding vector, target collection IDs, language-pair calibrated similarity threshold $\tau$ (e.g. $\tau_{\text{EN-EN}}, \tau_{\text{HI-HI}}, \tau_{\text{TE-TE}}, \tau_{\text{cross}}$), top-$k$ limit.
- **Outputs:** Ranked semantic candidate passage IDs with cosine similarity scores.
- **Dependencies:** PostgreSQL 16 + `pgvector`.
- **Data Ownership:** Queries `embeddings` joined with `collection_documents`.
- **Error Handling:** Raises timeout if query execution exceeds threshold; verifies collection access.
- **Security Boundary:** Hard SQL filter on `collection_id IN (:authorized_collections)` preventing multi-tenant data leakage.

### 2.11 Candidate Fusion & Deduplication (`retrieval.fusion`)
- **Responsibility:** Merging lexical (Winnowing/BM25) and semantic (vector) candidates into a single deduplicated evaluation list for Stage 2.
- **Inputs:** Lexical candidate set, Semantic candidate set.
- **Outputs:** Deduplicated `List[RetrievalCandidate]`.
- **Dependencies:** Candidate ranking algorithms (linear weighted fusion or Reciprocal Rank Fusion).
- **Data Ownership:** Ephemeral job state.
- **Error Handling:** Safely handles empty lexical or empty semantic sets.
- **Security Boundary:** Pure internal processing.

### 2.12 Local Sequence Alignment (`alignment.local`)
- **Responsibility:** Executing token-level local alignment (modified Smith-Waterman) between submission passages and candidate source passages to delineate exact matching character boundaries.
- **Inputs:** Submission passage string, Reference passage string, match/mismatch/gap scoring parameters.
- **Outputs:** `AlignmentResult` containing exact character spans `[sub_start, sub_end)`, `[src_start, src_end)`, edit distance, and matched token count.
- **Behavior & Span Rule:** *Tier 2 Alignment Rule:* Aligns matching token spans down to a minimum span of $\ge 6$ tokens, capturing short definitions, sentences, and regional idioms.
- **Dependencies:** Cython / optimized C-extension or vectorized Python alignment routines.
- **Data Ownership:** Ephemeral; passed to scoring.
- **Error Handling:** Caps maximum sequence length to prevent quadratic time explosions ($O(N \cdot M)$ bounded by passage window).
- **Security Boundary:** Safe bounded memory allocations.

### 2.13 Evidence Aggregation & Uncertainty (`scoring.evidence`)
- **Responsibility:** Categorizing findings into match types (Exact Copy, Near-Exact Rewrite, Paraphrase, Potential Translation) and calculating confidence / evidence strength metrics.
- **Inputs:** `AlignmentResult`, lexical hash overlap ratio, vector cosine similarity.
- **Outputs:** `MatchEvidence` with categorical classification and uncertainty notes.
- **Classification & Confidence Rules:** *Tier 3 Reporting Rule:*
  - Spans $\ge 10$ tokens with $\ge 90\%$ token overlap $\rightarrow$ `EXACT_COPY` (`HIGH` confidence).
  - Spans 6–9 tokens with $\ge 90\%$ token overlap $\rightarrow$ `EXACT_COPY` (`LOW_CONFIDENCE`, tagged "Short or Common-Text Overlap" unless clustered).
  - Spans $\ge 10$ tokens with $70\% \le \text{overlap} < 90\%$ and $\ge \tau_{\text{lang}}+0.03$ $\rightarrow$ `NEAR_EXACT_REWRITE` (`HIGH`/`MODERATE` confidence).
  - Spans $\ge 12$ tokens with $\ge \tau_{\text{lang}}$ $\rightarrow$ `PARAPHRASE` (`MODERATE` confidence).
  - Spans $\ge 12$ tokens with $\ge \tau_{\text{cross}}$ $\rightarrow$ `POTENTIAL_TRANSLATION` (`MODERATE` confidence).
- **Dependencies:** Calibration threshold configurations.
- **Data Ownership:** Ephemeral; saved in `findings`.
- **Error Handling:** Marks ambiguous findings as `LOW_CONFIDENCE` rather than discarding evidence.
- **Security Boundary:** Pure business logic.

### 2.14 Similarity Scoring Engine (`scoring.engine`)
- **Responsibility:** Calculating aggregate Lexical Coverage and Potential Semantic Coverage percentages across the submission document, executing geometric interval union deduplication.
- **Inputs:** Set of all verified `SimilarityFinding` records, eligible document code-point length, active exclusion rules.
- **Outputs:** `AnalysisResult` with overall and per-source coverage statistics.
- **Dependencies:** Interval union algorithm.
- **Data Ownership:** `analyses` and `findings` tables.
- **Error Handling:** Handles zero-length documents and 100% overlap edge cases without division-by-zero.
- **Security Boundary:** Pure business logic.

### 2.15 Reporting Engine (`reporting`)
- **Responsibility:** Generating publication-grade PDF reports and formatting JSON payloads for frontend display.
- **Inputs:** `AnalysisResult`, document metadata, human review annotations, exclusion state.
- **Outputs:** Standalone PDF file path, structured summary JSON.
- **Dependencies:** ReportLab / WeasyPrint, Jinja2 templating, DejaVu / Noto Sans Indic fonts.
- **Data Ownership:** `storage/reports/*.pdf`.
- **Error Handling:** Handles missing fonts with verified fallbacks; validates PDF integrity before completing job.
- **Security Boundary:** Restricts PDF rendering from executing external scripts or embedding unsanitized user HTML.

### 2.16 Review Management (`reviews`)
- **Responsibility:** Recording human-in-the-loop annotations (`VALID_CITATION`, `SUSPECTED_PLAGIARISM`, `FALSE_POSITIVE`, `IGNORED`), updating adjusted net scores.
- **Inputs:** Reviewer user ID, finding ID, label, reviewer notes.
- **Outputs:** Updated `Review` record, recomputed adjusted analysis scores.
- **Dependencies:** `reviews` table, `scoring.engine`.
- **Data Ownership:** `reviews`.
- **Error Handling:** Validates reviewer permissions on the target analysis.
- **Security Boundary:** Immutable audit history of who applied each review decision.

### 2.17 Background Job Queue (`jobs`)
- **Responsibility:** Asynchronous dispatch and lifecycle tracking of document extraction, embedding generation, comparison jobs, and PDF rendering.
- **Inputs:** Job name, execution payload, user context, timeout limits.
- **Outputs:** `JobStatus` updates (`queued`, `processing`, `completed`, `failed`, `cancelled`).
- **Dependencies:** Redis 7, Python RQ.
- **Data Ownership:** `analysis_jobs` table and Redis queue keys.
- **Error Handling:** Automatic retry for transient database disconnections; catches unhandled exceptions and transitions job to `failed` with sanitized error message.
- **Security Boundary:** Worker processes run as non-privileged daemon users; payload parameters strictly validated.
