"""
Hybrid Plagiarism Detection Engine.
Unifies Lexical Analysis (Winnowing + BM25 + Exact Alignment) with
Semantic AI (Multilingual E5 + Dense Vector Index + Cross-Lingual Alignment).
Handles deduplication, separate metric reporting, and non-overlapping hybrid coverage.
"""

import logging
from dataclasses import dataclass
from typing import Any

from plagiarism.core.config import get_settings
from plagiarism.core.errors import BadRequestError, NotFoundError
from plagiarism.services.lexical.aligner import AlignedFinding, PassageAligner
from plagiarism.services.lexical.bm25 import BM25Index
from plagiarism.services.lexical.coverage import (
    CoverageCalculator,
    SourceCoverageSummary,
    merge_token_intervals,
)
from plagiarism.services.lexical.tokenizer import LexicalToken, LexicalTokenizer
from plagiarism.services.lexical.winnowing import WinnowingEngine
from plagiarism.services.semantic.matcher import SemanticFinding, SemanticMatcher
from plagiarism.storage.local_db import LocalMetadataRepository, get_local_repo

logger = logging.getLogger(__name__)


@dataclass
class HybridFinding:
    finding_id: str
    submission_document_id: str
    reference_document_id: str
    reference_source_title: str
    category: str  # 'exact_copy', 'near_exact_rewrite', 'paraphrase', 'potential_translation'
    confidence: str  # 'high', 'moderate', 'low'
    submission_start_offset: int
    submission_end_offset: int
    submission_excerpt: str
    reference_start_offset: int
    reference_end_offset: int
    reference_excerpt: str
    reference_page_number: int
    matched_token_count: int
    lexical_similarity: float
    semantic_similarity: float
    is_quoted: bool
    is_excluded: bool
    language_pair: str | None = None
    model_name: str | None = None


