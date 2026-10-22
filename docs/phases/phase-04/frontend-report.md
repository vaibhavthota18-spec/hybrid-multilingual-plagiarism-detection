# Phase 4 Frontend Report: React Dashboard, Mode Selectors, and Visualizations

## 1. User Interface Enhancements Overview

The React 18 + Vite + Tailwind CSS frontend (`apps/web`) was enhanced to present Phase 4 semantic AI detection capabilities seamlessly alongside Phase 3 lexical results.

---

## 2. Component Updates

### A. Detection Mode Selector (`IngestionPage.tsx` & `AnalysisHistoryPage.tsx`)
Interactive card selectors allow users to pick their detection strategy before launching an analysis:
1. **Hybrid AI (Recommended)**: Combines deterministic Winnowing with dense multilingual embeddings for comprehensive plagiarism detection.
2. **Lexical Only (Phase 3)**: Fast, exact and near-exact matching using character winnowing and polynomial rolling hash.
3. **Semantic AI Only (Phase 4)**: Pure dense embedding cosine similarity search for cross-language translations and paraphrasing.

### B. Results Dashboard 5-Metric Suite (`ResultsDashboardPage.tsx`)
Replaces single-metric displays with a 5-card metric row:
- **Composite Hybrid Score**: Primary institutional weighted score ($0.40 \text{ Lex} + 0.60 \text{ Sem}$).
- **Lexical Coverage**: Exact token overlap percentage from Winnowing.
- **Semantic AI Coverage**: Paraphrased and translated passage coverage percentage from Multilingual E5.
- **Matched Sources**: Count of distinct reference documents with detected overlaps.
- **Total Findings**: Aggregate count of identified passage matches.

### C. Active Model Metadata Banner
Displays active model details:
- Model Name (`intfloat/multilingual-e5-small`)
- Embedding Dimensions (`384`)
- Max Sequence Budget (`512 tokens`)
- Inference Hardware (`CPU` / `Native Windows Host`)
- Active Paraphrase Cutoff (`0.82`) & Translation Cutoff (`0.80`)

### D. Category-Specific Text Highlighting & Evidence Inspector
Passages in submission and reference viewers are color-coded:
- **Red (`bg-red-500/20 text-red-300`)**: Exact Copy ($100\%$ verbatim).
- **Amber (`bg-amber-500/20 text-amber-300`)**: Near-Exact Rewrite ($>80\%$ token overlap).
- **Violet (`bg-violet-500/20 text-violet-300`)**: Paraphrase (Semantic Cosine $\ge 0.82$).
- **Cyan (`bg-cyan-500/20 text-cyan-300`)**: Cross-Language Translation (Semantic Cosine $\ge 0.80$, e.g. Hindi $\leftrightarrow$ English, Telugu $\leftrightarrow$ English).

Clicking any highlighted passage activates the Finding Inspector drawer, displaying side-by-side excerpts, character offsets, language pair badges, lexical similarity, and semantic cosine scores.
