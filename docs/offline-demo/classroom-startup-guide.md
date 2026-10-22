# Classroom Offline Startup & Quick Demonstration Guide

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Target Environment:** Native Windows 11 Laptop (No Wi-Fi / Completely Disconnected)  

---

## 1. Classroom One-Command Launch (Wi-Fi Turned OFF)

1. **Disconnect Wi-Fi / Airplane Mode:**
   Turn off Wi-Fi on your Windows 11 laptop. Ensure no mobile data or Ethernet is connected.

2. **Open PowerShell as Normal User (No Administrator Required):**
   ```powershell
   cd "C:\Users\vaibh\OneDrive\Documents\plagarism engine"
   ```

3. **Run the One-Command Offline Launcher:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File "scripts\start-offline-demo.ps1"
   ```

### What Happens Automatically:
- Sets `APP_RUNTIME_MODE=local` (SQLite + bounded thread pool executor; no Docker, no WSL2, no Redis).
- Sets `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`.
- Points to the persistent offline model cache at `%LOCALAPPDATA%\plagiarism_engine\model_cache`.
- Frees and binds ports `8000` (FastAPI) and `5173` (Vite).
- Starts the FastAPI backend and automatically polls `http://127.0.0.1:8000/health` until ready.
- Starts the React/Vite development server.
- Displays the ready banner:
  ```
  ==========================================================
    CLASSROOM DEMONSTRATION IS READY (100% OFFLINE)           
  ==========================================================
    Web Application:      http://localhost:5173     
    Interactive API Docs: http://localhost:8000/docs 
    Backend Health Check: http://localhost:8000/health
    Mode:                 APP_RUNTIME_MODE=local (SQLite)    
    AI Model:             intfloat/multilingual-e5-small     
    Network Connectivity: None Required (100% Localhost)     
  ```

4. **Open Browser:**
   Open Google Chrome, Microsoft Edge, or Firefox and go to:
   **`http://localhost:5173`**

---

## 2. Recommended 5-Minute Professor Live Demonstration Flow

| Step | Action on UI (`http://localhost:5173`) | What to Explain to Professor |
|---|---|---|
| **1. Upload Document** | Click **"Select or Drop Document"** -> Choose a PDF/DOCX/TXT file. | Ingestion extracts raw text, validates MIME magic bytes, and applies Unicode NFC normalization to preserve Indic matras. |
| **2. Select Mode & References** | Choose **"Hybrid Detection"** -> Select a reference document or collection. | Explain that Hybrid mode runs both Winnowing lexical fingerprinting and Multilingual E5 semantic embedding search. |
| **3. Click Analyze** | Click **"Analyze Document"**. | Show that the analysis completes smoothly offline in seconds without hanging or requiring internet. |
| **4. Side-by-Side Highlighting** | Click on matched sources to view highlighted passages. | Explain the color coding: verbatim exact matches vs semantic paraphrase/translation matches. |
| **5. Human Reviewer Action** | Click on a finding -> select **"Quoted / Cited"** or **"Exclude"**. | Show that original AI scores are preserved, while "Reviewer-Adjusted Coverage %" dynamically updates in real time. |
| **6. Download PDF Report** | Click **"Download Report"** -> choose **"PDF"**. | Show the generated multi-page audit report featuring pixel-perfect Hindi and Telugu text rendering using Nirmala UI font. |

---

## 3. How to Cleanly Shut Down and Restart

### Clean Shutdown
In the terminal where `start-offline-demo.ps1` is running:
- Simply press **Enter** or **Ctrl+C**.
- The script automatically terminates the FastAPI backend and Node/Vite processes and frees ports 8000 and 5173.

### Cold Restart (Still Offline)
To restart the application while remaining offline:
```powershell
powershell -ExecutionPolicy Bypass -File "scripts\start-offline-demo.ps1"
```
Reopen `http://localhost:5173` and click **"History"** to show that previous analysis records and reviewer decisions persisted cleanly in SQLite.

---

## 4. Troubleshooting in the Classroom

| Symptom | Cause | One-Line Fix |
|---|---|---|
| Port 8000 or 5173 already in use | Previous process lingering | `Get-Process python, node -ErrorAction SilentlyContinue \| Stop-Process -Force` |
| Execution Policy Error | PowerShell restricts script execution | Pass `-ExecutionPolicy Bypass` as shown in the launch command. |
| Browser shows "Site can't be reached" | Backend still booting | Wait 3 seconds and refresh `http://localhost:5173`. Check that `http://localhost:8000/health` returns `{"status":"ok"}`. |
| Model not found error | First-time preparation not run | Run `powershell -ExecutionPolicy Bypass -File scripts\prepare-offline-demo.ps1` once before heading to class. |
