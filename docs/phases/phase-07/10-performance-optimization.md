# Phase 7 — Performance Benchmarks & Optimization

## 1. Measured System Latencies (Lenovo LOQ / Windows 11)

| Subsystem / Operation | Typical Duration | Bottleneck / Mitigation |
| :--- | :--- | :--- |
| **Backend Startup (FastAPI)** | ~1.2 s | Fast startup via lazy model loading |
| **Model Cold-Load (E5-Small)** | ~3.5 s | Hugging Face weights cached locally in user cache |
| **Model Warm Inference (64 passages)** | ~120 ms | Batched tensor operations on CPU |
| **Document Ingestion (TXT)** | < 50 ms | Direct UTF-8 decode & NFC normalization |
| **Document Ingestion (PDF, 5 pages)** | ~180 ms | `pypdf` page text extraction |
| **Winnowing Fingerprinting** | ~15 ms | Rolling 64-bit integer hashing |
| **BM25 Retrieval (Corpus N=50)** | ~25 ms | In-memory token frequency maps |
| **Passage Alignment (Smith-Waterman)** | ~40 ms | Bounded DP matrix with loop counter safety |
| **Full Direct Hybrid Analysis** | ~450 ms | End-to-end extraction + hybrid matching |
| **PDF Report Generation (ReportLab)** | ~60 ms | Fast streaming canvas generation |
| **Offline HTML Report Generation** | < 10 ms | In-memory string templating |

## 2. Resource Footprint
- **RAM Working Set:** ~380 MB during active PyTorch model inference.
- **Disk Footprint:**
  - Model weights: ~133 MB (intfloat/multilingual-e5-small).
  - Web bundle: 279 kB (gzip: 74 kB).
  - SQLite database: ~1.5 MB for 500+ document records.
