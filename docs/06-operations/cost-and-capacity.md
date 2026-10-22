# Resource Sizing & Capacity Planning

> **Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
> **Phase:** Phase 0 — Blueprint & Architecture  
> **Date:** October 2026  

---

## 1. Capacity Sizing Principles & Assumptions

> **Transparency Note:** All numbers in this document are engineering resource estimates derived from theoretical memory profiles and benchmark footprints of the selected technologies. They are not cloud vendor quotes or fixed commercial price guarantees.

### Baseline Sizing Scenario: Single Institutional Node
- **Indexed Reference Corpus:** 1,000 documents (approx. 25,000 indexed passages).
- **Daily Ingestion / Analysis Throughput:** 500 document similarity analyses per day.
- **Average Submission:** 10 pages (~3,500 words, ~45 passages).
- **Concurrency:** Up to 4 simultaneous analyses executing in parallel.

---

## 2. Component Resource Breakdown

### 2.1 Model & Memory Footprint (RAM)
- **Embedding Weights (`multilingual-e5-base`):**
  - Model disk size: ~1.11 GB (`model.safetensors`).
  - PyTorch in-memory footprint (FP32): ~1.8 GB per worker process.
- **FastAPI Web Server:** ~250 MB RSS.
- **Redis 7:** ~50–100 MB RAM for message queue and job status keys.
- **PostgreSQL 16 + pgvector:**
  - Base instance: ~500 MB RAM.
  - Shared buffers: Recommended 2 GB RAM.
  - Work memory: 64 MB per connection.
- **Total Recommended Node RAM:** **16 GB minimum** (provides headroom for 4 parallel worker processes at ~2 GB RAM each + 4 GB OS and DB cache).

### 2.2 Storage Footprint (Disk & Volumes)
- **Raw Document Files (`storage/uploads/`):**
  - Average PDF size: 1.5 MB.
  - 1,000 reference documents: ~1.5 GB.
  - 10,000 active user documents: ~15 GB.
- **Database Tables (`PostgreSQL`):**
  - Extracted text (`passages`): ~25,000 passages $\times$ 1 KB text = 25 MB.
  - Fingerprints (`fingerprints`): ~25,000 passages $\times$ 15 fingerprints $\times$ 32 bytes = 12 MB.
  - Dense Vectors (`embeddings`):
    - 768 float4 dimensions = $768 \times 4 = 3,072$ bytes raw per passage.
    - PostgreSQL tuple overhead: ~3.2 KB per vector row.
    - 25,000 passages: $25,000 \times 3.2\text{ KB} \approx 80$ MB.
    - 200,000 passages (10,000 docs): $200,000 \times 3.2\text{ KB} \approx 640$ MB.
- **Generated PDF Reports (`storage/reports/`):** ~200 KB per report.
- **Total Recommended Node Storage:** **100 GB NVMe SSD** (accommodates 10,000 documents, database, logs, Docker images, and 30-day backups).

### 2.3 Compute & CPU Allocation
- **Inference Requirements:**
  - Tokenization & forward pass for 45 passages on 8-core CPU (AVX-512 enabled): ~15–30 seconds.
  - Winnowing hash extraction: $<1$ second.
  - Token-level local sequence alignment on top 20 candidates: ~2–5 seconds.
  - Total processing time per 10-page document: ~30–45 seconds under moderate load.
- **Core Allocation:** 8 physical/virtual CPU cores (vCPUs) comfortably support 4 parallel worker processes without thrashing.

### 2.4 Optional GPU Acceleration Comparison
| Resource Dimension | CPU Baseline (8 Cores) | Optional GPU Deployment (NVIDIA T4 / A10G) |
|---|---|---|
| Forward Pass (16-batch) | ~800 ms | ~45 ms (18x speedup) |
| 10-Page Document Inference | ~25 seconds | ~1.5 seconds |
| Host Memory Need | 16 GB System RAM | 16 GB System RAM + 8 GB VRAM |
| Operational Complexity | Low (Standard x86_64 server) | Medium (NVIDIA container toolkit, CUDA drivers) |
| Phase 0–4 Recommendation | **Sufficient for MVP & Baseline** | Reserve for high-volume enterprise scaling |

---

## 3. Network & Backup Throughput

- **Network Ingress:** 500 uploads $\times$ 1.5 MB = 750 MB / day.
- **Network Egress (Reports):** 300 downloads $\times$ 200 KB = 60 MB / day.
- **Daily Backup Volume:** ~2 GB compressed snapshot.
- Network bandwidth requirements are minimal; a standard 100 Mbps uplink easily satisfies demands.
