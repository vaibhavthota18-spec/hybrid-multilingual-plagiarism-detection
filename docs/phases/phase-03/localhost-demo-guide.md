# Localhost Demonstration & Verification Guide: Phase 3

This guide provides step-by-step instructions for launching and demonstrating the Lexical Plagiarism Detection Engine and Results Dashboard natively on Windows 11.

---

## 1. Prerequisites & Terminal Setup

Ensure PowerShell is open at the repository root:
`C:\Users\vaibh\OneDrive\Documents\plagarism engine`

All required dependencies are already installed in:
- Backend: `apps\backend\.venv`
- Frontend: `apps\web\node_modules`

---

## 2. Launching the Localhost Servers

### Terminal 1: Backend API Server (FastAPI on Port 8000)
```powershell
$env:PATH = "C:\Users\vaibh\AppData\Local\Programs\Python\Python312;C:\Users\vaibh\AppData\Local\Programs\Python\Python312\Scripts;" + $env:PATH
& "apps\backend\.venv\Scripts\python.exe" -m uvicorn plagiarism.main:app --host 127.0.0.1 --port 8000 --reload
```
Verify backend readiness by navigating to:
- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Interactive Swagger docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Terminal 2: Frontend Web Client (Vite on Port 5173)
```powershell
$env:PATH = "C:\Users\vaibh\AppData\Local\Programs\NodeJS;C:\Users\vaibh\AppData\Local\Programs\Git\cmd;" + $env:PATH
cd apps\web
npm run dev
```
Open your browser to:
- [http://localhost:5173](http://localhost:5173)

---

## 3. Demonstration Workflow

### Step 1: Upload Documents (Document Ingestion Tab)
1. In the top navigation bar, click **Document Ingestion**.
2. Drag and drop or upload sample documents from `data/samples/`:
   - `sample_english.txt`
   - `sample_hindi.txt`
   - `sample_telugu.txt`
   - `sample_paper.pdf`
3. Click **Upload & Process Documents**. Text extraction, language identification, and passage segmentation run immediately.

### Step 2: Configure & Execute Analysis (Comparison Setup Tab)
1. Within Document Ingestion, switch to the **Comparison Setup** tab.
2. Select **Direct Comparison (1:1)** mode.
3. In **Submission Document**, select `sample_english.txt`.
4. In **Reference Document**, select another document or a copy.
5. Click **Validate Comparison Inputs**. A green banner confirms inputs are valid.
6. Click the newly activated **Execute Similarity Analysis** button.
7. The system computes token Winnowing fingerprints, aligns passages, verifies character offsets, and routes you directly to the Results Dashboard!

### Step 3: Inspect Findings on the Results Dashboard
1. The **Overall Lexical Coverage** card displays the non-overlapping token match percentage (e.g. `100.0%` for identical text, or `50.0%` for partial copy).
2. The **Detection Engine** card confirms `Winnowing (k=25, w=16) | Guarantee: t=40 tokens | BM25 ranking`.
3. In the **Side-by-Side Document Viewer**:
   - The left pane displays the **Candidate Submission Text** with highlighted matched passages.
   - The right pane displays the **Matched Reference Source Text** with corresponding highlights.
   - Click on any highlighted `<mark>` span to view the **Inspecting Match Finding** card with verbatim excerpts, exact offsets, and confidence ratings.

### Step 4: Manage History & Run Quick Analyses (Similarity Analysis Tab)
1. Click **Similarity Analysis** in the main navigation bar.
2. View your complete analysis history table showing Analysis IDs, modes, lexical similarity scores, match counts, and execution runtimes.
3. Click **Run New Analysis** to open the quick-run drawer. Select a mode (Direct, One-to-Many, or Corpus), pick documents, and click **Start Analysis** to watch real-time polling progress.
4. Click **Inspect** on any completed analysis to view its dual-pane Results Dashboard.
5. Click the trash icon to test cascading deletion of an analysis and its findings.
