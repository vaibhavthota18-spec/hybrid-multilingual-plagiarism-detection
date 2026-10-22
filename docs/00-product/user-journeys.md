# User Journeys & Operational Workflows

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Overview

This document specifies the end-to-end user journeys supported by the platform. For each journey, we define user preconditions, UI interactions, expected backend behavior, permission checks, and error/exception handling paths.

---

## 2. Journey 1: Guest Visiting the Website

### Persona & Goal
An unauthenticated guest lands on the homepage seeking to understand what the tool does and test basic functionality.

### Steps
1. **Access Homepage:** User visits `/`.
2. **System Response:** Presents a clean, utility-focused landing interface explaining:
   - Three comparison modes (Direct, One-to-Many, Corpus).
   - Supported file formats (PDF, DOCX, TXT) and languages (English, Hindi, Telugu).
   - Privacy guarantee (no public indexing without permission, zero data retention upon deletion).
3. **Authentication Choice:**
   - Guest can authenticate (login/register) to access saved history and institutional corpora.
   - Guest can execute a lightweight Direct Comparison (Mode A) using a temporary session identifier.

### Exceptions & Errors
- Rate limiting: If an unauthenticated IP exceeds 5 comparisons per hour, the UI presents HTTP 429 with a countdown and an invitation to log in.

---

## 3. Journey 2: Student Checking Two Documents (Mode A: Direct Comparison)

### Persona & Goal
A student wants to verify that their revised essay does not accidentally copy text from a specific draft or reference article.

### Steps
1. **Select Mode:** User selects "Direct Comparison" on the dashboard.
2. **Upload Submission Document:** Drags essay file (`essay_v2.pdf`) into the Submission upload zone.
3. **Upload Reference Document:** Drags source file (`source_article.docx`) into the Reference upload zone.
4. **Configure Options:**
   - Toggle "Exclude Quotations" (default: checked).
   - Toggle "Exclude References / Bibliography" (default: checked).
5. **Initiate Analysis:** Clicks "Compare Documents".
6. **Background Processing:**
   - System returns HTTP 202 Accepted with `job_id` and redirects to `/analyses/{id}`.
   - Progress bar updates: Uploading $\rightarrow$ Extracting Text $\rightarrow$ Generating Fingerprints $\rightarrow$ Aligning Passages $\rightarrow$ Finalizing Report.
7. **Inspect Results:**
   - Dashboard reveals: Lexical Coverage (e.g., 4.2%), Semantic Coverage (e.g., 8.5%).
   - Interactive document viewer highlights matching spans with color coding: Green/Yellow for paraphrasing, Orange/Red for verbatim text.
   - Clicking a highlighted span scrolls the right-hand panel directly to the corresponding source paragraph.

### Exceptions & Errors
- **Unextractable Text:** If `essay_v2.pdf` is a scanned image with no text layer, system transitions job to `failed` with code `EXTRACTION_EMPTY_TEXT` and suggests uploading a searchable PDF or DOCX.
- **File Exceeds Limit:** Uploading a file $>30$ MB triggers immediate client-side validation rejection before network transfer.

---

## 4. Journey 3: Researcher Checking Multiple References (Mode B: One-to-Many Comparison)

### Persona & Goal
An academic author wants to check their 25-page manuscript against 8 related reference papers before journal submission.

### Steps
1. **Select Mode:** User selects "One-to-Many Comparison".
2. **Upload Submission:** Uploads `manuscript_final.pdf`.
3. **Upload Reference Batch:** Uploads 8 reference PDF/DOCX files simultaneously.
4. **Initiate Analysis:** Clicks "Analyze Against References".
5. **Processing Execution:**
   - Worker extracts and fingerprints the manuscript.
   - Worker extracts all 8 reference documents, creates an ephemeral in-memory inverted index, and computes multilingual embeddings.
   - Parallel lexical and semantic queries match manuscript passages against the reference batch.
6. **Review Findings by Source:**
   - Report presents an executive breakdown: Source A (5% match), Source B (1.2% match), Sources C–H (0% match).
   - Filtering allows the researcher to isolate findings from Source A specifically.

### Exceptions & Errors
- **Partial Extraction Failure:** If 1 of the 8 reference files is corrupted, the system logs a non-blocking warning, marks that reference as `extraction_failed`, and processes the remaining 7 valid documents, explicitly flagging the skipped file in the final report.

---

## 5. Journey 4: User Searching an Authorized Corpus (Mode C: Corpus Search)

### Persona & Goal
A university instructor checks a submitted student paper against a departmental repository containing 1,500 indexed past assignments and reference dissertations.

