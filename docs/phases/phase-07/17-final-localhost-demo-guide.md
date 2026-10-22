# Phase 7 — Live Localhost Demonstration Guide

## 1. Quick Startup
To start both backend and frontend on Windows localhost:
```powershell
.\scripts\start-local.ps1
```
Open browser to: [**`http://localhost:5173`**](http://localhost:5173)

---

## 2. 5-Minute Professor Demonstration Script

### Step 1: Central Document Upload (Stage 1)
- On the homepage, drag and drop or browse to select your test submission document (`.txt`, `.pdf`, or `.docx`).
- Point out the clean Slate-50 layout and zero confusing developer metrics.

### Step 2: Choose Reference Document (Stage 2)
- Select **Direct File Compare** and upload or select the target comparison source.
- Explain that the engine supports English, Hindi (हिन्दी), and Telugu (తెలుగు).

### Step 3: Run Hybrid AI Analysis (Stages 3 & 4)
- Select **Hybrid Detection (Recommended)**.
- Explain the dual engine:
  - **Winnowing ($k=25, w=16$):** Captures verbatim exact copying.
  - **Multilingual E5 ($384\text{d}$):** Captures semantic paraphrasing and cross-language translation.
- Watch the 5-step non-intrusive progress bar complete.

### Step 4: Inspect Evidence in the Dual-Pane Viewer (Stage 5)
- Show the side-by-side synchronized document inspection panes.
- Click any finding card: observe both left and right panes jump smoothly to the exact character spans.
- Point out the distinct highlight colors (Exact Copy: Rose; Paraphrase: Amber; Translation: Purple).

### Step 5: Perform Human Review & Note Score Adjustment
- Select a finding that represents common domain terminology or an attributed quotation.
- Click **Exclude** or **Quoted / Cited**.
- Add a reviewer justification note (e.g., *"Legitimate citation according to IEEE standards"*).
- **Highlight the key mathematical invariant:**
  - The **Original Evidence** remains locked at its raw score (e.g., 65.0%).
  - The **Reviewer-Adjusted Score** recalculates dynamically to reflect the verified active plagiarism union.

### Step 6: Export Multi-Format Audit Reports
- Click **Download Report** and select:
  1. **Formal PDF:** Open the generated PDF report; show the executive summary, sources table, and finding cards.
  2. **Offline Printable HTML:** Show that it can be opened without internet and printed cleanly via `Ctrl+P`.
  3. **JSON Audit Export:** Show the machine-readable schema for university LMS/SIS integration.
