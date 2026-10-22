# Phase 6 Handoff & Implementation Roadmap

## 1. Overview of Phase 6 Scope

**Phase 6 Milestone**: *Advanced User Experience, Explainable Reporting, and Reviewer Workflows*.

With the algorithmic foundations (Phase 3 & 4) and scientific evaluation (Phase 5) complete and verified, Phase 6 focuses on transforming the raw detection evidence into an intuitive, explainable, and interactive human-in-the-loop review application.

---

## 2. Key Insights Transferred from Phase 5 to Phase 6

1. **Explainable Dual Evidence Display**:
   - The UI must clearly differentiate between **Lexical Evidence** (verbatim copy-paste, exact token highlight) and **Semantic Evidence** (paraphrase or cross-lingual translation).
   - In Phase 5, semantic detection achieved 100% recall on paraphrases, but users need visual explanations to understand *why* two structurally different sentences were flagged.
2. **Reviewer Caution Badges for Known Failure Modes**:
   - Phase 5 identified two primary false-positive triggers: **Negation Shifts** and **Numerical Changes**.
   - Phase 6 UI should surface a *"Reviewer Caution: Verify Polarity / Dates"* pill whenever high cosine similarity matches sentences with contrasting negation or numbers.
3. **Interactive Side-by-Side Dual Pane**:
   - The Phase 3/4 results dashboard provides synchronized scrolling. Phase 6 should enhance this with inline sentence alignment, diff highlighting, and translation overlays.
4. **Exportable Audit Reports**:
   - Academic institutions and editorial boards require downloadable PDF/HTML summary reports containing overall similarity scores, finding breakdowns, matched excerpts, and reviewer annotations.
5. **Human Override & Annotation Workflows**:
   - Enable reviewers to mark individual findings as *"Verified Plagiarism"*, *"Permitted Citation / Quote"*, or *"Dismissed False Positive"*, recomputing the adjusted net score dynamically.

---

## 3. Strict Boundary Reminder

Phase 6 work must **NOT** begin until the user explicitly requests Phase 6 execution via the Phase 6 master implementation prompt. All current Phase 5 deliverables are frozen and verified.