### Steps
1. **Select Mode:** User selects "Corpus Search".
2. **Choose Authorized Collection:** Selects "Department of Computer Science — Theses 2024–2026" from a dropdown of collections they are authorized to access.
3. **Upload Submission:** Uploads `student_paper.pdf`.
4. **Execute Search:**
   - API verifies user's `READ` permission on the specified collection (`CollectionPermission`).
   - Query passages are retrieved via Winnowing fingerprint matches in the collection's inverted index and exact vector search across the collection's pre-computed `pgvector` embeddings.
5. **Review Attributed Sources:**
   - Matches are mapped back to indexed corpus documents, displaying author, title, submission date, and matched excerpts.

### Exceptions & Errors
- **Unauthorized Collection Access:** If a user manipulates API parameters to query a private collection owned by another department, the system rejects the request with HTTP 403 Forbidden (`AUTH_INSUFFICIENT_COLLECTION_PERMISSIONS`).
- **Empty Collection:** If the selected collection contains no indexed documents, system warns the user immediately before launching the job.

---

## 6. Journey 5: Reviewer Analyzing Findings & Human-in-the-Loop Review

### Persona & Goal
An academic reviewer reviews an automatically generated finding report to determine whether flagged similarities represent academic misconduct or legitimate scholarly citation.

### Steps
1. **Open Analysis:** Reviewer navigates to `/analyses/{id}`.
2. **Inspect Finding Cards:**
   - Finding 1: 120-token exact match against a textbook definition.
   - Finding 2: Paraphrased Telugu translation of an English research paper methodology section.
3. **Side-by-Side Verification:**
   - Reviewer clicks Finding 1. UI renders dual-pane view: Left shows submission text; Right shows source text with matched words highlighted.
4. **Apply Human Review Action:**
   - Finding 1: Reviewer notes proper blockquote formatting. Selects action: "Mark as Valid Citation / Quote", types optional note "Standard definition with proper attribution", and clicks Save.
   - Finding 2: Reviewer identifies uncredited translation. Selects action: "Flag as Suspected Plagiarism".
5. **Dynamic Metric Recalculation:**
   - The UI updates the "Adjusted Net Plagiarism Score" by subtracting validated citations while retaining uncredited matches.

---

## 7. Journey 6: User Downloading an Official PDF Report

### Persona & Goal
An educator needs an official, printable audit report to attach to an academic evaluation committee dossier.

### Steps
1. **Trigger Export:** Clicks "Download PDF Report" on the analysis view.
2. **Export Options Dialog:**
   - Include/Exclude Human Review Notes.
   - Include/Exclude Full Side-by-Side Passages.
   - Select Language for Report Headers (English / Hindi / Telugu).
3. **Report Generation:**
   - Backend renders an immutable PDF report using ReportLab or Weasyprint, stamping:
     - Document SHA-256 hash.
     - Submission timestamp and analysis identifier.
     - Lexical & Semantic coverage charts.
     - Source attribution breakdown.
     - Human reviewer signatures and notes.
4. **Delivery:** Browser initiates file download (`report-analysis-7a8b9c.pdf`).

---

## 8. Journey 7: User Deleting a Document (Right to Erasure)

### Persona & Goal
A student or researcher wishes to delete their submitted document and all associated data after receiving their report.

### Steps
1. **Initiate Deletion:** Clicks "Delete Document" on `/documents/{id}`.
2. **Confirmation Dialog:** UI displays warning: "This will permanently delete the original file, extracted text, fingerprint hashes, vector embeddings, and generated findings. This action cannot be undone."
3. **Execute Deletion:** User confirms deletion.
4. **System Response:**
   - API issues cascading database deletion.
   - Storage service removes raw file from disk (`/storage/uploads/{id}.pdf`).
   - pgvector deletes passage embedding rows.
   - Inverted index removes fingerprint tokens.
   - Analysis results referencing this document are sanitized or purged according to collection policy.
   - Returns HTTP 204 No Content.

---

## 9. Journey 8: User Encountering Processing Failures

### Persona & Goal
A user experiences an unexpected upload or background processing error and requires clear, actionable guidance.

### Error Scenarios & System Responses

| Scenario | System Diagnosis | User-Facing Actionable Feedback |
|---|---|---|
| **Corrupted File Header** | Magic-byte mismatch (e.g., file named `.pdf` is actually an HTML error page). | "The uploaded file could not be recognized as a valid PDF. Please check the file and try again." |
| **Password-Protected PDF** | PyMuPDF raises `PdfEncryptedError`. | "This PDF is password-protected. Please remove the password and re-upload." |
| **Worker Timeout** | Document exceeds 100 pages or worker process crashes. | Job state marked `failed`. User receives message: "Processing timed out. We suggest analyzing documents under 50 pages in direct mode." System records error in audit log. |
| **Unsupported Language** | Language identification detects script outside EN/HI/TE. | System processes lexical matching but displays warning: "The detected language is not officially calibrated for semantic analysis. Semantic matching may be limited." |
