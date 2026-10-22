# Dataset Curation, Annotation Schemas & Partition Governance

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Target Execution Phase:** Phase 5 (Multilingual Evaluation)  
> **Date:** October 2026  

---

## 1. Dataset Targets & Architectural Sizing

To ensure statistically valid and empirically reproducible evaluation across English, Hindi, and Telugu, the evaluation suite defines two phased dataset targets:

### 1.1 Pilot Dataset Target (~360 Labeled Pairs)
- **Purpose:** Algorithm validation, unit benchmark testing, and initial threshold calibration during Phase 3 and Phase 4.
- **Composition:** 60 labeled passage pairs for each of the 6 language pairs ($60 \times 6 = 360$ total pairs).

### 1.2 Expanded Production Benchmark Target (~900 Pairs + 90 Long Documents)
- **Purpose:** Comprehensive final evaluation and ablation verification during Phase 5.
- **Composition:**
  - **900 Passage Pairs:** 150 pairs per language relationship across 10 balanced semantic classes.
  - **90 Annotated Long Documents:** Realistic multi-page papers (15 documents per language pair) containing mixed verbatim sections, translated excerpts, legitimate citations, and uncopied text.

---

## 2. Six Language Relationships

The evaluation suite explicitly covers all six language directional pairs:

1. **English – English (EN–EN):** Baseline high-resource validation.
2. **Hindi – Hindi (HI–HI):** Monolingual Devanagari script evaluation.
3. **Telugu – Telugu (TE–TE):** Monolingual Telugu script with agglutinative morphology.
4. **English – Hindi (EN–HI):** Cross-lingual translation between Indo-European languages.
5. **English – Telugu (EN–TE):** Cross-lingual translation across language families (Indo-European $\leftrightarrow$ Dravidian).
6. **Hindi – Telugu (HI–TE):** Cross-lingual Indic translation across distinct language families.

---

## 3. Semantic Case Types & Class Balance

Each language pair split contains a balanced distribution across ten distinct evidentiary cases:

| Case Category | Sub-Category | Expected System Finding | Target Count (Pilot / Expanded) |
|---|---|---|---|
| **Verbatim Copy** | Exact Copy | `EXACT_COPY` | 10 / 25 pairs |
| | Partial Copy (Cut & Paste) | `EXACT_COPY` | 10 / 25 pairs |
| **Near-Verbatim** | Near-Exact Rewrite (Minor edits) | `NEAR_EXACT_REWRITE` | 10 / 20 pairs |
| **Semantic Reuse** | Moderate Paraphrase | `PARAPHRASE` | 10 / 20 pairs |
| | Heavy Paraphrase (Idea reuse) | `PARAPHRASE` | 10 / 20 pairs |
| **Cross-Lingual** | Direct Translation | `POTENTIAL_TRANSLATION` | 10 / 20 pairs |
| | Paraphrased Translation | `POTENTIAL_TRANSLATION` | 10 / 20 pairs |
| **Hard Negatives** | Topically Similar Negatives | No match (Cosine $< 0.80$) | 10 / 20 pairs |
| | Standard Technical Definitions | Low / Boilerplate Flag | 5 / 10 pairs |
| | Properly Formatted Quotes/Citations | Flagged as Excluded | 5 / 10 pairs |

---

## 4. Formal Annotation Schema (JSON Schema Format)

Every annotated benchmark record adheres to the following strict JSON schema (`evaluation/datasets/manifests/`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PlagiarismBenchmarkPair",
  "type": "object",
  "required": [
    "pair_id",
    "source_group_id",
    "language_pair",
    "case_category",
    "submission",
    "reference",
    "ground_truth"
  ],
  "properties": {
    "pair_id": { "type": "string", "format": "uuid" },
    "source_group_id": { "type": "string", "description": "Root document ID to enforce source-grouped partitioning" },
    "language_pair": { "type": "string", "enum": ["EN-EN", "HI-HI", "TE-TE", "EN-HI", "EN-TE", "HI-TE"] },
    "case_category": { 
      "type": "string", 
      "enum": [
        "EXACT_COPY", 
        "PARTIAL_COPY", 
        "NEAR_EXACT_REWRITE", 
        "MODERATE_PARAPHRASE", 
        "HEAVY_PARAPHRASE", 
        "DIRECT_TRANSLATION", 
        "PARAPHRASED_TRANSLATION", 
        "HARD_NEGATIVE_TOPICAL", 
        "STANDARD_DEFINITION", 
        "PROPER_CITATION"
      ] 
    },
    "submission": {
      "type": "object",
      "required": ["text", "language", "start_offset", "end_offset"],
      "properties": {
        "text": { "type": "string" },
        "language": { "type": "string", "enum": ["en", "hi", "te"] },
        "start_offset": { "type": "integer", "minimum": 0 },
        "end_offset": { "type": "integer", "minimum": 0 }
      }
    },
    "reference": {
      "type": "object",
      "required": ["document_id", "title", "text", "language", "start_offset", "end_offset"],
      "properties": {
        "document_id": { "type": "string", "format": "uuid" },
        "title": { "type": "string" },
        "text": { "type": "string" },
        "language": { "type": "string", "enum": ["en", "hi", "te"] },
        "start_offset": { "type": "integer", "minimum": 0 },
        "end_offset": { "type": "integer", "minimum": 0 }
      }
    },
    "ground_truth": {
      "type": "object",
      "required": ["is_plagiarism", "expected_finding_category", "annotator_agreement_score"],
      "properties": {
        "is_plagiarism": { "type": "boolean" },
        "expected_finding_category": { 
          "type": "string", 
          "enum": ["EXACT_COPY", "NEAR_EXACT_REWRITE", "PARAPHRASE", "POTENTIAL_TRANSLATION", "NONE"] 
        },
        "annotator_agreement_score": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
        "notes": { "type": "string" }
      }
    }
  }
}
```

---

## 5. Source-Grouped Partitioning & Held-Out Test Protection

To avoid data leakage, data splitting must NEVER be performed randomly across passage pairs.

### Partitioning Rules (60 / 20 / 20)
1. **Source-Group Invariant:** All passage pairs originating from or referencing the same root source document (`source_group_id`) MUST reside in the same partition:
   - **Development Split (60%):** Algorithm tuning and parameter sweeps.
   - **Validation Split (20%):** Threshold calibrations (e.g., setting cosine similarity cutoffs).
   - **Held-Out Test Split (20%):** Sealed evaluation. Never inspected during development.
2. **Leakage Verification:** An automated script (`scripts/verify_splits.py` in Phase 5) validates that:
   $$\text{Groups}_{\text{dev}} \cap \text{Groups}_{\text{val}} = \emptyset$$
   $$\text{Groups}_{\text{dev}} \cap \text{Groups}_{\text{test}} = \emptyset$$
   $$\text{Groups}_{\text{val}} \cap \text{Groups}_{\text{test}} = \emptyset$$

---

## 6. Annotator Protocol & Quality Control

- **Annotator Qualifications:** Native or bilingual speakers for Indic languages (Hindi, Telugu) with academic background.
- **Multi-Annotator Verification:** Every pair in the test split is independently annotated by 2 annotators.
- **Inter-Annotator Agreement:** Measured via Cohen's Kappa ($\kappa$). Pairs with $\kappa < 0.70$ are reviewed by a senior adjudicator or excluded from the benchmark.
- **Licensing:** All source texts in the public evaluation set must use Open Access licenses (`CC-BY-4.0` or public domain academic repositories).
