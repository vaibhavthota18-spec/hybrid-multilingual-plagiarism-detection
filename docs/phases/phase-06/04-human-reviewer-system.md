# Phase 6 — Human Reviewer System & Dynamic Union Recalculation

## 1. Motivation
Automated plagiarism detectors identify mathematical similarities, but human academic reviewers determine whether a matched passage constitutes legitimate scholarly attribution, common domain terminology, or unauthorized duplication.

Phase 6 introduces a full human reviewer workflow with real-time recalculation of adjusted coverage.

## 2. Reviewer Decisions
| Decision | Meaning | Impact on Adjusted Coverage |
| :--- | :--- | :--- |
| `keep` | Confirmed unauthorized match | **Included** in active token union |
| `exclude` | False positive / domain cliché | **Excluded** from active token union |
| `quoted_cited` | Properly attributed quotation | **Excluded** from active token union |
| `needs_review`| Pending committee / instructor review | **Included** in active token union |
| `unreviewed` | Default initial state | **Included** in active token union |

## 3. Mathematical Invariant & Dynamic Union Calculation
A strict mathematical invariant is enforced:
> **The original automated detector score is immutable.** Reviewer interventions never overwrite raw detection metrics (`overall_lexical_coverage_percent` or `overall_hybrid_coverage_percent`).

Instead, the system dynamically recomputes `reviewer_adjusted_coverage_percent`:

$$\text{Coverage}_{\text{adjusted}} = \frac{|\bigcup_{f \in \mathcal{F}_{\text{active}}} [s_f, e_f]|}{N_{\text{total}}} \times 100\%$$

where:
- $\mathcal{F}_{\text{active}} = \{f \in \text{Findings} \mid \text{decision}(f) \notin \{\text{exclude}, \text{quoted\_cited}\}\}$
- $[s_f, e_f]$ is the token index interval of finding $f$ in the submission document.
- Overlapping intervals are merged using deterministic 1D interval union before computing total covered tokens.
- $N_{\text{total}}$ is the total token count of the submission document.

## 4. Notes & Audit Trail
- Each decision can include custom reviewer notes (e.g., *"Excluded: APA 7th ed. citation verified"*).
- Timestamps and reviewer decisions are persisted in the `analysis_findings` and `analyses` SQLite tables.
