# Phase 6 — Dual-Pane Synchronized Evidence Viewer

## 1. Architectural Architecture
The dual-pane evidence viewer renders the full text of the submitted document in the left pane and the matched reference document in the right pane.

## 2. Synchronized Highlighting and Offset Mapping
- **Exact Offsets:** Uses UTF-8 / Unicode character offsets (`submission_start_offset`, `submission_end_offset`, `reference_start_offset`, `reference_end_offset`).
- **Color Category Scheme:**
  - **Exact Copy / Identical:** Rose highlight (`bg-rose-100 text-rose-900 border-b-2 border-rose-500`).
  - **Near-Exact Copy:** Orange highlight (`bg-orange-100 text-orange-900 border-b-2 border-orange-500`).
  - **Paraphrase:** Amber highlight (`bg-amber-100 text-amber-900 border-b-2 border-amber-500`).
  - **Translation / Cross-lingual:** Purple highlight (`bg-purple-100 text-purple-900 border-b-2 border-purple-500`).
- **Reviewer Status Visual Hints:**
  - **Excluded / Quoted:** Opacity reduced to 40% with strikethrough styling to visually signal that it has been deducted from the score.
  - **Active / Kept:** Solid, high-contrast highlighting.

## 3. Synchronized Scroll Interaction
- Selecting any finding card from the bottom findings panel or clicking an inline highlight jumps both panes directly to the corresponding character span.
- Preserves smooth bidirectional scrolling with scroll lock toggle.
