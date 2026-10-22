# Software Requirements Specification (SRS)

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Version:** 3.0 Master Specification Baseline  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Introduction & Structure

This document establishes the canonical Software Requirements Specification (SRS) for the system. Every functional requirement (FR) and non-functional requirement (NFR) is assigned a stable identifier, prioritization, owning architectural subsystem, implementation phase, dependencies, precise acceptance criteria, and verification methodology.

### Priority Scheme (MoSCoW)
- **P0 (Must Have):** Core foundational requirement indispensable for the MVP and core functionality.
- **P1 (Should Have):** Important requirement expected in standard production releases.
- **P2 (Could Have):** Desirable optimization or secondary feature implemented conditionally.
- **P3 (Won't Have / Out of Scope):** Deferred feature explicitly scheduled for future versions.

---

## 2. Functional Requirements (FR)

### 2.1 Document Ingestion & Management

#### `FR-DOC-001`: Multi-Format Document Upload
- **Description:** The system must accept user file uploads in PDF (`.pdf`), Microsoft Word (`.docx`), and Plain Text (`.txt`) formats up to 30 MB per file.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/ingestion/`
- **Implementation Phase:** Phase 2
- **Dependencies:** None
- **Acceptance Criteria:** Successfully uploads valid PDF, DOCX, and TXT files. Rejects files $>30$ MB or with mismatched magic-byte headers with HTTP 400/413.
- **Verification Method:** Automated API multipart upload test suite with valid and invalid sample payloads.

#### `FR-DOC-002`: Document Text Extraction & Unicode Normalization
- **Description:** The system must extract clean text from uploaded files using PyMuPDF (PDF), python-docx (DOCX), and native UTF-8 decoding (TXT), applying Unicode NFC normalization while preserving page and paragraph provenance.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/extraction/`
- **Implementation Phase:** Phase 2
- **Dependencies:** `FR-DOC-001`
- **Acceptance Criteria:** Extracted text accurately represents document content. Retains page number mappings for PDF. Gracefully handles Indic script ligatures (Devanagari, Telugu).
- **Verification Method:** Unit tests comparing extracted string output against pre-annotated plain text gold standards.

#### `FR-DOC-003`: Canonical Zero-Based Unicode Code-Point Offsets
- **Description:** The extraction service must establish and maintain canonical zero-based, half-open Unicode code-point offsets (`[start, end)`) referencing the raw extracted string.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/preprocessing/`
- **Implementation Phase:** Phase 2
- **Dependencies:** `FR-DOC-002`
- **Acceptance Criteria:** Every passage, sentence, and detected match contains exact code-point offsets such that `text[start:end]` reproduces the highlighted substring exactly without character drift.
- **Verification Method:** Deterministic property-based test checking 1,000 multi-script substring slices.

#### `FR-DOC-004`: Language Identification & Verification
- **Description:** The system must detect the primary document language and passage-level languages, classifying into English, Hindi, Telugu, or Other.
- **Priority:** P1 (Should Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/preprocessing/`
- **Implementation Phase:** Phase 2
- **Dependencies:** `FR-DOC-002`
- **Acceptance Criteria:** Accurately classifies monolingual English, Hindi, and Telugu documents with $\ge 98\%$ accuracy. Tags unsupported languages to trigger UI advisories.
- **Verification Method:** Benchmark test on multilingual text fixtures using fasttext/pycld3/langdetect.

#### `FR-DOC-005`: Multi-Tier Document Storage & Hard Deletion
- **Description:** Submitted files and derived artifacts (extracted text, fingerprints, vectors, cached reports) must be stored in tenant-isolated directories and expunged across operational, cache, and backup tiers upon user request.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/storage/`
- **Implementation Phase:** Phase 2
- **Dependencies:** `FR-DOC-001`
- **Acceptance Criteria:** `DELETE /api/v1/documents/{id}` executes a reliable multi-tier deletion workflow: immediate access restriction (`status = 'DELETING'`), append-only tombstone in independent Durable Deletion Ledger, worker fencing token (`fence:doc:{id}`), ACID database cascade, idempotent filesystem unlinking, and Redis cache eviction. Replays Durable Deletion Ledger to purge restored records if a backup snapshot is restored.
- **Verification Method:** Integration test verifying immediate access restriction, database cascading delete, filesystem unlink checks, worker fencing, and post-restore reconciliation hooks.

---

### 2.2 Comparison Modes

#### `FR-MODE-001`: Direct Comparison Mode (Mode A)
- **Description:** The system must allow users to upload one submission document and one reference document, performing pairwise comparison without requiring pre-indexed persistent collections.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/scoring/`
- **Implementation Phase:** Phase 3 & Phase 4
- **Dependencies:** `FR-DOC-001`, `FR-DET-001`, `FR-DET-003`
- **Acceptance Criteria:** Pairwise analysis completes within 10 seconds for 5-page documents. Surfaces exact, near-exact, and semantic similarities between the two files.
- **Verification Method:** End-to-end integration test comparing two known test documents.

#### `FR-MODE-002`: One-to-Many Comparison Mode (Mode B)
- **Description:** The system must support comparing one submission against a batch of up to 10 user-provided reference documents in a single job.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/scoring/`
- **Implementation Phase:** Phase 3 & Phase 4
- **Dependencies:** `FR-MODE-001`
- **Acceptance Criteria:** Ingests the batch, builds an ephemeral index, queries submission passages, attributes matches to specific references, and deduplicates multi-source overlaps.
- **Verification Method:** Batch upload test verifying multi-source attribution and aggregate score unification.

#### `FR-MODE-003`: Indexed Corpus Search Mode (Mode C)
- **Description:** The system must allow users to query a submission document against an authorized, pre-indexed persistent reference collection stored in PostgreSQL and `pgvector`.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/corpora/`
- **Implementation Phase:** Phase 2 & Phase 4
- **Dependencies:** `FR-COL-001`, `FR-DET-002`, `FR-DET-004`
- **Acceptance Criteria:** Queries pre-computed fingerprints and dense vectors across authorized collections only, returning source document attribution and metadata.
- **Verification Method:** Query execution test against a pre-indexed 500-document reference corpus.

---

### 2.3 Detection Pipeline

#### `FR-DET-001`: Winnowing Rolling-Hash Fingerprinting
- **Description:** The system must compute bounded rolling-hash fingerprints using the Winnowing algorithm with provisional character $k$-gram size $k_{\text{char}}=25$ characters and window size $w_{\text{hashes}}=16$ consecutive $k$-gram hashes (covering $k+w-1=40$ characters, rightmost minimum tie-break, tuned across $k \in [15, 35]$ and $w \in [8, 32]$ on development data) over normalized character sequences for exact verbatim match detection.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/fingerprinting/`
- **Implementation Phase:** Phase 3
- **Dependencies:** `FR-DOC-003`
- **Acceptance Criteria:** Mathematically guarantees detection of verbatim substrings of length $\ge (k + w - 1) = 40$ characters. Resolves ties using rightmost minimum hash. Verifies hash matches in Stage 2 against exact text offsets to eliminate false collisions. Produces identical hashes regardless of irrelevant whitespace variations.
- **Verification Method:** Unit tests against synthetic verbatim copy-paste pairs with variable spacing and boundary lengths.

#### `FR-DET-002`: Inverted Index & BM25 Lexical Retrieval
- **Description:** The system must maintain an inverted index and utilize Okapi BM25 scoring to retrieve top-$k$ candidate passages for submission queries during Mode C corpus searches.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/retrieval/`
- **Implementation Phase:** Phase 3
- **Dependencies:** `FR-DOC-002`
- **Acceptance Criteria:** Retrieves relevant candidate passages within 50 ms per query. Ranks lexical keyword overlaps ahead of unrelated passages.
- **Verification Method:** Benchmark test measuring Recall@20 on lexical keyword test queries.

#### `FR-DET-003`: Multilingual Semantic Embedding Generation
- **Description:** The system must generate 768-dimensional normalized dense embeddings for document passages using `intfloat/multilingual-e5-base` pinned to a specific Git commit SHA, applying appropriate "passage: " and "query: " prefixes and handling passages $>512$ tokens via sliding-window stride chunking.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/ml/`
- **Implementation Phase:** Phase 4
- **Dependencies:** `FR-DOC-003`
- **Acceptance Criteria:** Generates L2-normalized embeddings ($||v||_2 = 1.0 \pm 10^{-5}$) for English, Hindi, and Telugu passages up to 512 tokens. Rejects empty passages. Handles sliding-window chunking without truncation or memory leaks.
- **Verification Method:** Model inference unit tests checking embedding dimensionality, unit norm, and cross-lingual cosine similarity consistency.

#### `FR-DET-004`: Vector Retrieval via pgvector
- **Description:** The system must execute exact nearest-neighbor vector search in PostgreSQL using the `pgvector` negative inner-product operator (`<#>`) on unit-normalized embeddings to retrieve semantic candidates.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/retrieval/`
- **Implementation Phase:** Phase 4
- **Dependencies:** `FR-DET-003`
- **Acceptance Criteria:** Retrieves top-$k$ passages exceeding language-pair calibrated similarity thresholds $\tau$ scoped strictly by authorized collection IDs using `(embedding <#> query) <= -threshold`.
- **Verification Method:** Database integration query tests verifying precision, negative inner product sort order, and collection tenant filtering.

#### `FR-DET-005`: Candidate Fusion & Reciprocal Rank Merging
- **Description:** The system must merge candidate passages retrieved from lexical (Winnowing/BM25) and semantic (`pgvector`) retrieval pipelines into a unified, deduplicated candidate set for detailed verification.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/retrieval/`
- **Implementation Phase:** Phase 4
- **Dependencies:** `FR-DET-001`, `FR-DET-002`, `FR-DET-004`
- **Acceptance Criteria:** Merges candidates using weighted linear combination or reciprocal rank fusion, ensuring no candidate passage is evaluated twice during alignment.
- **Verification Method:** Test pipeline ensuring union of top candidates contains both exact keyword and paraphrased candidates.

#### `FR-DET-006`: Token-Level Local Alignment & Span Reporting
- **Description:** The system must perform token-level local sequence alignment (Smith-Waterman algorithm adapted for word/subword tokens) on candidate passage pairs down to $\ge 6$ tokens to pinpoint exact and near-exact matching character spans.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/alignment/`
- **Implementation Phase:** Phase 3
- **Dependencies:** `FR-DOC-003`
- **Acceptance Criteria:** Detects start and end character offsets of matching spans with $\ge 99\%$ accuracy on synthetic fixtures. Aligns spans down to $\ge 6$ tokens. Classifies spans $\ge 10$ tokens as high-confidence verbatim/rewrites, and spans 6–9 tokens as low-confidence common-text overlaps.
- **Verification Method:** Alignment benchmark measuring Intersection-over-Union (IoU) of predicted spans against gold spans.

#### `FR-DET-007`: Overlap Deduplication & Coverage Computation
- **Description:** The system must calculate Lexical Coverage and Potential Semantic Coverage percentages by geometrically merging overlapping matched intervals, ensuring no submission character is counted multiple times.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/scoring/`
- **Implementation Phase:** Phase 3 & Phase 4
- **Dependencies:** `FR-DET-006`
- **Acceptance Criteria:** Aggregate coverage matches the exact formula: $\text{Coverage} = 100 \times \frac{|\bigcup_i [s_i, e_i)|}{L_{\text{eligible}}}$. Returns $0.0\%$ for empty documents.
- **Verification Method:** Mathematical property tests with overlapping, nested, and disjoint interval sets.

---

### 2.4 Reporting, Review & UX

#### `FR-REP-001`: Interactive Side-by-Side Finding Viewer
- **Description:** The web frontend must display an interactive side-by-side view showing the submitted document alongside matched source passages with synchronized highlighting and source attribution metadata.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/web/src/features/analyses/`
- **Implementation Phase:** Phase 6
- **Dependencies:** `FR-DET-006`, `FR-DOC-003`
- **Acceptance Criteria:** Clicking a highlighted passage in the submission pane smoothly scrolls and centers the corresponding source passage in the reference pane. Highlights match exact backend code points.
- **Verification Method:** End-to-end browser automation test (Playwright) verifying DOM highlight offsets and click-scroll synchronization.

#### `FR-REP-002`: Citation & Quotation Filtering
- **Description:** The system must identify text enclosed in quotation marks (", '', «», “”) and standard bibliographic reference sections, allowing users to toggle their exclusion from the similarity score.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/scoring/`
- **Implementation Phase:** Phase 6
- **Dependencies:** `FR-DET-007`
- **Acceptance Criteria:** When toggled ON, eligible quoted spans are subtracted from both lexical and semantic coverage calculations, recalculating the net score in real time.
- **Verification Method:** Test fixture evaluation comparing scores with exclusions enabled vs. disabled.

#### `FR-REP-003`: Human-in-the-Loop Review & Annotation
- **Description:** Authorized reviewers must be able to mark individual findings with status labels (`VALID_CITATION`, `SUSPECTED_PLAGIARISM`, `FALSE_POSITIVE`, `IGNORED`) and attach explanatory commentary.
- **Priority:** P1 (Should Have)
- **Owning Module:** `apps/backend/src/plagiarism/api/v1/`
- **Implementation Phase:** Phase 6
- **Dependencies:** `FR-REP-001`
- **Acceptance Criteria:** Review decisions persist in the database, update the report summary, and appear in subsequent exported reports.
- **Verification Method:** API and UI test verifying review submission, persistence, and net score recalculation.

#### `FR-REP-004`: Downloadable PDF Audit Report
- **Description:** The platform must generate an official, publication-ready PDF report summarizing submission metadata, SHA-256 hash, dual coverage metrics, source breakdown, and highlighted excerpts.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/reporting/`
- **Implementation Phase:** Phase 6
- **Dependencies:** `FR-REP-001`, `FR-REP-002`, `FR-REP-003`
- **Acceptance Criteria:** Generated PDF renders properly formatted multilingual text (English, Hindi, Telugu) without font corruption or broken glyphs. Contains unalterable metadata and timestamp.
- **Verification Method:** Automated test verifying PDF generation, header validation, and Indic font rendering checks.

---

### 2.5 Reference Collection Management

#### `FR-COL-001`: Collection Creation & Access Control
- **Description:** Users must be able to create named document collections, define read/write permissions for specific users or institutional domains, and maintain strict multi-tenant isolation.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/corpora/`
- **Implementation Phase:** Phase 2
- **Dependencies:** None
- **Acceptance Criteria:** Users can only query or ingest into collections where they possess explicit `READ` or `WRITE` permissions. Rejects unauthorized requests with HTTP 403.
- **Verification Method:** RBAC matrix integration tests asserting allowed and forbidden access scenarios.

#### `FR-COL-002`: Document Ingestion into Corpus
- **Description:** Authorized users can add permitted reference documents to a collection, automatically triggering passage segmentation, Winnowing fingerprint indexing, and embedding storage in `pgvector`.
- **Priority:** P0 (Must Have)
- **Owning Module:** `apps/backend/src/plagiarism/services/corpora/`
- **Implementation Phase:** Phase 2 & Phase 4
- **Dependencies:** `FR-COL-001`, `FR-DET-001`, `FR-DET-003`
- **Acceptance Criteria:** Indexes documents in background queue. Tracks document metadata (title, author, license, provenance) and index status (`INDEXED`, `FAILED`).
- **Verification Method:** Corpus ingestion integration test verifying relational rows, fingerprint hashes, and vector embeddings.

---

## 3. Non-Functional Requirements (NFR)

### 3.1 Security & Privacy

#### `NFR-SEC-001`: Secure Upload Validation & File Isolation
- **Description:** File uploads must undergo magic-byte signature validation, strict file size enforcement (max 30 MB), filename sanitization (UUID generation), and storage outside public web roots.
- **Priority:** P0 (Must Have)
- **Implementation Phase:** Phase 2 & Phase 7
- **Verification Method:** Penetration test suite injecting polyglot files, path traversal payloads (`../../etc/passwd`), and oversized streams.

#### `NFR-SEC-002`: Multi-Tenant Isolation & Least Privilege
- **Description:** All database queries must enforce tenant and collection permission predicates. Raw text, embeddings, and reports must never leak across unauthorized user accounts.
- **Priority:** P0 (Must Have)
- **Implementation Phase:** Phase 2 & Phase 7
- **Verification Method:** Automated security tests attempting cross-tenant resource retrieval.

#### `NFR-PRIV-001`: Private-by-Default Submissions & Erasure
- **Description:** Submitted documents must not be added to general search indexes without explicit user consent. Hard deletion must erase all traces within 5 seconds of request execution.
- **Priority:** P0 (Must Have)
- **Implementation Phase:** Phase 2 & Phase 7
- **Verification Method:** Verification script asserting zero database records and zero filesystem residue after document deletion.

---

### 3.2 Performance & Scalability

#### `NFR-PERF-001`: Analysis Latency Target
- **Description:** For a 10-page document (approx. 3,500 words) analyzed against an indexed collection of 1,000 documents in Mode C, analysis latency must achieve p95 $\le 180$ seconds on 8 CPU cores / 16 GB RAM (CPU-only inference).
- **Priority:** P1 (Should Have)
- **Implementation Phase:** Phase 5 & Phase 7
- **Verification Method:** Load testing script profiling end-to-end execution across 10-page benchmark documents.

#### `NFR-PERF-002`: Direct Comparison Responsiveness
- **Description:** Mode A direct pairwise comparison for documents $\le 5$ pages must complete within 10 seconds p90.
- **Priority:** P0 (Must Have)
- **Implementation Phase:** Phase 3 & Phase 4
- **Verification Method:** Latency profiling across 50 paired test documents.

#### `NFR-SCAL-001`: Asynchronous Queue Decoupling
- **Description:** Web requests must never block on CPU-intensive extraction, embedding, or alignment tasks. All heavy compute must be dispatched to Redis-backed worker queues.
- **Priority:** P0 (Must Have)
- **Implementation Phase:** Phase 1 & Phase 2
- **Verification Method:** Concurrency test showing API responds with HTTP 202 in $<200$ ms under concurrent job submissions.

---

### 3.3 Reliability & Availability

#### `NFR-REL-001`: Resilient Job State Transitions
- **Description:** Every asynchronous task must adhere strictly to the state lifecycle (`queued` $\rightarrow$ `processing` $\rightarrow$ `completed` | `failed` | `cancelled`). Unhandled exceptions must transition the job to `failed` with sanitized error details.
- **Priority:** P0 (Must Have)
- **Implementation Phase:** Phase 1 & Phase 7
- **Verification Method:** Chaos tests injecting worker process terminations and verifying database state integrity.

#### `NFR-REL-002`: Document Extraction Fault Tolerance
- **Description:** Failure to extract text from a single corrupted page or malformed reference document must not crash the entire analysis batch.
- **Priority:** P1 (Should Have)
- **Implementation Phase:** Phase 2
- **Verification Method:** Ingestion test with intentionally corrupted test documents mixed into valid batches.

---

### 3.4 Accessibility & Usability

#### `NFR-A11Y-001`: Web Content Accessibility (WCAG 2.1 AA)
- **Description:** The frontend interface must comply with WCAG 2.1 AA guidelines, supporting full keyboard navigation, screen-reader semantic tags, and accessible color contrast ratios for similarity highlights.
- **Priority:** P1 (Should Have)
- **Implementation Phase:** Phase 6
- **Verification Method:** Automated accessibility audits using axe-core and manual keyboard traversal reviews.

---

### 3.5 Observability & Deployment

#### `NFR-OBS-001`: Structured JSON Logging & Telemetry
- **Description:** Backend services and workers must emit structured JSON logs containing correlation IDs (`trace_id`, `job_id`, `user_id`) with privacy-safe redaction of document text.
- **Priority:** P0 (Must Have)
- **Implementation Phase:** Phase 1 & Phase 7
- **Verification Method:** Automated log inspection asserting JSON formatting, absence of PII/text leaks, and presence of correlation IDs.

#### `NFR-DEP-001`: Deterministic Containerized Orchestration
- **Description:** The entire application stack (Web, API, Worker, PostgreSQL + pgvector, Redis) must deploy cleanly via a single `docker compose up` command on Linux, macOS, and Windows WSL2.
- **Priority:** P0 (Must Have)
- **Implementation Phase:** Phase 1 & Phase 7
- **Verification Method:** Clean-room deployment test inside isolated CI runner verifying container health probes.
