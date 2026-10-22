# Module Contracts & Canonical Data Interfaces

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Overview & Canonical Offset Invariant

A central vulnerability in multilingual document analysis systems is **character offset drift**. When documents contain multi-byte Unicode sequences—such as Indic vowels, conjunct consonants (aksharas in Hindi/Telugu), zero-width joiners, and emoji—different runtimes measure text boundaries differently:
- **C/Python byte offsets:** Count raw UTF-8 bytes (1 to 4 bytes per character).
- **JavaScript `string.length` / DOM Range:** Counts 16-bit code units (UTF-16), where surrogate pairs occupy 2 units.
- **Python `str` indexing:** Counts Unicode code points (scalar values).

### Mandatory Canonical Invariant
All backend services, database records, background worker payloads, and REST API responses MUST represent text spans using:
$$\mathbf{Span} = [\text{start\_offset}, \text{end\_offset})$$
where:
1. **Zero-Based:** The first character of the document is index `0`.
2. **Half-Open Interval:** `start_offset` is inclusive; `end_offset` is exclusive. The length in code points is $\Delta = \text{end\_offset} - \text{start\_offset}$.
3. **Unicode Code Points:** Offsets index directly into the canonical raw extracted string $T_{\text{orig}}$ before tokenization, lemmatization, or whitespace stripping.
4. **Invariant:** For any passage or finding span, the exact sliced text is guaranteed to equal $T_{\text{orig}}[\text{start\_offset} : \text{end\_offset}]$.

### Frontend UTF-16 Conversion Rule
When the React frontend highlights text inside the browser DOM, it must project code points to UTF-16 units using this formal mapping algorithm:
```typescript
/**
 * Maps Unicode code-point offsets to JavaScript UTF-16 character indices.
 * @param text The raw extracted text string.
 * @param codePointOffset The zero-based Unicode code-point index.
 * @returns The zero-based UTF-16 string index for string.slice() or DOM Range.
 */
export function codePointToUtf16Offset(text: string, codePointOffset: number): number {
  let currentCodePoint = 0;
  let utf16Index = 0;
  for (const char of text) { // iterating with 'for..of' traverses Unicode code points
    if (currentCodePoint === codePointOffset) {
      return utf16Index;
    }
    utf16Index += char.length; // 1 for BMP, 2 for astral surrogate pairs
    currentCodePoint += 1;
  }
  return utf16Index;
}
```

---

## 2. Core Typed Data Contracts (Python / Pydantic Definitions)

### 2.1 `ExtractedDocument`
Represents the un-normalized raw text and layout structure extracted from a file.
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class PageBoundary(BaseModel):
    page_number: int = Field(ge=1, description="1-based page number")
    start_offset: int = Field(ge=0, description="Start code-point offset of page")
    end_offset: int = Field(ge=0, description="End code-point offset of page")

class ExtractedDocument(BaseModel):
    document_id: UUID
    filename: str
    mime_type: str
    sha256_hash: str = Field(min_length=64, max_length=64)
    raw_text: str = Field(description="Unmodified extracted text string")
    char_count: int = Field(ge=0, description="Length in Unicode code points")
    page_count: int = Field(ge=1)
    page_boundaries: List[PageBoundary]
    detected_language: Optional[str] = Field(default=None, description="ISO-639 code")
    extraction_warnings: List[str] = Field(default_factory=list)
```

### 2.2 `NormalizedDocument`
Represents text standardized for indexing along with bidirectional index projection.
```python
class NormalizedDocument(BaseModel):
    document_id: UUID
    normalized_text: str
    # Map index in normalized_text to index in original raw_text
    norm_to_orig_map: List[int]
    total_normalized_chars: int
```

### 2.3 `Passage`
A discrete contextual window extracted from a document.
```python
class Passage(BaseModel):
    passage_id: UUID
    document_id: UUID
    sequence_index: int = Field(ge=0)
    start_offset: int = Field(ge=0, description="Canonical start code point in raw_text")
    end_offset: int = Field(ge=0, description="Canonical end code point in raw_text")
    text_content: str
    token_count: int = Field(ge=1)
    page_number: int = Field(ge=1)
    language: str = Field(min_length=2, max_length=3)
```

### 2.4 `Fingerprint`
A Winnowing hash value anchoring an exact verbatim span.
```python
class Fingerprint(BaseModel):
    fingerprint_id: Optional[UUID] = None
    hash_value: int = Field(description="64-bit integer hash")
    passage_id: UUID
    document_id: UUID
    collection_id: Optional[UUID] = None
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
```

### 2.5 `EmbeddingRecord`
Dense vector representation for semantic search.
```python
class EmbeddingRecord(BaseModel):
    embedding_id: Optional[UUID] = None
    passage_id: UUID
    document_id: UUID
    collection_id: Optional[UUID] = None
    model_identifier: str = "intfloat/multilingual-e5-base"
    model_revision: str = "main"
    dimensions: int = 768
    vector_values: List[float] = Field(min_length=768, max_length=768)
