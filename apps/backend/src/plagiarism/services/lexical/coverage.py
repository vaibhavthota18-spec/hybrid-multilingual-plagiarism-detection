"""
Defensible Lexical Coverage Calculator.
Computes non-overlapping union coverage of verified matches across submission tokens.
Guarantees 0.0% <= coverage <= 100.0% and prevents artificial score inflation.
"""

from dataclasses import dataclass

from plagiarism.services.lexical.aligner import AlignedFinding


@dataclass
class SourceCoverageSummary:
    reference_document_id: str
    source_title: str
    matched_passage_count: int
    lexical_coverage_percent: float
    semantic_coverage_percent: float = 0.0


def merge_token_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    Merges overlapping or adjacent half-open token intervals [start, end).
    Returns disjoint list of sorted intervals.
    """
    if not intervals:
        return []

    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged: list[tuple[int, int]] = []

    curr_start, curr_end = sorted_intervals[0]
    for n_start, n_end in sorted_intervals[1:]:
        if n_start <= curr_end:
            curr_end = max(curr_end, n_end)
        else:
            merged.append((curr_start, curr_end))
            curr_start, curr_end = n_start, n_end

    merged.append((curr_start, curr_end))
    return merged


class CoverageCalculator:
    """
    Calculates overall and per-source lexical coverage percentages.
    Overall coverage is based on the union of non-overlapping submission tokens.
    """

    def calculate(
        self,
        total_submission_tokens: int,
        findings: list[AlignedFinding],
    ) -> tuple[float, list[SourceCoverageSummary]]:
        """
        Computes:
        1. Overall lexical coverage percentage (0.0 to 100.0).
        2. Per-source coverage breakdown.
        """
        if total_submission_tokens <= 0 or not findings:
            return 0.0, []

        # 1. Compute overall covered tokens via interval union across all findings
        all_intervals: list[tuple[int, int]] = [
            (f.submission_start_token, f.submission_end_token) for f in findings
        ]
        disjoint_all = merge_token_intervals(all_intervals)

        total_covered_tokens = 0
        for start, end in disjoint_all:
            # Bound interval within [0, total_submission_tokens]
            s = max(0, start)
            e = min(total_submission_tokens, end)
            if e > s:
                total_covered_tokens += (e - s)

        overall_coverage = round(
            min(100.0, max(0.0, (total_covered_tokens / total_submission_tokens) * 100.0)),
            2
        )

        # 2. Compute per-source coverage
        sources_map: dict[str, dict] = {}
        for f in findings:
            ref_id = f.reference_document_id
            if ref_id not in sources_map:
                sources_map[ref_id] = {
                    "title": f.reference_source_title,
                    "findings": [],
                    "intervals": [],
                }
            sources_map[ref_id]["findings"].append(f)
            sources_map[ref_id]["intervals"].append(
                (f.submission_start_token, f.submission_end_token)
            )

        source_summaries: list[SourceCoverageSummary] = []
        for ref_id, data in sources_map.items():
            disjoint_src = merge_token_intervals(data["intervals"])
            src_covered_tokens = 0
            for start, end in disjoint_src:
                s = max(0, start)
                e = min(total_submission_tokens, end)
                if e > s:
                    src_covered_tokens += (e - s)

            src_cov = round(
                min(100.0, max(0.0, (src_covered_tokens / total_submission_tokens) * 100.0)),
                2
            )

            source_summaries.append(
                SourceCoverageSummary(
                    reference_document_id=ref_id,
                    source_title=data["title"],
                    matched_passage_count=len(data["findings"]),
                    lexical_coverage_percent=src_cov,
                    semantic_coverage_percent=0.0,
                )
            )

        # Sort sources descending by coverage
        source_summaries.sort(key=lambda x: x.lexical_coverage_percent, reverse=True)

        return overall_coverage, source_summaries
