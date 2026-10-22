# Phase 4 Embedding Engine: Architecture & Invariant Specifications

## 1. Embedding Provider Abstraction

The embedding engine is encapsulated by the `SemanticEmbeddingProvider` abstract base class in `apps/backend/src/plagiarism/services/semantic/provider.py`. The design decouples downstream retrieval logic from the specific transformer framework:

```python
class SemanticEmbeddingProvider(ABC):
    @abstractmethod
    def encode_queries(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encodes query texts into normalized dense vectors."""
        pass

    @abstractmethod
    def encode_passages(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encodes reference passages into normalized dense vectors."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Returns model metadata and execution hardware descriptor."""
        pass
```

---

## 2. Invariant Properties & Safety Rules

1. **Dimensional Invariant**: All produced embedding arrays are of shape $(N, 384)$ with dtype `numpy.float32`.
2. **$L_2$ Normalization Invariant**: Every vector satisfies:
   $$\|v\|_2 = \sqrt{\sum_{i=1}^{384} v_i^2} = 1.0 \pm 10^{-4}$$
   This allows cosine similarity to be computed via dot product: $\text{Cosine}(u, v) = u \cdot v$.
3. **Asymmetric Prefix Conditioning**:
   - Query inputs are automatically prepended with `"query: "`.
   - Passage inputs are automatically prepended with `"passage: "`.
4. **Deterministic Inference**: Model execution runs in `torch.inference_mode()` with `model.eval()`, ensuring identical inputs yield bit-exact float32 vectors across calls.
5. **Thread-Safe Process Singleton**: `get_embedding_provider()` utilizes a double-checked thread lock to load weights into memory exactly once per process.

---

## 3. Empty & Edge Case Input Handling

- **Empty Text List**: Returns `np.empty((0, 384), dtype=np.float32)`.
- **Whitespace / Blank Texts**: Encoded as `"query: empty"` or `"passage: empty"` rather than raising exceptions, guaranteeing pipeline stability on malformed documents.
- **Batch Processing**: Texts are batched in groups of 32 to optimize CPU cache utilization and prevent out-of-memory spikes.
