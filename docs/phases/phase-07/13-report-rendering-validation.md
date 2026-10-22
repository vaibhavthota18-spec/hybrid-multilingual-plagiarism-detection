# Phase 7 — Report Rendering & Indic Text Shaping Validation

## 1. Problem Statement & Root Cause
In initial builds, ReportLab's standard Type 1 fonts (`Helvetica`, `Courier`) only supported Latin-1 characters. Non-ASCII excerpts were sanitized using `.encode("ascii", "replace")`, which converted Hindi and Telugu text into `????`. Furthermore, standard ReportLab lacks HarfBuzz-level OpenType complex text shaping for Indic matras and conjuncts.

## 2. Solution Implemented
1. **Unicode TrueType Registration:**
   - Automatically detects and registers `Nirmala.ttc` from `C:\Windows\Fonts\`:
     - `NirmalaUI` (Regular, `subfontIndex=0`)
     - `NirmalaUIBold` (Bold, `subfontIndex=1`)
   - Replaces ASCII replacement with `html.escape()` XML-safe entity encoding.
2. **Verification Evidence:**
   - Generated PDF test containing:
     - Hindi: `कृत्रिम बुद्धिमत्ता और मशीन लर्निंग`
     - Telugu: `కృత్రిమ మేధస్సు మరియు సహజ భాషా ప్రాసెసింగ్`
   - Verified that `pypdf` extracts the exact Unicode strings with matras intact.
   - Rendered PDF page to `data/report_indic_rendered.png` via `pypdfium2` and verified visual glyph arrangement.
