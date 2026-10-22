# Phase 4 Model Selection: Multilingual Dense Embedding Model

## 1. Evaluation of Candidate Models

To support English, Hindi, and Telugu cross-lingual retrieval natively on a Windows 11 laptop (16 GB RAM, RTX 3050 GPU / Intel CPU) without external API dependencies, four candidate models were evaluated against engineering constraints:

| Candidate Model | Embedding Dim | Size on Disk | Max Sequence Length | English Quality | Hindi / Indic Quality | Telugu Support | License | Decision |
|---|---|---|---|---|---|---|---|---|
| **intfloat/multilingual-e5-small** | **384** | **~470 MB** | **512 tokens** | **High** | **High** | **Supported** | **MIT / Apache 2.0** | **SELECTED** |
| `intfloat/multilingual-e5-base` | 768 | ~1.1 GB | 512 tokens | High | Very High | Supported | Apache 2.0 | Deferred (Memory / CPU latency) |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384 | ~470 MB | 128 tokens | Moderate | Moderate | Limited Telugu coverage | Apache 2.0 | Rejected (Short context limit) |
| `sentence-transformers/LaBSE` | 768 | ~1.8 GB | 512 tokens | High | High | Good | Apache 2.0 | Rejected (Heavy footprint on localhost) |

---

## 2. Technical Justification for `multilingual-e5-small`

1. **Pretrained Multilingual Representation**: Trained on multilingual web-scale query-passage pairs spanning over 100 languages, with strong performance on Indic scripts (Devanagari, Telugu, Tamil, Bengali).
2. **Asymmetric Retrieval Head**: Employs asymmetric prefix tuning:
   - Queries: `query: <text>`
   - Passages / Reference documents: `passage: <text>`
   This optimizes directional retrieval where short submission queries match longer source passages.
3. **Compact Footprint & Latency**: With only 384 dimensions and ~118M parameters, it requires $<1.2$ GB of system RAM during inference. A single passage encodes in $\sim 28$ ms on native CPU, allowing instantaneous interactive analysis on consumer hardware without dedicated CUDA GPU requirements.
4. **Permissive Open-Source Licensing**: Apache 2.0 / MIT license allows fully compliant, royalty-free academic and commercial deployment.

---

## 3. Local Model Cache & Air-Gapped Operation

- **Model Identifier**: `intfloat/multilingual-e5-small`
- **Model Revision**: `614241f622f53c4eeff9890bdc4f31cfecc418b3`
- **Local Storage Path**: `storage/model_cache/models--intfloat--multilingual-e5-small/snapshots/614241f622f53c4eeff9890bdc4f31cfecc418b3`
- **Cached Files**:
  - `model.safetensors` (470,610,648 bytes)
  - `tokenizer.json` (17,092,306 bytes)
  - `sentencepiece.bpe.model` (5,069,321 bytes)
  - `config.json`, `tokenizer_config.json`, `modules.json`

The system operates completely air-gapped from Hugging Face once downloaded. The cache directory is strictly excluded from version control via `.gitignore`.
