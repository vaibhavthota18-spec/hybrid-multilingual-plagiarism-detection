# Phase 2 — Localhost Demonstration & Operator Walkthrough Guide

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Phase:** Phase 2 — Document Ingestion and Reference Collection Management  
**Environment:** Windows 11 Native Localhost  

---

## 1. Prerequisites & Server URLs

Both servers run concurrently on your local machine:
- **Frontend Web Application:** [http://127.0.0.1:5173](http://127.0.0.1:5173)
- **Backend API & Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Backend OpenAPI Specification:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

> [!NOTE]
> If you ever need to restart both servers together, simply execute:
> ```powershell
> powershell -ExecutionPolicy Bypass -File scripts\run_local.ps1
> ```

---

## 2. Interactive Operator Walkthrough (7 Steps)

### Step 1: Open Document Ingestion Workspace
1. In your web browser, navigate to [http://127.0.0.1:5173](http://127.0.0.1:5173).
2. Click the **Document Ingestion** tab in the top navigation bar.
3. You will see four sub-tabs:
   - **Upload Documents**
   - **Document Library**
   - **Reference Collections**
   - **Comparison Setup**

### Step 2: Upload Multilingual Sample Documents
1. In the **Upload Documents** tab, drag and drop or browse to select sample files located in `data/samples/`:
   - `sample_english.txt` (English academic text)
   - `sample_hindi.txt` (Devanagari text with combining vowels and danda punctuation)
   - `sample_telugu.txt` (Telugu text with Brahmic conjuncts and viramas)
   - `sample_paper.pdf` (Multi-page PDF research paper)
   - `sample_research.docx` (Word document containing formatted tables and headings)
2. You can leave Language Hint as **Auto Detect** or specify a target language.
3. Click **Upload Document**. A success banner will confirm upload and ingestion completion.

### Step 3: Inspect Document Library
1. Click the **Document Library** sub-tab.
2. Observe the tabular document manifest:
   - File format icon (`TXT`, `PDF`, `DOCX`).
   - Detected language badges (`en`, `hi`, `te`).
   - Word count, character count, page count, and status badge (`Completed`).
3. Use the search box to filter documents by title or filename.

### Step 4: Inspect Raw Text and Segmented Passages
1. In any document row, click **Inspect**.
2. A dual-tab inspector modal opens:
   - **Raw Text Tab:** Shows unnormalized original text, total character count, word count, and language.
   - **Passages Tab:** Displays deterministic segmented passages. Notice the exact start and end code-point character offsets:
     `Offset: [0 - 497] | 61 words`
   - Notice that Indic combining marks and sentence boundaries (`।`, `.`) are preserved with exact alignment.
3. Click **Close** to exit the modal.

### Step 5: Build a Reference Collection (Corpus)
1. Click the **Reference Collections** sub-tab.
2. Under "Create Reference Collection", enter:
   - **Name:** `Academic Benchmark Corpus 2026`
   - **Description:** `Verified reference texts for multilingual comparison`
3. Click **Create Collection**. The collection appears in the list.
4. Use the "Add Document" dropdown to add reference documents into the corpus (e.g. `sample_hindi.txt`, `sample_telugu.txt`, `sample_paper.pdf`).
5. Notice the document count badge update dynamically to `3 documents`.

### Step 6: Configure & Validate Comparisons (3 Modes)
1. Click the **Comparison Setup** sub-tab.
2. Select your candidate submission document from the dropdown (e.g. `sample_english.txt`).
3. Test all three comparison modes:
   - **Mode A: Direct Comparison (1:1):** Select one reference document from the dropdown and click **Validate Comparison Setup**.
   - **Mode B: One-to-Many (1:N):** Check multiple checkboxes for reference documents and click **Validate Comparison Setup**.
   - **Mode C: Corpus Comparison (1:Collection):** Select `Academic Benchmark Corpus 2026` from the dropdown and click **Validate Comparison Setup**.

### Step 7: Verify Honest Phase 3 Boundary Notice
1. When you click **Validate Comparison Setup**, observe the status banner:
   > **Status: READY FOR ANALYSIS**  
   > *"Documents are ready for analysis. Similarity detection will be implemented in Phase 3."*
2. Confirm that **strictly zero fake plagiarism percentages, mocked similarity scores, or fictitious heatmaps** are displayed anywhere in the application.

---

## 3. Running Automated Acceptance Scripts

To execute the entire 24-step verification workflow automatically from the command line:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_tests.ps1
```
This runs OpenAPI contract validation, Phase 0 consistency guards, 67 backend pytest tests, 13 frontend vitest tests, production build, and all 24 localhost acceptance steps.
