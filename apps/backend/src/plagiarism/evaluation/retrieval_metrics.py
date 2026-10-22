"""
Retrieval Metrics Computation for Information Retrieval and Candidate Selection.
Calculates Recall@1, Recall@5, Recall@10, Mean Reciprocal Rank (MRR),
Mean Average Precision (MAP), and retrieval latency across candidate pools.
"""

from typing import Any, Dict, List
from plagiarism.evaluation.schemas import RetrievalMetrics


def compute_retrieval_metrics(
    query_results: List[Dict[str, Any]],
    candidate_pool_size: int,
) -> RetrievalMetrics:
    """
    Computes standard IR ranking metrics.
    Each item in `query_results` must contain:
    - `target_source_id`: True relevant document ID
    - `ranked_source_ids`: Ordered list of retrieved document IDs (rank 1 is index 0)
    - `latency_ms`: Execution time in milliseconds
    """
    if not query_results:
        return RetrievalMetrics(
            recall_at_1=0.0,
            recall_at_5=0.0,
            recall_at_10=0.0,
            mrr=0.0,
            map_score=0.0,
            mean_latency_ms=0.0,
            candidate_pool_size=candidate_pool_size,
            queries_evaluated=0,
        )

    r_at_1_hits = 0
    r_at_5_hits = 0
    r_at_10_hits = 0
    reciprocal_ranks = []
    average_precisions = []
    latencies = []

    for qr in query_results:
        target = qr["target_source_id"]
        ranked = qr["ranked_source_ids"]
        latency = qr.get("latency_ms", 0.0)
        latencies.append(latency)

        # 1-indexed rank of target source
        rank = None
        for idx, doc_id in enumerate(ranked):
            if doc_id == target:
                rank = idx + 1
                break

        if rank is not None:
            if rank <= 1:
                r_at_1_hits += 1
            if rank <= 5:
                r_at_5_hits += 1
            if rank <= 10:
                r_at_10_hits += 1

            rr = 1.0 / rank
            reciprocal_ranks.append(rr)
            average_precisions.append(rr)  # For single true target, AP is 1/rank
        else:
            reciprocal_ranks.append(0.0)
            average_precisions.append(0.0)

    num_queries = len(query_results)
    mean_latency = sum(latencies) / num_queries if num_queries > 0 else 0.0

    return RetrievalMetrics(
        recall_at_1=round(r_at_1_hits / num_queries, 4),
        recall_at_5=round(r_at_5_hits / num_queries, 4),
        recall_at_10=round(r_at_10_hits / num_queries, 4),
        mrr=round(sum(reciprocal_ranks) / num_queries, 4),
        map_score=round(sum(average_precisions) / num_queries, 4),
        mean_latency_ms=round(mean_latency, 2),
        candidate_pool_size=candidate_pool_size,
        queries_evaluated=num_queries,
    )
