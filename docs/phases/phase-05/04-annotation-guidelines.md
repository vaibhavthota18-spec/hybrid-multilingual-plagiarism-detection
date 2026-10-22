# Annotation Guidelines & Ground-Truth Specification

## 1. Ground-Truth Span Annotation Standards

To ensure mathematical precision during localization evaluation, all ground-truth plagiarism spans adhere to strict Unicode offset rules:

1. **0-Indexed Unicode Code Points**: Offsets represent exact character positions (`start_char` to `end_char`) within Python 3 strings, properly indexing multi-byte Devanagari and Telugu grapheme clusters.
2. **Half-Open Intervals `[start, end)`**: The slice `suspicious_text[start_char:end_char]` must return the exact ground truth string with byte-level fidelity.
3. **Punctuation & Whitespace Normalization**: Leading and trailing whitespace is trimmed from annotated spans unless the copied passage explicitly includes sentence-initial indentation.

---

## 2. Plagiarism Annotation Criteria

### 2.1 Verbatim / Exact Copy (`exact`)
- Identical character-for-character sequence.
- Ground truth span covers the entire matched passage.
- Label: `is_plagiarism = True`.

### 2.2 Near-Exact Rewrite (`near_exact`)
- Superficially altered through minor synonym swaps, punctuation changes, or small clause reordering.
- Ground truth span highlights the contiguous region derived from the reference source.
- Label: `is_plagiarism = True`.

### 2.3 Semantic Paraphrase (`paraphrase`)
- Substantial structural reorganization, passive-to-active voice conversion, or conceptual rewording where core propositional content is preserved without attribution.
- Ground truth span marks the entire conceptual passage.
- Label: `is_plagiarism = True`.

### 2.4 Cross-Lingual Translation (`translation`)
- Direct or paraphrase translation of ideas between English, Hindi, and Telugu.
- Ground truth span covers the entire translated sentence or paragraph.
- Label: `is_plagiarism = True`.

### 2.5 Hard Negative (`hard_negative`)
- Sentences that share domain vocabulary, entity names, or sentence structures but convey **contrary or distinct propositions**.
- Examples: Negation shifts ("prohibited" vs. "permitted"), numerical changes ("increased 8%" vs. "contracted 2%"), or contrasting architectures (Relational ACID vs. NoSQL Eventual Consistency).
- Ground truth span: `[]` (empty list).
- Label: `is_plagiarism = False`.

### 2.6 Unrelated Control (`unrelated_control`)
- Passages from completely disjoint domains (e.g., Supersonic aerodynamics vs. Classical Sanskrit literature).
- Ground truth span: `[]`.
- Label: `is_plagiarism = False`.

---

## 3. Automated Validation

Every example in `benchmark_dataset_v1.json` is validated by `validate_example_spans()` in `dataset_loader.py`. If a span offset differs by even a single character or punctuation mark, the loader rejects the dataset with a `DatasetValidationError`.
