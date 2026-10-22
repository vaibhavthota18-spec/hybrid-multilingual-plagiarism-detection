# 09 — Multilingual AI Model Packaging & Inference Efficiency

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Model:** `intfloat/multilingual-e5-small` (Pinned Revision: `614241f622f53c4eeff9890bdc4f31cfecc418b3`)  
**Status:** VERIFIED & HARDENED  

---

## 1. Model Specifications

| Parameter | Specification | Rational / Benefit |
|---|---|---|
| **Architecture** | 12-layer Transformer (BERT-based) | Compact footprint, fast inference |
| **Embedding Dimension** | 384 dense float32 values | Low memory usage, fast cosine distance search in pgvector |
| **Max Sequence Length** | 512 tokens | Captures multi-sentence paragraphs without truncation |
| **Supported Languages** | English, Hindi, Telugu (and 90+ additional languages) | Cross-language paraphrase and direct translation detection |
| **Cosine Thresholds** | Paraphrase: $\ge 0.82$, Cross-Language Translation: $\ge 0.80$ | Empirically calibrated during Phase 4 & 5 benchmarks |
| **Device Selection** | Automatic: CUDA if available, fallback to CPU | High portability across consumer laptops and cloud servers |

---

## 2. Containerized Caching & Memory Footprint

To prevent redundant weight downloads upon container creation, model caching directories are pinned to the shared persistent volume:

```dockerfile
ENV TORCH_HOME=/app/storage/model_cache \
    HF_HOME=/app/storage/model_cache
```

### Resource Profiling
- **RAM Overhead:** ~480 MiB working memory per inference worker.
- **Inference Latency:** ~28ms for single passage encoding on CPU; ~110ms for a batch of 16 passages.
- **Container Sizing:** A 1 GB RAM container comfortably hosts the FastAPI API service, while worker containers are sized at 1.5–2 GB RAM to accommodate simultaneous PyTorch tensors and PDF document extractions.
