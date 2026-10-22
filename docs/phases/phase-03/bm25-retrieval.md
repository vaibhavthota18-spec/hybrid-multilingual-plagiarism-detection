# Okapi BM25 Candidate Retrieval & Ranking

## 1. Role in the Multi-Stage Detection Pipeline

In **Corpus Comparison Mode** (1:Collection), comparing a candidate submission against dozens, hundreds, or thousands of repository documents via fine-grained Winnowing alignment would introduce unnecessary computational overhead.

To maintain sub-second response times on standard consumer laptops, Phase 3 implements an **Okapi BM25** pre-filtering index. BM25 acts as the coarse candidate retrieval filter, selecting the top-$K$ most relevant reference documents to pass down to fine-grained passage alignment and verification.

---

## 2. Mathematical Formulation

Given a collection of reference documents $\mathcal{D}$, the BM25 relevance score for a document $D \in \mathcal{D}$ against candidate query tokens $Q = \{q_1, q_2, \dots, q_m\}$ is computed as:

$$\text{Score}(D, Q) = \sum_{i=1}^m \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left( 1 - b + b \cdot \frac{|D|}{\text{avgdl}} \right)}$$

### Term Definitions & Constants:
- **$f(q_i, D)$**: Term frequency of token $q_i$ in reference document $D$.
- **$|D|$**: Total token length of document $D$.
- **$\text{avgdl}$**: Average document length across all documents in the active collection:
  $$\text{avgdl} = \frac{1}{|\mathcal{D}|} \sum_{D \in \mathcal{D}} |D|$$
- **$k_1 = 1.2$**: Term frequency saturation parameter. Controls how quickly repeated occurrences of a word reach diminishing returns.
- **$b = 0.75$**: Document length normalization parameter. Heavily penalizes bloated documents while rewarding concise matches.

### Probabilistic Inverse Document Frequency (IDF)
We implement the standard Lucene/Robertson Robertson-Sparck-Jones IDF formula with smoothing to guarantee strictly non-negative values:

$$\text{IDF}(q_i) = \ln \left( 1 + \frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} \right)$$

where:
- **$N$**: Total number of documents in the collection ($|\mathcal{D}|$).
- **$n(q_i)$**: Number of documents containing token $q_i$.

---

## 3. Query Construction from Submissions

When evaluating a candidate submission:
1. The submission text is tokenized into normalized lower-case tokens using `LexicalTokenizer`.
2. Stop-words and single-character tokens are pruned.
3. The query token sequence is submitted to `BM25Index.query(tokens, top_k=10)`.
4. The index evaluates candidate document scores and returns a sorted list of `(document_id, bm25_score)`.
5. Documents scoring above a minimum relevance threshold ($\text{Score} > 0.05$) are dispatched to `PassageAligner`.