```

### 2.6 `RetrievalCandidate`
A reference passage retrieved during Stage 1 coarse search.
```python
from enum import Enum

class RetrievalChannel(str, Enum):
    LEXICAL_WINNOWING = "lexical_winnowing"
    LEXICAL_BM25 = "lexical_bm25"
    SEMANTIC_VECTOR = "semantic_vector"
    HYBRID = "hybrid"

class RetrievalCandidate(BaseModel):
    submission_passage_id: UUID
    reference_passage_id: UUID
    reference_document_id: UUID
    channel: RetrievalChannel
    lexical_score: Optional[float] = None
    semantic_score: Optional[float] = None
    combined_score: float
```

### 2.7 `AlignmentResult`
Granular sequence alignment output from token-level local alignment.
```python
class AlignmentResult(BaseModel):
    submission_start_offset: int
    submission_end_offset: int
    reference_start_offset: int
    reference_end_offset: int
    matched_tokens: int
    edit_distance: int
    token_overlap_ratio: float = Field(ge=0.0, le=1.0)
```

### 2.8 `MatchEvidence` & `SimilarityFinding`
The formal verified finding produced by Stage 2 verification and Stage 3 reporting. Adheres to the **Three-Tier Policy**:
- **Long Verbatim ($\ge 10$ tokens):** Classified as `EXACT_COPY` with `ConfidenceLevel.HIGH`.
- **Short Verbatim (6–9 tokens):** Classified as `EXACT_COPY` with `ConfidenceLevel.LOW` and annotated with `"Short or Common-Text Overlap"` in `evidence_notes` (unless clustered).
- **Near-Exact Rewrite ($\ge 10$ tokens):** `NEAR_EXACT_REWRITE` with `HIGH` or `MODERATE` confidence.
- **Paraphrase / Translation ($\ge 12$ tokens):** `PARAPHRASE` or `POTENTIAL_TRANSLATION` with `MODERATE` confidence, meeting language-pair calibrated cutoffs.
```python
class MatchCategory(str, Enum):
    EXACT_COPY = "exact_copy"
    NEAR_EXACT_REWRITE = "near_exact_rewrite"
    PARAPHRASE = "paraphrase"
    POTENTIAL_TRANSLATION = "potential_translation"

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"

class SimilarityFinding(BaseModel):
    finding_id: UUID
    analysis_id: UUID
    submission_document_id: UUID
    reference_document_id: UUID
    source_title: str
    source_author: Optional[str] = None
    category: MatchCategory
    confidence: ConfidenceLevel
    evidence_notes: Optional[str] = Field(default=None, description="e.g., 'Short or Common-Text Overlap' for 6-9 token matches")
    submission_start_offset: int
    submission_end_offset: int
    submission_text_excerpt: str
    reference_start_offset: int
    reference_end_offset: int
    reference_text_excerpt: str
    reference_page_number: int
    lexical_similarity: float = Field(ge=0.0, le=1.0)
    semantic_similarity: float = Field(ge=0.0, le=1.0)
    is_quoted: bool = False
    is_in_bibliography: bool = False
    is_excluded: bool = False
```

### 2.9 `AnalysisResult`
The aggregate results payload returned to the client and rendered in PDF reports.
```python
class SourceCoverageSummary(BaseModel):
    reference_document_id: UUID
    source_title: str
    matched_passage_count: int
    lexical_coverage_percent: float
    semantic_coverage_percent: float

class AnalysisResult(BaseModel):
    analysis_id: UUID
    submission_document_id: UUID
    comparison_mode: str  # direct | one_to_many | corpus
    status: str           # queued | processing | completed | failed | cancelled
    eligible_code_points: int
    overall_lexical_coverage_percent: float
    overall_semantic_coverage_percent: float
    net_adjusted_score_percent: float
    total_findings_count: int
    findings: List[SimilarityFinding]
    source_breakdown: List[SourceCoverageSummary]
    created_at: str
    completed_at: Optional[str] = None
```

### 2.10 `SourceManifest`
Provenance and license declaration for reference corpus documents.
```python
class SourceManifest(BaseModel):
    document_id: UUID
    collection_id: UUID
    title: str
    author: Optional[str] = None
    publication_year: Optional[int] = None
    license: str = Field(description="e.g., CC-BY-4.0, Institutional-Internal")
    provenance_uri: Optional[str] = None
    checksum_sha256: str
    indexed_passages_count: int
    indexed_at: str
```
