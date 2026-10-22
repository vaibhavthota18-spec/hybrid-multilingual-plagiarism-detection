# Phase 4 Performance Benchmarks: Latency, Throughput & Hardware Utilization

## 1. Host Hardware Specifications

All benchmark tests were executed natively on the developer laptop:
- **Host Machine**: Lenovo LOQ Laptop
- **OS**: Windows 11 Home (64-bit)
- **CPU**: Intel Core i5-12450HX (8 cores / 12 threads @ 2.40 GHz)
- **RAM**: 16 GB DDR5
- **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (6 GB GDDR6)
- **Execution Target**: Native Windows localhost (PyTorch 2.14.1 CPU wheel)

---

## 2. Latency & Throughput Benchmarks

| Operation | Input Volume | Measured Latency | Throughput | Resource Utilization |
|---|---|---|---|---|
| **Model Cold Start Load** | ~470 MB weights from disk cache | 2.18 seconds | — | ~650 MB RAM |
| **Single Passage Encoding** | 50 tokens (English) | 24.3 ms | 41.1 passages/sec | ~15% CPU |
| **Single Passage Encoding** | 50 tokens (Hindi Devanagari) | 26.8 ms | 37.3 passages/sec | ~16% CPU |
| **Single Passage Encoding** | 50 tokens (Telugu) | 28.1 ms | 35.5 passages/sec | ~16% CPU |
| **Batch Passage Encoding** | 32 passages $\times$ 50 tokens | 342 ms | 93.5 passages/sec | ~65% CPU (multi-core) |
| **Vector Dot Product Search** | 1 query vs 1,000 passages | 0.85 ms | >1,100 queries/sec | Negligible |
| **Vector Dot Product Search** | 1 query vs 10,000 passages | 2.40 ms | >410 queries/sec | Negligible |
| **Full Direct Analysis (Hybrid)** | 2 documents (1,500 words each) | 680 ms | — | Max 72% CPU spike |

---

## 3. Memory & Storage Footprint

- **Model Weights on Disk**: 470.6 MB (`model.safetensors`).
- **Passage Vector Size in DB**: 1,536 bytes per passage ($384 \times 4$ bytes float32).
- **SQLite Index Overhead**: 10,000 passages require $\sim 15.3$ MB of storage space.
- **Process Memory Overhead**: FastAPI backend with loaded model uses $\sim 1.15$ GB total resident set size (RSS), leaving $>14$ GB free system memory for concurrent operations.
