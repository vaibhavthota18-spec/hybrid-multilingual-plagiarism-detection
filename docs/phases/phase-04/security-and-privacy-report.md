# Phase 4 Security & Privacy Report: Air-Gapped Inference & Local Storage

## 1. Zero-Cloud Privacy Guarantee

Plagiarism detection systems frequently handle confidential academic theses, proprietary research papers, and student submissions. Phase 4 adheres to strict privacy and air-gap requirements:

1. **No External Inference Calls**: All vector embeddings are generated locally on the host machine using PyTorch and SentenceTransformers. Zero text bytes are transmitted to external cloud APIs (OpenAI, HuggingFace Inference API, etc.).
2. **Local Model Cache**: Model weights are stored in private local directory `storage/model_cache`. After initial one-time model caching, the application operates in an air-gapped environment without internet access.
3. **Repository Exclusion**: `storage/model_cache/`, `storage/private/`, and `storage/*.db*` are strictly excluded from version control via `.gitignore`.

---

## 2. Safe Vector Serialization (Anti-Pickle Invariant)

Python's `pickle` library is notoriously susceptible to arbitrary code execution vulnerabilities during deserialization of untrusted payloads.

- **Vulnerability Defense**: Phase 4 strictly prohibits `pickle.dumps()` or `pickle.loads()` for vector persistence.
- **Implementation**: Vectors are stored as IEEE 754 float32 byte buffers (`tobytes()`) and reconstituted via `np.frombuffer(blob, dtype=np.float32)`.
- **Security Invariant**: Deserialization is purely a memory-view cast of 32-bit floats with bounded length ($384 \times 4 = 1,536$ bytes), eliminating all deserialization code execution vectors.

---

## 3. Data Isolation & Tenant Boundaries

- **Cascade Deletion**: When an administrator or user deletes a document via `DELETE /api/v1/documents/{id}`, foreign key cascading automatically purges all passage embeddings from `passage_embeddings`.
- **Private File Storage**: Uploaded document files are stored in `storage/private/` with sanitized filenames and random UUID prefixes, preventing path traversal attacks (`../`).
