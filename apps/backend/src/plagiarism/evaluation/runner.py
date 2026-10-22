"""
Evaluation Runner and Threshold Calibration Engine.
Executes reproducible experiments across Lexical, Semantic, and Hybrid detection modes,
performs calibration sweeps on calibration partitions, tests frozen thresholds on held-out splits,
and generates standardized evaluation reports with error taxonomies.
"""

from datetime import datetime, timezone
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from plagiarism.evaluation.schemas import (
    BootstrapConfidenceInterval,
    ClassificationMetrics,
    ErrorRecord,
    EvaluationDataset,
    EvaluationExample,
    EvaluationReport,
    LocalizationMetrics,
    PlagiarismCategory,
    PredictionResult,
    PredictionSpan,
    RetrievalMetrics,
    SplitPartition,
)
from plagiarism.evaluation.classification_metrics import compute_classification_metrics
from plagiarism.evaluation.retrieval_metrics import compute_retrieval_metrics
from plagiarism.evaluation.localization_metrics import (
    compute_interval_overlap,
    compute_localization_metrics,
    compute_span_iou,
)
from plagiarism.evaluation.statistical import compute_bootstrap_ci
from plagiarism.services.lexical.tokenizer import LexicalTokenizer
from plagiarism.services.lexical.winnowing import WinnowingEngine
from plagiarism.services.lexical.aligner import PassageAligner
from plagiarism.services.lexical.coverage import merge_token_intervals
from plagiarism.services.semantic.provider import get_embedding_provider, SemanticEmbeddingProvider


