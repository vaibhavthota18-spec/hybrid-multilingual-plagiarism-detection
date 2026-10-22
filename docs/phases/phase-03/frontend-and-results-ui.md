# Frontend Architecture & Results Dashboard UI

## 1. UI Components Overview

Phase 3 introduces two major new pages and updates navigation to provide full interactive inspection of plagiarism evidence:

1. **`ResultsDashboardPage.tsx`**:
   - Side-by-side synchronized document inspection panes (Candidate Submission vs. Matched Reference).
   - Real-time Safe Text Highlighting based on exact character code-point offsets.
   - Metrics cards: Overall Lexical Coverage %, Matched Sources Count, Verified Match Findings, Algorithm Specification (Winnowing $k=25, w=16$, BM25Okapi).
   - Interactive Source Breakdown selector cards (clicking a source highlights findings for that reference).
   - Finding Detail Inspector card showing verbatim excerpts, confidence, and exact offsets.

2. **`AnalysisHistoryPage.tsx`**:
   - Filterable, searchable table of prior similarity analyses.
   - Quick-Run Drawer allowing users to configure and launch Direct, One-to-Many, or Corpus analyses with real-time polling progress feedback.
   - Action controls: Inspect results, Delete analysis record.

3. **`IngestionPage.tsx` (Comparison Setup tab)**:
   - Live "Execute Similarity Analysis" action button enabled upon comparison input validation.
   - Launches analysis, polls completion, and automatically routes the user to the Results Dashboard.

---

## 2. Safe Text Highlighting (Zero XSS Vulnerabilities)

A common security vulnerability in plagiarism dashboards is using `dangerouslySetInnerHTML` to inject `<mark>` or `<span>` tags into document text. If an uploaded document contains malicious HTML or script tags (`<script>alert(1)</script>`), injecting innerHTML leads to Cross-Site Scripting (XSS).

### Safe Interval Slicing Implementation:
`ResultsDashboardPage` eliminates `dangerouslySetInnerHTML` entirely. It divides the raw string into disjoint character intervals and renders them as native React elements:

```tsx
function renderHighlightedContent(
  fullText: string,
  spans: HighlightSpan[],
  selectedFindingId: string | null,
  onSpanClick: (findingId: string) => void
): React.ReactNode {
  if (!fullText) return null;
  if (!spans || spans.length === 0) return <span>{fullText}</span>;

  // 1. Sort spans by start offset
  const sorted = [...spans].sort((a, b) => a.start - b.start);
  const elements: React.ReactNode[] = [];
  let cursor = 0;

  sorted.forEach((span, idx) => {
    const s = Math.max(cursor, span.start);
    const e = Math.min(fullText.length, span.end);

    if (s > cursor) {
      // Unmatched plain text segment (React text node)
      elements.push(<span key={`plain-${idx}`}>{fullText.slice(cursor, s)}</span>);
    }

    if (e > s) {
      const isSelected = span.findingId === selectedFindingId;
      const bgClass = isSelected
        ? 'bg-amber-400 text-slate-950 font-semibold ring-2 ring-amber-300'
        : 'bg-amber-500/25 text-amber-200 border-b-2 border-amber-500';

      // Highlighted match rendered as native React <mark> node
      elements.push(
        <mark
          key={`mark-${idx}`}
          onClick={() => onSpanClick(span.findingId)}
          className={`rounded px-1 py-0.5 cursor-pointer transition-all ${bgClass}`}
        >
          {fullText.slice(s, e)}
        </mark>
      );
    }

    cursor = Math.max(cursor, e);
  });

  if (cursor < fullText.length) {
    elements.push(<span key="plain-tail">{fullText.slice(cursor)}</span>);
  }

  return <>{elements}</>;
}
```

Every character is safely escaped by React's standard JSX rendering engine. Malicious script strings are rendered safely as visible plain text.
