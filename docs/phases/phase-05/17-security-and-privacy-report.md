# Security & Privacy Verification Report

## 1. Threat Model & Privacy Perimeter

In plagiarism detection systems, documents submitted for analysis frequently contain proprietary intellectual property, pre-publication academic research, or confidential student work.

Phase 5 verified the system against the following core threat vectors:

```
[Local Browser UI] ---> [FastAPI Localhost:8000] ---> [Local SQLite / Filesystem Storage]
                               ▲
                               | (Air-Gapped Local Inference)
                       [Local E5 Weights]
```

---

## 2. Security Invariants Verification

### 2.1 Complete Network Air-Gap
- **Zero Outbound Telemetry**: Verified that no HTTP or gRPC requests leave localhost during model inference or evaluation.
- **Local Weight Cache**: Model weights are loaded strictly from the local filesystem directory (`storage/model_cache/`).
- **No Third-Party Paid APIs**: Zero reliance on external SaaS embedding APIs (OpenAI, Cohere, Anthropic).

### 2.2 Deserialization Safety (No Pickle Vulnerabilities)
- Dense embeddings are stored and retrieved from SQLite `passage_embeddings` as raw IEEE 754 float32 byte buffers (`tobytes()` and `np.frombuffer()`).
- The Python standard library `pickle` module is strictly prohibited from vector persistence, eliminating arbitrary code execution vectors.

### 2.3 Partition Isolation
- Evaluation examples and benchmark datasets reside in `data/evaluation/` and never interact with user-uploaded document collections in `storage/local_metadata.db`.
- Foreign key cascading (`ON DELETE CASCADE`) ensures that if a document is deleted, all associated passage embeddings and Winnowing fingerprints are permanently purged.
