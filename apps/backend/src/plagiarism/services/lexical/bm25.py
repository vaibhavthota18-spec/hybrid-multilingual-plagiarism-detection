"""
BM25Okapi Lexical Information Retrieval Engine.
Provides candidate source ranking based on probabilistic term relevance.
BM25 scores represent retrieval relevance, NOT plagiarism percentages.
"""

import math
from collections import Counter


class BM25Index:
    """
    In-memory BM25Okapi inverted index for candidate reference retrieval.
    Formula:
        IDF(t) = ln( (N - n(t) + 0.5) / (n(t) + 0.5) + 1 )
        Score(Q, D) = sum_{t in Q} IDF(t) * ( f(t,D) * (k1 + 1) ) / ( f(t,D) + k1 * (1 - b + b * (|D| / avgdl)) )
    """

    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_ids: list[str] = []
        self.doc_lengths: dict[str, int] = {}
        self.term_frequencies: dict[str, Counter] = {}
        self.doc_frequencies: Counter = Counter()
        self.total_docs: int = 0
        self.avg_doc_length: float = 0.0

    def add_document(self, doc_id: str, tokens: list[str]) -> None:
        """Indexes a document from a list of normalized token strings."""
        if doc_id in self.doc_lengths:
            # Document already indexed; skip or replace
            return

        tf = Counter(tokens)
        self.term_frequencies[doc_id] = tf
        self.doc_lengths[doc_id] = len(tokens)
        self.doc_ids.append(doc_id)

        # Update document frequencies for unique terms in doc
        for term in tf.keys():
            self.doc_frequencies[term] += 1

        self.total_docs = len(self.doc_ids)
        total_len = sum(self.doc_lengths.values())
        self.avg_doc_length = total_len / self.total_docs if self.total_docs > 0 else 0.0

    def idf(self, term: str) -> float:
        """Computes Robertson-Spärck Jones IDF with smoothing (+1 to prevent negative values)."""
        n_t = self.doc_frequencies.get(term, 0)
        numerator = self.total_docs - n_t + 0.5
        denominator = n_t + 0.5
        val = math.log((numerator / denominator) + 1.0)
        return max(0.0, val)

    def score_document(self, query_tokens: list[str], doc_id: str) -> float:
        """Calculates BM25 relevance score of a specific document for a query."""
        if doc_id not in self.term_frequencies or self.total_docs == 0:
            return 0.0

        doc_len = self.doc_lengths.get(doc_id, 0)
        if doc_len == 0 or self.avg_doc_length == 0.0:
            return 0.0

        tf = self.term_frequencies[doc_id]
        score = 0.0
        query_counts = Counter(query_tokens)

        len_norm = 1.0 - self.b + self.b * (doc_len / self.avg_doc_length)

        for term, qf in query_counts.items():
            freq = tf.get(term, 0)
            if freq == 0:
                continue

            idf_val = self.idf(term)
            num = freq * (self.k1 + 1.0)
            den = freq + self.k1 * len_norm
            score += idf_val * (num / den)

        return score

    def rank_candidates(
        self,
        query_tokens: list[str],
        candidate_doc_ids: list[str] = None,
        top_k: int = 20
    ) -> list[tuple[str, float]]:
        """
        Ranks candidate documents by BM25 relevance score.
        If candidate_doc_ids is None, searches all indexed documents.
        Returns ordered list of (doc_id, bm25_score) descending.
        """
        target_ids = candidate_doc_ids if candidate_doc_ids is not None else self.doc_ids
        scored: list[tuple[str, float]] = []

        for doc_id in target_ids:
            s = self.score_document(query_tokens, doc_id)
            if s > 0.0:
                scored.append((doc_id, round(s, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
