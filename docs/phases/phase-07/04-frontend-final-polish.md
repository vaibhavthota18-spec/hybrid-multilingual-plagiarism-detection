# Phase 7 — Frontend Final Polish & Accessibility

## 1. UI Principles & Aesthetics
- **Canvas:** Slate-50 (`#F8FAFC`) with pure white card surfaces and Slate-200 borders.
- **Workflow:** Strict adherence to the 5-step journey: **Upload $\to$ Compare $\to$ Analyze $\to$ Review $\to$ Download**.
- **No Developer Clutter:** Internal database pools, vector dimensions, and debug logs are isolated from end-user viewports.

## 2. Component Polish & Responsive Verification
- **Header & Navigation:** Sticky top navbar with brand mark, active route indicator, and quick links to Analysis History and Document Library.
- **Central Upload Hero:** Supports drag-and-drop, file browser dialog, and format guidance chips for PDF, DOCX, and TXT with multilingual language tags (English, Hindi, Telugu).
- **Dual-Pane Evidence Viewer:**
  - Synchronized bidirectional scrolling with scroll lock toggle.
  - Multi-category highlighting:
    - Exact Copy: Rose (`#FFE4E6` / `#E11D48`)
    - Near-Exact: Orange (`#FFEDD5` / `#EA580C`)
    - Paraphrase: Amber (`#FEF3C7` / `#D97706`)
    - Translation: Purple (`#F3E8FF` / `#9333EA`)
  - Strikethrough visual styling for findings marked `exclude` or `quoted_cited`.
- **Responsive Viewports Tested:**
  - Desktop: 1440 × 900
  - Laptop: 1366 × 768
  - Tablet: 1024 × 768
  - Mobile: 390 × 844 (collapsible drawer navigation and stacked viewports).