class HybridAnalysisService:
    """
    Orchestrates multi-modal plagiarism analysis supporting:
    - 'lexical': Purely Winnowing, BM25, exact/near-exact alignment.
    - 'semantic': Purely dense vector embeddings and semantic passage retrieval.
    - 'hybrid': Unified pipeline with non-duplicating evidence integration.
    """

    def __init__(
        self,
        repo: LocalMetadataRepository | None = None,
        tokenizer: LexicalTokenizer | None = None,
        winnowing: WinnowingEngine | None = None,
        aligner: PassageAligner | None = None,
        coverage_calc: CoverageCalculator | None = None,
        semantic_matcher: SemanticMatcher | None = None,
    ):
        self.repo = repo or get_local_repo()
        self.tokenizer = tokenizer or LexicalTokenizer()
        self.winnowing = winnowing or WinnowingEngine(k=25, w=16)
        self.aligner = aligner or PassageAligner(min_token_match=8, min_char_length=25)
        self.coverage_calc = coverage_calc or CoverageCalculator()
        self.semantic_matcher = semantic_matcher or SemanticMatcher(repo=self.repo)
        self.settings = get_settings()

    def run_analysis(
        self,
        analysis_id: str,
        owner_user_id: str,
        submission_document_id: str,
        mode: str,
        detection_mode: str = "hybrid",
        reference_document_id: str | None = None,
        reference_document_ids: list[str] | None = None,
        collection_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Executes end-to-end plagiarism analysis synchronously.
        """
        try:
            # 1. Load submission document
            self.repo.update_analysis_status(
                analysis_id, status="processing", progress_percent=10, current_step="loading_submission"
            )
            sub_doc = self.repo.get_document(submission_document_id)
            if not sub_doc:
                raise NotFoundError(f"Submission document {submission_document_id} not found")
            if sub_doc["status"] != "completed":
                raise BadRequestError(f"Submission document is in {sub_doc['status']} status; must be 'completed'")

            sub_raw_text = sub_doc.get("raw_text", "")
            sub_lang = sub_doc.get("detected_language", "en")
            sub_tokens = self.tokenizer.tokenize(sub_raw_text)

            # 2. Resolve Candidate Reference Documents
            self.repo.update_analysis_status(
                analysis_id, status="processing", progress_percent=20, current_step="resolving_candidates"
            )
            candidate_docs: list[dict[str, Any]] = []

            if mode == "direct":
                if not reference_document_id:
                    raise BadRequestError("Direct comparison mode requires 'reference_document_id'")
                ref = self.repo.get_document(reference_document_id)
                if not ref:
                    raise NotFoundError(f"Reference document {reference_document_id} not found")
                if ref["status"] != "completed":
                    raise BadRequestError(f"Reference document is in '{ref['status']}' status")
                candidate_docs.append(ref)

            elif mode == "one_to_many":
                ref_ids = reference_document_ids or []
                if not ref_ids:
                    raise BadRequestError("One-to-many mode requires 'reference_document_ids'")
                for rid in ref_ids:
                    if rid == submission_document_id:
                        continue
                    ref = self.repo.get_document(rid)
                    if ref and ref["status"] == "completed":
                        candidate_docs.append(ref)
                if not candidate_docs:
                    raise BadRequestError("No completed reference documents available for comparison")

            elif mode == "corpus":
                if not collection_id:
                    raise BadRequestError("Corpus mode requires 'collection_id'")
                col = self.repo.get_collection(collection_id)
                if not col:
                    raise NotFoundError(f"Collection {collection_id} not found")
                col_members = self.repo.list_collection_documents(collection_id)
                for mem in col_members:
                    if mem["document_id"] == submission_document_id:
                        continue
                    if mem["status"] == "completed":
                        candidate_docs.append(mem)
                if not candidate_docs:
                    raise BadRequestError(f"Collection {collection_id} contains no eligible completed documents")

            else:
                raise BadRequestError(f"Unknown comparison mode '{mode}'")

            # 3. Candidate Metadata & Execution Dispatch
            run_lexical = detection_mode in ("lexical", "hybrid")
            run_semantic = detection_mode in ("semantic", "hybrid")

            lexical_findings: list[AlignedFinding] = []
            semantic_findings: list[SemanticFinding] = []
            bm25_score_map = {}
            shared_fp_counts = {}

            # Execute Lexical Pipeline if active
            if run_lexical:
                self.repo.update_analysis_status(
                    analysis_id, status="processing", progress_percent=35, current_step="lexical_matching"
                )
                # Fingerprint submission document if not already indexed
                sub_fps = self.repo.get_fingerprints(submission_document_id)
                if not sub_fps:
                    generated_fps = self.winnowing.fingerprint_tokens(sub_tokens)
                    self.repo.save_fingerprints(
                        submission_document_id, generated_fps, self.winnowing.algorithm_version
                    )

                bm25 = BM25Index(k1=1.2, b=0.75)
                ref_tokens_cache: dict[str, list[LexicalToken]] = {}
                candidate_ids = [c["document_id"] for c in candidate_docs]

                for c in candidate_docs:
                    c_id = c["document_id"]
                    c_raw = c.get("raw_text", "")
                    c_toks = self.tokenizer.tokenize(c_raw)
                    ref_tokens_cache[c_id] = c_toks
                    bm25.add_document(c_id, [t.norm_text for t in c_toks])

                    # Ensure reference fingerprints exist
                    c_fps = self.repo.get_fingerprints(c_id)
                    if not c_fps:
                        c_gen_fps = self.winnowing.fingerprint_tokens(c_toks)
                        self.repo.save_fingerprints(c_id, c_gen_fps, self.winnowing.algorithm_version)

                sub_norm_tokens = [t.norm_text for t in sub_tokens]
                bm25_rankings = bm25.rank_candidates(sub_norm_tokens, candidate_ids, top_k=len(candidate_ids))
                bm25_score_map = dict(bm25_rankings)

                shared_fps = self.repo.find_shared_fingerprints(submission_document_id, candidate_ids)
                for sfp in shared_fps:
                    r_id = sfp["reference_document_id"]
                    shared_fp_counts[r_id] = shared_fp_counts.get(r_id, 0) + 1

                for c in candidate_docs:
                    c_id = c["document_id"]
                    c_title = c.get("title") or c.get("filename") or "Reference Document"
                    c_raw = c.get("raw_text", "")
                    c_toks = ref_tokens_cache[c_id]

                    findings = self.aligner.align_documents(
                        submission_id=submission_document_id,
                        submission_raw_text=sub_raw_text,
                        submission_tokens=sub_tokens,
                        reference_id=c_id,
                        reference_title=c_title,
                        reference_raw_text=c_raw,
                        reference_tokens=c_toks,
                    )
                    lexical_findings.extend(findings)

            # Execute Semantic Pipeline if active
            if run_semantic:
                self.repo.update_analysis_status(
                    analysis_id, status="processing", progress_percent=60, current_step="semantic_matching"
                )
                semantic_findings = self.semantic_matcher.match_documents(
                    submission_document_id=submission_document_id,
                    submission_text=sub_raw_text,
                    submission_lang=sub_lang,
                    candidate_docs=candidate_docs,
                    top_k=5,
                )

            # 4. Evidence Integration & Deduplication
            self.repo.update_analysis_status(
                analysis_id, status="processing", progress_percent=80, current_step="integrating_evidence"
            )

            final_findings, overall_lexical_cov, overall_semantic_cov, hybrid_cov, net_score, sources = (
                self._integrate_and_score(
                    sub_tokens=sub_tokens,
                    sub_raw_text=sub_raw_text,
                    lexical_findings=lexical_findings,
                    semantic_findings=semantic_findings,
                    candidate_docs=candidate_docs,
                    detection_mode=detection_mode,
                )
            )

            # 5. Candidate metadata
            model_info = self.semantic_matcher.provider.get_model_info() if run_semantic else {}
            candidate_metadata = {
                "total_candidates_evaluated": len(candidate_docs),
                "detection_mode": detection_mode,
                "bm25_scores": bm25_score_map,
                "shared_fingerprint_counts": shared_fp_counts,
                "model_info": model_info,
            }

            # 6. Save results to persistent repository
            self.repo.update_analysis_status(
                analysis_id, status="processing", progress_percent=95, current_step="saving_results"
            )
            self.repo.save_analysis_results(
                analysis_id=analysis_id,
                overall_lexical_cov=overall_lexical_cov,
                findings=final_findings,
                sources=sources,
                candidate_metadata=candidate_metadata,
                overall_semantic_cov=overall_semantic_cov,
                net_adjusted_score=net_score,
                hybrid_evidence_cov=hybrid_cov,
            )

            return self.repo.get_analysis(analysis_id)

        except Exception as e:
            logger.exception("Error executing %s analysis %s: %s", detection_mode, analysis_id, str(e))
            self.repo.update_analysis_status(
                analysis_id,
                status="failed",
                progress_percent=0,
                current_step="failed",
                error_code="ANALYSIS_EXECUTION_ERROR",
                error_message=str(e),
            )
            raise

    def _integrate_and_score(
        self,
        sub_tokens: list[LexicalToken],
        sub_raw_text: str,
        lexical_findings: list[AlignedFinding],
        semantic_findings: list[SemanticFinding],
        candidate_docs: list[dict[str, Any]],
        detection_mode: str,
    ) -> tuple[list[HybridFinding], float, float, float, float, list[SourceCoverageSummary]]:
        """
        Deduplicates overlapping spans, computes separate metrics, and builds per-source summaries.
        """
        total_tokens = len(sub_tokens)
        final_findings: list[HybridFinding] = []

        # Map character offsets to token intervals
        def char_offsets_to_token_interval(start_char: int, end_char: int) -> tuple[int, int]:
            matched_toks = [
                t.index for t in sub_tokens
                if t.start_char >= start_char and t.end_char <= end_char
            ]
            if not matched_toks:
                # Approximate nearest token
                for t in sub_tokens:
                    if t.start_char <= start_char < t.end_char or t.start_char < end_char <= t.end_char:
                        matched_toks.append(t.index)
            if not matched_toks:
                return (0, 0)
            return (min(matched_toks), max(matched_toks) + 1)

        # 1. Process Lexical findings
        lexical_intervals: list[tuple[int, int]] = []
        for lf in lexical_findings:
            lexical_intervals.append((lf.submission_start_token, lf.submission_end_token))
            final_findings.append(
                HybridFinding(
                    finding_id=lf.finding_id,
                    submission_document_id=lf.submission_document_id,
                    reference_document_id=lf.reference_document_id,
                    reference_source_title=lf.reference_source_title,
                    category=lf.category,
                    confidence=lf.confidence,
                    submission_start_offset=lf.submission_start_offset,
                    submission_end_offset=lf.submission_end_offset,
                    submission_excerpt=lf.submission_excerpt,
                    reference_start_offset=lf.reference_start_offset,
                    reference_end_offset=lf.reference_end_offset,
                    reference_excerpt=lf.reference_excerpt,
                    reference_page_number=getattr(lf, "reference_page_number", 1) or 1,
                    matched_token_count=lf.matched_token_count,
                    lexical_similarity=lf.lexical_similarity,
                    semantic_similarity=0.0,
                    is_quoted=lf.is_quoted,
                    is_excluded=lf.is_excluded,
                )
            )

        # 2. Process and Deduplicate Semantic findings
        semantic_intervals: list[tuple[int, int]] = []
        for sf in semantic_findings:
            tok_s, tok_e = char_offsets_to_token_interval(
                sf.submission_start_offset, sf.submission_end_offset
            )
            if tok_e > tok_s:
                semantic_intervals.append((tok_s, tok_e))

            # Deduplication: Check if there is an existing lexical finding covering this exact span and source
            duplicate_lex = False
            for lf in final_findings:
                if lf.reference_document_id == sf.reference_document_id:
                    # Check overlap ratio
                    overlap_s = max(lf.submission_start_offset, sf.submission_start_offset)
                    overlap_e = min(lf.submission_end_offset, sf.submission_end_offset)
                    if overlap_e > overlap_s:
                        overlap_len = overlap_e - overlap_s
                        lex_len = lf.submission_end_offset - lf.submission_start_offset
                        if lex_len > 0 and (overlap_len / lex_len) >= 0.70:
                            # Attach semantic score to the lexical finding rather than duplicating the row
                            lf.semantic_similarity = sf.semantic_similarity
                            lf.language_pair = sf.language_pair
                            lf.model_name = sf.model_name
                            duplicate_lex = True
                            break

            if not duplicate_lex:
                final_findings.append(
                    HybridFinding(
                        finding_id=sf.finding_id,
                        submission_document_id=sf.submission_document_id,
                        reference_document_id=sf.reference_document_id,
                        reference_source_title=sf.reference_source_title,
                        category=sf.category,
                        confidence=sf.confidence,
                        submission_start_offset=sf.submission_start_offset,
                        submission_end_offset=sf.submission_end_offset,
                        submission_excerpt=sf.submission_excerpt,
                        reference_start_offset=sf.reference_start_offset,
                        reference_end_offset=sf.reference_end_offset,
                        reference_excerpt=sf.reference_excerpt,
                        reference_page_number=sf.reference_page_number,
                        matched_token_count=sf.matched_token_count,
                        lexical_similarity=0.0,
                        semantic_similarity=sf.semantic_similarity,
                        is_quoted=sf.is_quoted,
                        is_excluded=sf.is_excluded,
                        language_pair=sf.language_pair,
                        model_name=sf.model_name,
                    )
                )

        # 3. Calculate separate non-overlapping coverage metrics
        def interval_coverage(intervals: list[tuple[int, int]]) -> float:
            if not intervals or total_tokens <= 0:
                return 0.0
            disjoint = merge_token_intervals(intervals)
            covered = sum(min(total_tokens, e) - max(0, s) for s, e in disjoint if e > s)
            return round(min(100.0, max(0.0, (covered / total_tokens) * 100.0)), 2)

        overall_lexical_cov = interval_coverage(lexical_intervals)
        overall_semantic_cov = interval_coverage(semantic_intervals)

        # Hybrid coverage is the union of ALL unique matched token intervals
        hybrid_intervals = lexical_intervals + semantic_intervals
        hybrid_cov = interval_coverage(hybrid_intervals)

        # Net adjusted score formulation (ADR-0003):
        # In lexical-only mode: net_score = lexical_cov
        # In semantic-only mode: net_score = semantic_cov
        # In hybrid mode: net_score = 0.40 * lexical_cov + 0.60 * semantic_cov (bounded by hybrid_cov)
        if detection_mode == "lexical":
            net_score = overall_lexical_cov
        elif detection_mode == "semantic":
            net_score = overall_semantic_cov
        else:
            net_score = round(min(100.0, 0.40 * overall_lexical_cov + 0.60 * overall_semantic_cov), 2)

        # 4. Build per-source coverage breakdowns
        sources_map: dict[str, dict[str, Any]] = {}
        for c in candidate_docs:
            cid = c["document_id"]
            title = c.get("title") or c.get("filename") or "Reference Document"
            sources_map[cid] = {
                "title": title,
                "lexical_intervals": [],
                "semantic_intervals": [],
                "matched_count": 0,
            }

        for f in final_findings:
            rid = f.reference_document_id
            if rid in sources_map:
                sources_map[rid]["matched_count"] += 1
                tok_s, tok_e = char_offsets_to_token_interval(
                    f.submission_start_offset, f.submission_end_offset
                )
                if tok_e > tok_s:
                    if f.lexical_similarity > 0.0 or f.category in ("exact_copy", "near_exact_rewrite"):
                        sources_map[rid]["lexical_intervals"].append((tok_s, tok_e))
                    if f.semantic_similarity > 0.0 or f.category in ("paraphrase", "potential_translation"):
                        sources_map[rid]["semantic_intervals"].append((tok_s, tok_e))

        source_summaries: list[SourceCoverageSummary] = []
        for rid, sdata in sources_map.items():
            if sdata["matched_count"] > 0:
                s_lex_cov = interval_coverage(sdata["lexical_intervals"])
                s_sem_cov = interval_coverage(sdata["semantic_intervals"])
                source_summaries.append(
                    SourceCoverageSummary(
                        reference_document_id=rid,
                        source_title=sdata["title"],
                        matched_passage_count=sdata["matched_count"],
                        lexical_coverage_percent=s_lex_cov,
                        semantic_coverage_percent=s_sem_cov,
                    )
                )

        # Sort sources descending by max coverage
        source_summaries.sort(
            key=lambda x: max(x.lexical_coverage_percent, x.semantic_coverage_percent),
            reverse=True,
        )

        # Sort findings deterministically by submission offset
        final_findings.sort(key=lambda x: (x.submission_start_offset, x.submission_end_offset))

        return final_findings, overall_lexical_cov, overall_semantic_cov, hybrid_cov, net_score, source_summaries

    def recompute_reviewer_adjusted_coverage(self, analysis_id: str) -> dict[str, Any]:
        """
        Recomputes reviewer-adjusted evidence coverage after review decisions change.
        Mathematical Invariant:
        - Original detector scores are preserved intact.
        - Findings marked 'exclude' or 'quoted_cited' are omitted from active intervals.
        - Active findings are mapped to token intervals on the submission document.
        - Non-overlapping union coverage is computed as:
            (covered_tokens / total_tokens) * 100.0
        """
        analysis = self.repo.get_analysis(analysis_id)
        if not analysis:
            raise NotFoundError(f"Analysis {analysis_id} not found")

        sub_doc = self.repo.get_document(analysis["submission_document_id"])
        if not sub_doc:
            raise NotFoundError(f"Submission document {analysis['submission_document_id']} not found")

        sub_raw_text = sub_doc.get("raw_text", "")
        sub_tokens = self.tokenizer.tokenize(sub_raw_text)
        total_tokens = len(sub_tokens)

        findings = self.repo.get_analysis_findings(analysis_id)
        active_intervals: list[tuple[int, int]] = []

        status_counts = {
            "total": len(findings),
            "unreviewed": 0,
            "keep": 0,
            "exclude": 0,
            "quoted_cited": 0,
            "needs_review": 0,
        }

        for f in findings:
            dec = f.get("review_decision") or "unreviewed"
            status_counts[dec] = status_counts.get(dec, 0) + 1

            # Exclude if explicitly excluded or marked as quoted/cited
            if dec in ("exclude", "quoted_cited") or f.get("is_excluded") or f.get("is_quoted"):
                continue

            # Convert character offsets to token interval
            s_char = f["submission_start_offset"]
            e_char = f["submission_end_offset"]
            matched_toks = [
                t.index for t in sub_tokens
                if t.start_char >= s_char and t.end_char <= e_char
            ]
            if not matched_toks:
                for t in sub_tokens:
                    if t.start_char <= s_char < t.end_char or t.start_char < e_char <= t.end_char:
                        matched_toks.append(t.index)
            if matched_toks:
                active_intervals.append((min(matched_toks), max(matched_toks) + 1))

        if not active_intervals or total_tokens <= 0:
            adjusted_coverage = 0.0
        else:
            disjoint = merge_token_intervals(active_intervals)
            covered = sum(min(total_tokens, e) - max(0, s) for s, e in disjoint if e > s)
            adjusted_coverage = round(min(100.0, max(0.0, (covered / total_tokens) * 100.0)), 2)

        reviewed_count = len(findings) - status_counts["unreviewed"]
        self.repo.update_analysis_review_summary(
            analysis_id=analysis_id,
            reviewer_adjusted_coverage_percent=adjusted_coverage,
            reviewed_findings_count=reviewed_count,
        )

        return {
            "analysis_id": analysis_id,
            "original_evidence_coverage_percent": analysis.get("hybrid_evidence_coverage_percent", 0.0),
            "reviewer_adjusted_coverage_percent": adjusted_coverage,
            "reviewed_findings_count": reviewed_count,
            "total_findings_count": len(findings),
            "status_counts": status_counts,
        }


_hybrid_service: HybridAnalysisService | None = None


def get_hybrid_service() -> HybridAnalysisService:
    global _hybrid_service
    if _hybrid_service is None:
        _hybrid_service = HybridAnalysisService()
    return _hybrid_service
