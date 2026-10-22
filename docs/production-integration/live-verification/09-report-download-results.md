# 09 — Multi-Format Report Download & Indic Typography Verification

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Milestone:** Live Deployment & Production Verification Audit  
**Date:** 2026-10-16  
**Files:** `apps/backend/src/plagiarism/services/reports/report_generator.py`, `apps/web/src/pages/ResultsDashboardPage.tsx`  
**Status:** RESOLVED & VERIFIED  

---

## 1. Resolution of the Critical Report Download Defect

### Original Problem
In earlier iterations, clicking "Download PDF Report" in the browser resulted in broken entries titled `report.customization` with browser error *"Site wasn't available"*.

### Root Cause
1. Large syllabus documents (>1,000 pt passage blocks) exceeded the 708 pt frame height of ReportLab, throwing an unhandled `LayoutError`.
2. Frontend used an unhandled `<a download>` tag pointing directly to an API route, causing browser timeout when ReportLab crashed.

### Complete Engineering Solution Implemented
1. **Dual PDF Engine:** Headless Chromium print-to-pdf is the primary engine, producing 100% vector-faithful Indic typography and native CSS page-breaks. ReportLab serves as a headless fallback without unsafe `KeepTogether` constraints.
2. **Async Blob Download Handler:** The frontend in `ResultsDashboardPage.tsx` executes an asynchronous authenticated fetch, verifies HTTP 200, handles errors with visual alerts, and streams the binary blob with dynamic filename assignment.
3. **HTTP Content-Disposition Headers:** The backend formats human-readable filenames:
   - PDF: `Content-Disposition: attachment; filename="<Document_Title>_Similarity_Report.pdf"`
   - HTML: `Content-Disposition: attachment; filename="<Document_Title>_Similarity_Report.html"`
   - JSON: `Content-Disposition: attachment; filename="<Document_Title>_Similarity_Report.json"`

---

## 2. Linux Indic Font Verification (Hindi & Telugu)

The Dockerfile installs `fonts-noto-core`, `fonts-deva`, and `fonts-telu`. `report_generator.py` registers Linux font paths (`/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf` and `NotoSansTelugu-Regular.ttf`), ensuring complex ligature glyphs (e.g. `बुद्धिमत्ता`, `మేధస్సు`) render with accurate vowel signs and no missing character boxes.
