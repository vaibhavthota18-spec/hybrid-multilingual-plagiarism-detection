# Phase 4 Localhost Demo Guide: Running & Exploring Hybrid Plagiarism Detection

## 1. Prerequisites

Native Windows 11 environment with Python 3.12 and Node.js:
- Backend virtual environment: `apps\backend\.venv`
- Frontend dependencies: `apps\web\node_modules`
- Downloaded model weights: `storage\model_cache`

---

## 2. Starting the Localhost Servers

Open two separate PowerShell terminal tabs in the project root:

### Tab 1: FastAPI Backend
```powershell
cd "C:\Users\vaibh\OneDrive\Documents\plagarism engine"
.\apps\backend\.venv\Scripts\Activate.ps1
uvicorn plagiarism.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend runs at `http://127.0.0.1:8000` with Swagger docs at `http://127.0.0.1:8000/docs`.*

### Tab 2: React Frontend
```powershell
cd "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\web"
npm run dev
```
*Frontend runs at `http://localhost:5173`.*

---

## 3. Step-by-Step Interactive Walkthrough

### Step 1: Verify Active Model Info
1. Navigate to `http://127.0.0.1:8000/api/v1/analyses/models/info` in your browser.
2. Confirm the JSON response:
   - `model_name`: `intfloat/multilingual-e5-small`
   - `embedding_dimension`: `384`
   - `runtime_device`: `cpu`

### Step 2: Upload Reference & Submission Documents
1. Open `http://localhost:5173` in your browser.
2. Under **Ingestion Workspace**, upload a reference document (e.g. English science or tech article).
3. Upload a submission document containing paraphrased sections or Hindi/Telugu translations.

### Step 3: Run Hybrid Plagiarism Analysis
1. Switch to the **Comparison Setup** tab.
2. Select your submission document and reference document.
3. In the **Detection Engine Mode** selector, click **Hybrid AI (Recommended)**.
4. Click **Start Similarity Analysis**.

### Step 4: Inspect Results Dashboard
1. Review the 5 metric cards:
   - **Composite Hybrid Score**: Institutional weighted score.
   - **Lexical Coverage**: Verbatim match percentage.
   - **Semantic AI Coverage**: Paraphrase coverage percentage.
   - **Matched Sources** & **Total Findings**.
2. Examine the highlighted text viewer:
   - Red highlights: Exact copied text.
   - Amber highlights: Near-exact rewrites.
   - Violet highlights: Paraphrased passages.
   - Cyan highlights: Cross-language translations (e.g. `hi-en` or `te-en`).
3. Click any highlighted passage to open the side-by-side evidence inspector.

---

## 4. Running the Automated E2E Verification Script
```powershell
cd "C:\Users\vaibh\OneDrive\Documents\plagarism engine"
.\apps\backend\.venv\Scripts\python.exe scripts\verify_phase4_e2e.py
```
*Runs all 14 acceptance scenarios and outputs full pass confirmation.*
