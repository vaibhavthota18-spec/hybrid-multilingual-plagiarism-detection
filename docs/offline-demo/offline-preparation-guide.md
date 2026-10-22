# One-Time Online Preparation Guide for Classroom Demonstration

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Purpose:** Pre-download and verify all model weights, node modules, Python packages, and fonts while Wi-Fi is available, so the entire application can run 100% offline during the classroom demonstration.

---

## 1. Prerequisites (While Connected to Internet)

Ensure your laptop has:
1. **Windows 11** (64-bit).
2. **Python 3.12** installed and available in PATH.
3. **Node.js 18+ / 20+** installed and available in PATH.
4. **Visual Studio Code** installed.
5. Internet connection (Wi-Fi or Ethernet) active for this preparation phase only.

---

## 2. Automated One-Command Preparation

Open a PowerShell terminal, navigate to the project directory, and run:

```powershell
cd "C:\Users\vaibh\OneDrive\Documents\plagarism engine"
powershell -ExecutionPolicy Bypass -File "scripts\prepare-offline-demo.ps1"
```

### What this script automatically performs:
1. **Validates Python virtual environment** at `apps/backend/.venv` (Python 3.12).
2. **Validates Node.js dependencies** at `apps/web/node_modules`.
3. **Downloads/verifies the complete Hugging Face model snapshot** for `intfloat/multilingual-e5-small` (revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`).
4. **Synchronizes model snapshot to persistent local storage:**
   `C:\Users\<username>\AppData\Local\plagiarism_engine\model_cache`  
   *(This ensures that even if OneDrive dehydrates or manages files on demand, the offline model is 100% physically present on local NVMe disk).*
5. **Executes live offline multilingual inference verification** across English, Hindi, and Telugu test sentences to confirm 384-dimensional normalized vector generation.
6. **Validates native Windows Indic fonts** (`C:\Windows\Fonts\Nirmala.ttc`) for pixel-perfect PDF rendering of Hindi and Telugu.
7. **Verifies SQLite database and private document storage accessibility.**
8. **Compiles the Vite frontend bundle** (`npx vite build`) with zero errors.

---

## 3. OneDrive Files-On-Demand Precaution

Because the project folder is located within OneDrive:
`C:\Users\vaibh\OneDrive\Documents\plagarism engine`

Windows Storage Sense or OneDrive can dehydrate files into cloud-only placeholders (`.tmp` or cloud icon).

### Action to Prevent Dehydration:
1. Open Windows File Explorer.
2. Navigate to `C:\Users\vaibh\OneDrive\Documents\`.
3. Right-click the folder **`plagarism engine`**.
4. Click **"Always keep on this device"**.
5. Wait for the green checkmark icon to confirm that all files are stored physically on your laptop.

*(Note: Our system also stores a second copy of the AI model snapshot in `AppData\Local\plagiarism_engine\model_cache`, which is outside OneDrive and will never be dehydrated).*

---

## 4. Verification Check

To confirm that the offline preparation succeeded, run:

```powershell
& "apps\backend\.venv\Scripts\python.exe" scripts\prepare_offline_assets.py
```

**Expected Console Output:**
```
--- 1. Locating Storage and Cache Directories ---
Repo storage cache:      C:\Users\vaibh\OneDrive\Documents\plagarism engine\storage\model_cache
Persistent local cache:  C:\Users\vaibh\AppData\Local\plagiarism_engine\model_cache

--- 2. Checking AI Model Snapshot Files ---
Verified model snapshot already exists locally.

--- 3. Synchronizing to Persistent Storage outside OneDrive ---
Model snapshot is available in both repo storage and persistent LocalAppData.

--- 4. Validating Offline Multilingual Inference (EN, HI, TE) ---
Loading weights: 100%|##########| 199/199 [00:00<00:00, 3200it/s]
Computed 3 embeddings (384-dimensional). L2 squared norms: [1.0, 1.0, 1.0]
  [English] (63 chars) -> vector norm: 1.0 (L2-normalized)
  [Hindi] (70 chars) -> vector norm: 1.0 (L2-normalized)
  [Telugu] (53 chars) -> vector norm: 1.0 (L2-normalized)

=======================================================
ALL OFFLINE AI ASSETS VERIFIED SUCCESSFULLY!
=======================================================
```

Once this output appears, your laptop is **fully prepared**. You can disconnect all Wi-Fi, Ethernet, and mobile hotspots before entering the classroom.
