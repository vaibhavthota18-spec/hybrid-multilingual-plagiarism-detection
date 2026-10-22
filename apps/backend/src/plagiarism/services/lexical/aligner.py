"""
Detailed Lexical Passage Aligner.
Finds, expands, verifies, and merges exact and near-exact matching spans between
submission and reference documents, generating verified source-linked findings.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
import uuid

from plagiarism.services.lexical.tokenizer import LexicalToken


@dataclass
class AlignedFinding:
    finding_id: str
    submission_document_id: str
    reference_document_id: str
    reference_source_title: str
    category: str                      # 'exact_copy' or 'near_exact_rewrite'
    confidence: str                    # 'high', 'moderate', 'low'
    submission_start_offset: int       # Code point start in submission raw text
    submission_end_offset: int         # Code point end in submission raw text
    submission_start_token: int        # Token index start
    submission_end_token: int          # Token index end (exclusive)
    submission_excerpt: str            # Original text excerpt
    reference_start_offset: int        # Code point start in reference raw text
    reference_end_offset: int          # Code point end in reference raw text
    reference_start_token: int         # Token index start in reference
    reference_end_token: int           # Token index end in reference (exclusive)
    reference_excerpt: str             # Reference original text excerpt
    matched_token_count: int           # Count of matched tokens
    lexical_similarity: float          # Similarity ratio (1.0 for exact, >= 0.85 for near-exact)
    reference_page_number: Optional[int] = 1
    is_quoted: bool = False
    is_excluded: bool = False


class PassageAligner:
    """
    Detailed alignment engine combining fingerprint seed expansion and n-gram anchor chaining.
    """

    def __init__(
        self,
        min_token_match: int = 8,
        min_char_length: int = 25,
        max_merge_gap: int = 4
    ):
        self.min_token_match = min_token_match
        self.min_char_length = min_char_length
        self.max_merge_gap = max_merge_gap

    def align_documents(
        self,
        submission_id: str,
        submission_raw_text: str,
        submission_tokens: List[LexicalToken],
        reference_id: str,
        reference_title: str,
        reference_raw_text: str,
        reference_tokens: List[LexicalToken],
    ) -> List[AlignedFinding]:
        """
        Executes fine-grained alignment between submission and a candidate reference document.
        Returns a deduplicated, non-overlapping list of verified AlignedFinding instances.
        """
        n_sub = len(submission_tokens)
        n_ref = len(reference_tokens)

        if n_sub == 0 or n_ref == 0:
            return []

        # Effective minimum tokens for short documents
        effective_min_tokens = min(self.min_token_match, max(3, min(n_sub, n_ref) // 2))

        # 1. Build an inverted index of small n-grams (seed size 5) on reference document
        seed_size = min(5, effective_min_tokens)
        ref_seeds: Dict[Tuple[str, ...], List[int]] = {}
        for r in range(n_ref - seed_size + 1):
            gram = tuple(t.norm_text for t in reference_tokens[r : r + seed_size])
            ref_seeds.setdefault(gram, []).append(r)

        # 2. Scan submission tokens to discover seed matches and expand
        raw_spans: List[Tuple[int, int, int, int]] = []  # (sub_start, sub_end, ref_start, ref_end)

        s = 0
        while s <= n_sub - seed_size:
            gram = tuple(t.norm_text for t in submission_tokens[s : s + seed_size])
            if gram in ref_seeds:
                # Find the best reference anchor that extends the furthest
                best_sub_start = s
                best_sub_end = s + seed_size
                best_ref_start = ref_seeds[gram][0]
                best_ref_end = best_ref_start + seed_size

                for ref_start in ref_seeds[gram]:
                    # Extend forward while normalized tokens match
                    curr_s = s + seed_size
                    curr_r = ref_start + seed_size
                    while curr_s < n_sub and curr_r < n_ref:
                        if submission_tokens[curr_s].norm_text == reference_tokens[curr_r].norm_text:
                            curr_s += 1
                            curr_r += 1
                        else:
                            break

                    # Extend backward if possible
                    back_s = s
                    back_r = ref_start
                    while back_s > 0 and back_r > 0:
                        if submission_tokens[back_s - 1].norm_text == reference_tokens[back_r - 1].norm_text:
                            back_s -= 1
                            back_r -= 1
                        else:
                            break

                    if (curr_s - back_s) > (best_sub_end - best_sub_start):
                        best_sub_start = back_s
                        best_sub_end = curr_s
                        best_ref_start = back_r
                        best_ref_end = curr_r

                matched_len = best_sub_end - best_sub_start
                if matched_len >= effective_min_tokens:
                    raw_spans.append((best_sub_start, best_sub_end, best_ref_start, best_ref_end))
                    s = max(s + 1, best_sub_end)
                    continue

            s += 1

        if not raw_spans:
            return []

        # 3. Merge adjacent or slightly separated spans (gaps <= max_merge_gap)
        merged_spans = self._merge_adjacent_spans(raw_spans)

        # 4. Construct verified AlignedFinding instances
        findings: List[AlignedFinding] = []
        for (sub_start, sub_end, ref_start, ref_end, is_near_exact) in merged_spans:
            matched_count = sub_end - sub_start

            # Check character offsets and slice raw original text
            sub_c_start = submission_tokens[sub_start].start_char
            sub_c_end = submission_tokens[sub_end - 1].end_char
            ref_c_start = reference_tokens[ref_start].start_char
            ref_c_end = reference_tokens[ref_end - 1].end_char

            char_len = sub_c_end - sub_c_start
            if char_len < self.min_char_length and matched_count < effective_min_tokens:
                continue

            sub_excerpt = submission_raw_text[sub_c_start:sub_c_end]
            ref_excerpt = reference_raw_text[ref_c_start:ref_c_end]

            # Invariant: excerpt must be non-empty
            if not sub_excerpt.strip() or not ref_excerpt.strip():
                continue

            # Confidence determination
            if matched_count >= 25 or char_len >= 120:
                confidence = "high"
            elif matched_count >= 12 or char_len >= 50:
                confidence = "moderate"
            else:
                confidence = "low"

            category = "near_exact_rewrite" if is_near_exact else "exact_copy"
            similarity = 0.90 if is_near_exact else 1.0

            findings.append(
                AlignedFinding(
                    finding_id=str(uuid.uuid4()),
                    submission_document_id=submission_id,
                    reference_document_id=reference_id,
                    reference_source_title=reference_title,
                    category=category,
                    confidence=confidence,
                    submission_start_offset=sub_c_start,
                    submission_end_offset=sub_c_end,
                    submission_start_token=sub_start,
                    submission_end_token=sub_end,
                    submission_excerpt=sub_excerpt,
                    reference_start_offset=ref_c_start,
                    reference_end_offset=ref_c_end,
                    reference_start_token=ref_start,
                    reference_end_token=ref_end,
                    reference_excerpt=ref_excerpt,
                    matched_token_count=matched_count,
                    lexical_similarity=similarity,
                    reference_page_number=1,
                )
            )

        return findings

    def _merge_adjacent_spans(
        self,
        spans: List[Tuple[int, int, int, int]]
    ) -> List[Tuple[int, int, int, int, bool]]:
        """
        Sorts and merges spans that are adjacent or separated by small gaps.
        Returns list of (sub_start, sub_end, ref_start, ref_end, is_near_exact).
        """
        if not spans:
            return []

        # Sort spans by submission start
        spans.sort(key=lambda x: (x[0], x[2]))

        merged: List[Tuple[int, int, int, int, bool]] = []
        curr_sub_start, curr_sub_end, curr_ref_start, curr_ref_end = spans[0]
        has_gap = False

        for next_span in spans[1:]:
            n_sub_start, n_sub_end, n_ref_start, n_ref_end = next_span

            sub_gap = n_sub_start - curr_sub_end
            ref_gap = n_ref_start - curr_ref_end

            # If overlapping or adjacent within tolerance gap
            if 0 <= sub_gap <= self.max_merge_gap and 0 <= ref_gap <= self.max_merge_gap:
                curr_sub_end = max(curr_sub_end, n_sub_end)
                curr_ref_end = max(curr_ref_end, n_ref_end)
                if sub_gap > 0 or ref_gap > 0:
                    has_gap = True
            elif n_sub_start < curr_sub_end:
                # Direct overlap; extend boundaries
                curr_sub_end = max(curr_sub_end, n_sub_end)
                curr_ref_end = max(curr_ref_end, n_ref_end)
            else:
                # Push previous span and start new
                merged.append((curr_sub_start, curr_sub_end, curr_ref_start, curr_ref_end, has_gap))
                curr_sub_start, curr_sub_end, curr_ref_start, curr_ref_end = next_span
                has_gap = False

        merged.append((curr_sub_start, curr_sub_end, curr_ref_start, curr_ref_end, has_gap))
        return merged
