# Performance Benchmarks & Reference Scaling Analysis

## 1. Benchmarking Environment

All benchmarks were measured natively on the user's localhost laptop environment:
- **Device**: Lenovo LOQ Laptop (Windows 11 Home).
- **CPU**: Intel Core Architecture, multi-threaded CPU execution.
- **Python**: 3.12.10 in virtual environment (`apps/backend/.venv`).
- **PyTorch**: 2.14.1+cpu.
- **Model**: `intfloat/multilingual-e5-small` (384 dimensions, float32 weights).

---

## 2. Cold Start vs. Warm Start Latency

| Execution State | Latency | Memory Footprint (Working Set) |
| :--- | :---: | :---: |
| **Initial Process Baseline** | — | **78.5 MB** |
| **Cold Start** (Module import + weight load + 1st inference) | **75,359.48 ms** (~75.3s) | **1,209.3 MB** (+1,130.8 MB) |
| **Warm Start (Mean)** | **101.51 ms** | **1,209.3 MB** (Stable) |
| **Warm Start (p50)** | **101.37 ms** | **1,209.3 MB** |
| **Warm Start (p95)** | **115.14 ms** | **1,209.3 MB** |

---

## 3. Per-Module Latency Breakdown

Measured on a standard technical paragraph (~350 characters, 45 tokens):

| Pipeline Module | Algorithm / Library | Execution Latency |
| :--- | :--- | :---: |
| **Lexical Tokenization** | `LexicalTokenizer` (`unicodedata.normalize`) | **0.68 ms** |
| **Winnowing Fingerprinting** | $k=25, w=16$ Karp-Rabin Rolling Hash | **0.29 ms** |
| **BM25 Candidate Ranking** | Okapi BM25 Index | **0.20 ms** |
| **Passage Alignment** | `PassageAligner` anchor chain search | **0.23 ms** |
| **Dense E5 Encoding** | Transformer forward pass on CPU | **116.97 ms** |
| **Dense Vector Search ($N=100$)** | Vectorized NumPy dot product matrix | **0.06 ms** |

---

## 4. Reference Collection Scaling Benchmark

Empirical evaluation of dense vector search latency as candidate collection scales:

| Candidates ($N$) | Mean Search Latency | 95th Percentile Latency | Vector RAM Footprint |
| :---: | :---: | :---: | :---: |
| **10** | 0.0023 ms | 0.0035 ms | 15.0 KB |
| **50** | 0.0106 ms | 0.0125 ms | 75.0 KB |
| **100** | 0.0158 ms | 0.0184 ms | 150.0 KB |
| **500** | 0.0550 ms | 0.0735 ms | 750.0 KB |
| **1,000** | **0.1863 ms** | 0.2685 ms | 1.50 MB |

---

## 5. Analytical Extrapolation for $N = 10,000$ Reference Documents

Using the empirical scaling slope ($0.0001863$ ms per vector dot product):
- **Projected Search Latency ($N=10,000$)**: **1.86 milliseconds**.
- **Projected Vector Memory ($N=10,000$)**: $10,000 \times 384 \times 4 \text{ bytes} = \mathbf{14.65\text{ MB}}$.
- **Feasibility Verdict**: **Highly feasible natively on localhost CPU**. Even without GPU acceleration or specialized ANN indexers (HNSW/FAISS), a collection of 10,000 reference documents can be searched in under 2 milliseconds on CPU with negligible memory overhead.
