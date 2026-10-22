# Information Retrieval & Candidate Ranking Metrics

## 1. Candidate Retrieval Evaluation Framework

In real-world plagiarism detection, suspicious documents are not compared against a single known source; they are evaluated against an entire repository or collection of reference documents. The retrieval engine must rank the true copied source at the top of candidate matches.

Phase 5 evaluated candidate retrieval across **20 reference source documents** for all positive queries in the held-out partition ($N=11$ positive queries):

---

## 2. Empirical Ranking Results

| Metric | Lexical Mode | Semantic AI Mode | Hybrid Mode | Relative Gain |
| :--- | :---: | :---: | :---: | :--- |
| **Recall@1** | 63.64% | **81.82%** | **81.82%** | **+18.18%** |
| **Recall@5** | 63.64% | **100.00%** | **100.00%** | **+36.36%** |
| **Recall@10** | 63.64% | **100.00%** | **100.00%** | **+36.36%** |
| **Mean Reciprocal Rank (MRR)** | 0.6724 | **0.8939** | **0.8939** | **+0.2215** |
| **Mean Average Precision (MAP)** | 0.6724 | **0.8939** | **0.8939** | **+0.2215** |
| **Mean Retrieval Latency** | **0.05 ms** | 0.15 ms | 0.18 ms | Fast CPU inference |

---

## 3. Analysis of Retrieval Dynamics

### 3.1 Lexical Ceiling
The lexical retrieval engine plateaus at **63.64% Recall@1 through Recall@10**.
- For exact copies, lexical token overlap ranks the target document at Rank 1.
- For paraphrases and cross-lingual translations, lexical overlap with the true source is 0%, meaning the true source is not retrieved in the top 10 candidates.

### 3.2 Semantic & Hybrid Superiority
- **Recall@5 reaches 100.0%**: In every single query, the true source document was retrieved within the top 5 candidates.
- **MRR of 0.8939**: Indicates that on average, the true source appears at Rank 1.11 across the entire candidate pool.
- **Microsecond Ranking Speed**: Ranking 20 candidate vectors via vectorized NumPy dot products takes under **0.2 milliseconds**.