class EvaluationRunner:
    """
    Modular evaluation test runner operating across detection modes:
    - 'lexical': Winnowing (k=25, w=16), Karp-Rabin alignment, token coverage
    - 'semantic': intfloat/multilingual-e5-small (384-dim), dense cosine search
    - 'hybrid': Deduplicated combination of lexical coverage and semantic similarity
    """

    def __init__(
        self,
        provider: Optional[SemanticEmbeddingProvider] = None,
        tokenizer: Optional[LexicalTokenizer] = None,
        winnowing: Optional[WinnowingEngine] = None,
        aligner: Optional[PassageAligner] = None,
    ):
        self.tokenizer = tokenizer or LexicalTokenizer()
        self.winnowing = winnowing or WinnowingEngine(k=25, w=16)
        self.aligner = aligner or PassageAligner(min_token_match=8, min_char_length=25)
        self.provider = provider or get_embedding_provider()
        self._query_cache: Dict[str, np.ndarray] = {}
        self._passage_cache: Dict[str, np.ndarray] = {}

    def get_query_embedding(self, text: str) -> np.ndarray:
        if text not in self._query_cache:
            self._query_cache[text] = self.provider.encode_queries([text])[0]
        return self._query_cache[text]

    def get_passage_embedding(self, text: str) -> np.ndarray:
        if text not in self._passage_cache:
            self._passage_cache[text] = self.provider.encode_passages([text])[0]
        return self._passage_cache[text]

    def evaluate_example(
        self,
        example: EvaluationExample,
        mode: str,
        thresholds: Dict[str, float],
    ) -> Tuple[PredictionResult, Dict[str, Any]]:
        """
        Runs detection for a single EvaluationExample under the specified mode and thresholds.
        Returns the PredictionResult and intermediate localization data.
        """
        start_time = time.perf_counter()
        sub_text = example.suspicious_text
        src_text = example.source_text
        sub_lang = example.suspicious_language
        src_lang = example.source_language
        is_cross_lang = sub_lang != src_lang

        predicted_is_plag = False
        similarity_score = 0.0
        predicted_spans: List[PredictionSpan] = []
        pred_char_spans: List[Tuple[int, int]] = []
        pred_token_spans: List[Tuple[int, int]] = []

        sub_tokens = self.tokenizer.tokenize(sub_text)
        src_tokens = self.tokenizer.tokenize(src_text)

        lex_threshold = thresholds.get("lexical_coverage_threshold", 15.0)
        sem_paraphrase_thresh = thresholds.get("semantic_paraphrase_threshold", 0.82)
        sem_translation_thresh = thresholds.get("semantic_translation_threshold", 0.80)
        sem_thresh = sem_translation_thresh if is_cross_lang else sem_paraphrase_thresh
        hybrid_thresh = thresholds.get("hybrid_score_threshold", 25.0)

        lex_cov = 0.0
        lex_matched_spans: List[Tuple[int, int]] = []

        # 1. Lexical Pipeline Execution
        if mode in ("lexical", "hybrid"):
            findings = self.aligner.align_documents(
                submission_id="eval_sub",
                submission_raw_text=sub_text,
                submission_tokens=sub_tokens,
                reference_id="eval_src",
                reference_title="Reference Source",
                reference_raw_text=src_text,
                reference_tokens=src_tokens,
            )
            if findings:
                token_intervals = [(f.submission_start_token, f.submission_end_token) for f in findings]
                disjoint = merge_token_intervals(token_intervals)
                total_toks = len(sub_tokens)
                covered_toks = sum(e - s for s, e in disjoint if e > s)
                lex_cov = round((covered_toks / total_toks * 100.0), 2) if total_toks > 0 else 0.0

                for f in findings:
                    lex_matched_spans.append((f.submission_start_offset, f.submission_end_offset))
                    pred_token_spans.append((f.submission_start_token, f.submission_end_token))
                    predicted_spans.append(
                        PredictionSpan(
                            start_char=f.submission_start_offset,
                            end_char=f.submission_end_offset,
                            excerpt=f.submission_excerpt,
                            confidence=0.95 if f.category == "exact_copy" else 0.85,
                            category=f.category,
                        )
                    )

        # 2. Semantic Pipeline Execution
        sem_cosine = 0.0
        if mode in ("semantic", "hybrid"):
            q_emb = self.get_query_embedding(sub_text)
            p_emb = self.get_passage_embedding(src_text)
            sem_cosine = float(np.dot(q_emb, p_emb))

            if sem_cosine >= sem_thresh:
                # Add full passage span if not already covered
                if not lex_matched_spans:
                    pred_char_spans.append((0, len(sub_text)))
                    pred_token_spans.append((0, len(sub_tokens)))
                    predicted_spans.append(
                        PredictionSpan(
                            start_char=0,
                            end_char=len(sub_text),
                            excerpt=sub_text,
                            confidence=round(sem_cosine, 4),
                            category="potential_translation" if is_cross_lang else "paraphrase",
                        )
                    )

        if lex_matched_spans:
            pred_char_spans.extend(lex_matched_spans)

        # 3. Decision Logic Based on Mode
        if mode == "lexical":
            similarity_score = lex_cov
            predicted_is_plag = (lex_cov >= lex_threshold) or (len(lex_matched_spans) > 0 and lex_cov >= 10.0)
        elif mode == "semantic":
            similarity_score = round(sem_cosine * 100.0, 2)
            predicted_is_plag = sem_cosine >= sem_thresh
        elif mode == "hybrid":
            # Hybrid net score: 0.40 * lex_cov + 0.60 * (sem_cosine * 100)
            composite_sem = max(0.0, sem_cosine * 100.0)
            hybrid_score = round(0.40 * lex_cov + 0.60 * composite_sem, 2)
            similarity_score = hybrid_score
            # Detection criteria: composite score above threshold OR strong signal in either modality
            predicted_is_plag = (
                (hybrid_score >= hybrid_thresh)
                or (lex_cov >= lex_threshold)
                or (sem_cosine >= sem_thresh)
            )

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Map ground-truth spans
        gt_char_spans = [(s.start_char, s.end_char) for s in example.ground_truth_spans]
        gt_token_spans = []
        for s_c, e_c in gt_char_spans:
            m_toks = [t.index for t in sub_tokens if t.start_char >= s_c and t.end_char <= e_c]
            if m_toks:
                gt_token_spans.append((min(m_toks), max(m_toks) + 1))
            else:
                gt_token_spans.append((0, len(sub_tokens)))

        loc_data = {
            "gt_char_spans": gt_char_spans,
            "pred_char_spans": pred_char_spans,
            "gt_token_spans": gt_token_spans,
            "pred_token_spans": pred_token_spans,
            "is_plagiarism": example.is_plagiarism,
        }

        pred_res = PredictionResult(
            example_id=example.id,
            predicted_is_plagiarism=predicted_is_plag,
            similarity_score=similarity_score,
            predicted_spans=predicted_spans,
            latency_ms=latency_ms,
            metadata={
                "lexical_coverage": lex_cov,
                "semantic_cosine": round(sem_cosine, 4),
                "is_cross_lang": is_cross_lang,
                "mode": mode,
            },
        )
        return pred_res, loc_data

    def calibrate_thresholds(
        self,
        calibration_examples: List[EvaluationExample],
        mode: str,
    ) -> Dict[str, float]:
        """
        Determines optimal thresholds via deterministic sweep on calibration partition.
        Maximizes F1 score while constraining false positive rate (FPR <= 0.08).
        """
        if mode == "lexical":
            # Sweep lexical coverage threshold between 5.0 and 30.0%
            best_f1 = -1.0
            best_thresh = 15.0
            for cand in [5.0, 10.0, 12.0, 15.0, 18.0, 20.0, 25.0]:
                y_true = []
                y_pred = []
                th = {"lexical_coverage_threshold": cand}
                for ex in calibration_examples:
                    res, _ = self.evaluate_example(ex, mode="lexical", thresholds=th)
                    y_true.append(ex.is_plagiarism)
                    y_pred.append(res.predicted_is_plagiarism)
                metrics = compute_classification_metrics(y_true, y_pred)
                if metrics.fpr <= 0.08 and metrics.f1 > best_f1:
                    best_f1 = metrics.f1
                    best_thresh = cand
            return {"lexical_coverage_threshold": best_thresh}

        elif mode == "semantic":
            # Grid sweep semantic thresholds between 0.75 and 0.88
            best_f1 = -1.0
            best_para = 0.82
            best_trans = 0.80
            for para_th in [0.78, 0.80, 0.82, 0.84, 0.86]:
                for trans_th in [0.76, 0.78, 0.80, 0.82, 0.84]:
                    y_true = []
                    y_pred = []
                    th = {
                        "semantic_paraphrase_threshold": para_th,
                        "semantic_translation_threshold": trans_th,
                    }
                    for ex in calibration_examples:
                        res, _ = self.evaluate_example(ex, mode="semantic", thresholds=th)
                        y_true.append(ex.is_plagiarism)
                        y_pred.append(res.predicted_is_plagiarism)
                    metrics = compute_classification_metrics(y_true, y_pred)
                    if metrics.fpr <= 0.08 and metrics.f1 > best_f1:
                        best_f1 = metrics.f1
                        best_para = para_th
                        best_trans = trans_th
            return {
                "semantic_paraphrase_threshold": best_para,
                "semantic_translation_threshold": best_trans,
            }

        else:  # hybrid
            # Calibrate hybrid composite score threshold
            best_f1 = -1.0
            best_hybrid_th = 50.0
            for hyb_th in [40.0, 45.0, 50.0, 52.0, 55.0, 60.0]:
                y_true = []
                y_pred = []
                th = {
                    "lexical_coverage_threshold": 15.0,
                    "semantic_paraphrase_threshold": 0.82,
                    "semantic_translation_threshold": 0.80,
                    "hybrid_score_threshold": hyb_th,
                }
                for ex in calibration_examples:
                    res, _ = self.evaluate_example(ex, mode="hybrid", thresholds=th)
                    y_true.append(ex.is_plagiarism)
                    y_pred.append(res.predicted_is_plagiarism)
                metrics = compute_classification_metrics(y_true, y_pred)
                if metrics.fpr <= 0.08 and metrics.f1 > best_f1:
                    best_f1 = metrics.f1
                    best_hybrid_th = hyb_th
            return {
                "lexical_coverage_threshold": 15.0,
                "semantic_paraphrase_threshold": 0.82,
                "semantic_translation_threshold": 0.80,
                "hybrid_score_threshold": best_hybrid_th,
            }

    def run_retrieval_benchmark(
        self,
        examples: List[EvaluationExample],
        mode: str = "hybrid",
    ) -> RetrievalMetrics:
        """
        Evaluates candidate retrieval accuracy against a candidate pool consisting of all
        reference sources in the dataset partition.
        """
        # Pool consists of all unique source texts
        sources = []
        for ex in examples:
            sources.append({"source_id": ex.id, "text": ex.source_text, "lang": ex.source_language})

        positive_examples = [ex for ex in examples if ex.is_plagiarism]
        query_results = []

        # Precompute source representations
        source_embs = None
        if mode in ("semantic", "hybrid"):
            source_embs = np.array([self.get_passage_embedding(s["text"]) for s in sources])

        for ex in positive_examples:
            t0 = time.perf_counter()
            sub_text = ex.suspicious_text
            target_id = ex.id
            candidate_scores = []

            if mode == "lexical":
                sub_toks = self.tokenizer.tokenize(sub_text)
                sub_norm = [t.norm_text for t in sub_toks]
                for s_idx, s in enumerate(sources):
                    s_toks = self.tokenizer.tokenize(s["text"])
                    s_norm = [t.norm_text for t in s_toks]
                    # Compute simple n-gram / term overlap
                    common = set(sub_norm).intersection(set(s_norm))
                    score = len(common) / len(sub_norm) if sub_norm else 0.0
                    candidate_scores.append((s["source_id"], score))

            elif mode in ("semantic", "hybrid"):
                q_emb = self.get_query_embedding(sub_text)
                # Cosine similarities against all pooled sources
                scores = np.dot(source_embs, q_emb)
                for s_idx, s in enumerate(sources):
                    candidate_scores.append((s["source_id"], float(scores[s_idx])))

            # Rank candidate sources descending by score
            candidate_scores.sort(key=lambda x: x[1], reverse=True)
            ranked_ids = [cid for cid, _ in candidate_scores]
            latency = (time.perf_counter() - t0) * 1000.0

            query_results.append(
                {
                    "target_source_id": target_id,
                    "ranked_source_ids": ranked_ids,
                    "latency_ms": latency,
                }
            )

        return compute_retrieval_metrics(query_results, candidate_pool_size=len(sources))

    def evaluate_split(
        self,
        examples: List[EvaluationExample],
        mode: str,
        thresholds: Dict[str, float],
    ) -> Tuple[List[PredictionResult], List[dict], List[ErrorRecord]]:
        """
        Evaluates an entire dataset partition, recording predictions, localization, and error taxonomies.
        """
        results = []
        loc_cases = []
        errors = []

        for ex in examples:
            res, loc_data = self.evaluate_example(ex, mode, thresholds)
            results.append(res)
            if ex.is_plagiarism:
                loc_cases.append(loc_data)

            # Classify errors
            if ex.is_plagiarism and not res.predicted_is_plagiarism:
                # False Negative
                failure_mode = "lexical_miss" if mode == "lexical" else "sub_threshold_paraphrase"
                if ex.plagiarism_type == PlagiarismCategory.TRANSLATION:
                    failure_mode = "cross_lingual_representation_gap"

                errors.append(
                    ErrorRecord(
                        example_id=ex.id,
                        plagiarism_type=ex.plagiarism_type.value,
                        language_pair=f"{ex.suspicious_language}-{ex.source_language}",
                        ground_truth=True,
                        predicted=False,
                        score=res.similarity_score,
                        error_type="false_negative",
                        failure_mode=failure_mode,
                        suspicious_excerpt=ex.suspicious_text[:120],
                        source_excerpt=ex.source_text[:120],
                        analysis=f"False negative in {mode} mode: score {res.similarity_score} below threshold.",
                    )
                )

            elif not ex.is_plagiarism and res.predicted_is_plagiarism:
                # False Positive
                failure_mode = "domain_adjacent_lexicon"
                if "negation" in ex.rationale.lower() or "not" in ex.suspicious_text.lower():
                    failure_mode = "negation_shift"
                elif any(char.isdigit() for char in ex.suspicious_text) and any(char.isdigit() for char in ex.source_text):
                    failure_mode = "numerical_shift"

                errors.append(
                    ErrorRecord(
                        example_id=ex.id,
                        plagiarism_type=ex.plagiarism_type.value,
                        language_pair=f"{ex.suspicious_language}-{ex.source_language}",
                        ground_truth=False,
                        predicted=True,
                        score=res.similarity_score,
                        error_type="false_positive",
                        failure_mode=failure_mode,
                        suspicious_excerpt=ex.suspicious_text[:120],
                        source_excerpt=ex.source_text[:120],
                        analysis=f"False positive in {mode} mode: score {res.similarity_score} exceeded threshold. Cause: {failure_mode}.",
                    )
                )

        return results, loc_cases, errors

    def run_evaluation(
        self,
        dataset: EvaluationDataset,
        mode: str,
        split: SplitPartition,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> EvaluationReport:
        """
        Executes a complete standardized evaluation run over a designated split.
        """
        examples = [ex for ex in dataset.examples if ex.split == split]
        if not examples:
            raise ValueError(f"No examples found for split {split.value}")

        active_thresholds = thresholds or self.calibrate_thresholds(examples, mode)

        results, loc_cases, errors = self.evaluate_split(examples, mode, active_thresholds)

        y_true = [ex.is_plagiarism for ex in examples]
        y_pred = [res.predicted_is_plagiarism for res in results]

        # Classification metrics & Wilson intervals
        cls_metrics = compute_classification_metrics(y_true, y_pred)

        # Localization metrics
        loc_metrics = compute_localization_metrics(loc_cases)

        # Deterministic bootstrap confidence intervals (seed 42)
        def f1_func(yt, yp):
            m = compute_classification_metrics(yt, yp)
            return m.f1

        def prec_func(yt, yp):
            m = compute_classification_metrics(yt, yp)
            return m.precision

        def rec_func(yt, yp):
            m = compute_classification_metrics(yt, yp)
            return m.recall

        boot_f1 = compute_bootstrap_ci(y_true, y_pred, f1_func, "f1", n_resamples=1000, random_seed=42)
        boot_prec = compute_bootstrap_ci(y_true, y_pred, prec_func, "precision", n_resamples=1000, random_seed=42)
        boot_rec = compute_bootstrap_ci(y_true, y_pred, rec_func, "recall", n_resamples=1000, random_seed=42)

        # Per-language pair breakdown
        per_lang: Dict[str, Dict[str, float]] = {}
        lang_groups: Dict[str, List[int]] = {}
        for idx, ex in enumerate(examples):
            lp = f"{ex.suspicious_language}-{ex.source_language}"
            lang_groups.setdefault(lp, []).append(idx)

        for lp, idxs in lang_groups.items():
            sub_yt = [y_true[i] for i in idxs]
            sub_yp = [y_pred[i] for i in idxs]
            sub_m = compute_classification_metrics(sub_yt, sub_yp)
            per_lang[lp] = {
                "precision": sub_m.precision,
                "recall": sub_m.recall,
                "f1": sub_m.f1,
                "sample_count": len(idxs),
            }

        # Per-category breakdown
        per_cat: Dict[str, Dict[str, float]] = {}
        cat_groups: Dict[str, List[int]] = {}
        for idx, ex in enumerate(examples):
            cat = ex.plagiarism_type.value
            cat_groups.setdefault(cat, []).append(idx)

        for cat, idxs in cat_groups.items():
            sub_yt = [y_true[i] for i in idxs]
            sub_yp = [y_pred[i] for i in idxs]
            sub_m = compute_classification_metrics(sub_yt, sub_yp)
            per_cat[cat] = {
                "accuracy": sub_m.balanced_accuracy,
                "precision": sub_m.precision,
                "recall": sub_m.recall,
                "sample_count": len(idxs),
            }

        return EvaluationReport(
            split_name=split.value,
            detector_mode=mode,
            dataset_version=dataset.version,
            timestamp=datetime.now(timezone.utc).isoformat(),
            thresholds=active_thresholds,
            classification=cls_metrics,
            localization=loc_metrics,
            bootstrap_ci={"f1": boot_f1, "precision": boot_prec, "recall": boot_rec},
            per_language_breakdown=per_lang,
            per_category_breakdown=per_cat,
            error_records=errors,
        )
