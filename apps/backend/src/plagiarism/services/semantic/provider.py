"""
Semantic Embedding Provider.
Loads and executes dense multilingual embedding models locally.
Adheres to Phase 4 requirements: local inference, intfloat/multilingual-e5-small,
E5 query/passage prefixes, L2 normalization, deterministic evaluation.
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
import torch

from plagiarism.core.config import get_settings

logger = logging.getLogger(__name__)


class SemanticEmbeddingProvider(ABC):
    """
    Abstract interface for dense embedding generation.
    """

    @abstractmethod
    def encode_queries(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Encode query texts (submission passages) using model query format."""
        pass

    @abstractmethod
    def encode_passages(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Encode reference passage texts using model passage format."""
        pass

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]:
        """Return model metadata (id, revision, dimension, device)."""
        pass


class LocalSentenceTransformerProvider(SemanticEmbeddingProvider):
    """
    Local implementation using SentenceTransformers and intfloat/multilingual-e5-small.
    """

    def __init__(
        self,
        model_name: str | None = None,
        revision: str | None = None,
        cache_dir: Path | None = None,
        device: str | None = None,
    ):
        settings = get_settings()
        self.model_name = model_name or settings.SEMANTIC_MODEL_NAME
        self.revision = revision or settings.SEMANTIC_MODEL_REVISION
        self.cache_dir = cache_dir or settings.SEMANTIC_MODEL_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Device determination
        target_device = device or settings.SEMANTIC_DEVICE
        if target_device == "auto":
            self.device_str = "cuda" if torch.cuda.is_available() else "cpu"
        elif target_device == "cuda":
            self.device_str = "cuda" if torch.cuda.is_available() else "cpu"
            if self.device_str == "cpu":
                logger.warning("CUDA requested but not available. Falling back to CPU safely.")
        else:
            self.device_str = "cpu"

        self.embedding_dim = settings.SEMANTIC_EMBEDDING_DIM
        self.max_seq_length = settings.SEMANTIC_MAX_SEQ_LENGTH
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        """Loads SentenceTransformer with safe local cache and offline configuration."""
        from sentence_transformers import SentenceTransformer

        # Configure environment to prioritize local cache and enforce offline operation
        os.environ["HF_HOME"] = str(self.cache_dir.resolve())
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

        logger.info(
            "Loading local semantic model '%s' (revision: %s) on device '%s' from cache '%s'...",
            self.model_name,
            self.revision,
            self.device_str,
            self.cache_dir,
        )

        try:
            self._model = SentenceTransformer(
                self.model_name,
                revision=self.revision,
                cache_folder=str(self.cache_dir),
                device=self.device_str,
                trust_remote_code=False,
                local_files_only=True,
            )
            self._model.eval()
            self._model.max_seq_length = self.max_seq_length
            logger.info("Semantic model '%s' loaded successfully offline from local cache.", self.model_name)
        except Exception as offline_err:
            logger.warning(
                "Offline model load with local_files_only=True failed (%s); trying fallback...",
                offline_err,
            )
            try:
                self._model = SentenceTransformer(
                    self.model_name,
                    revision=self.revision,
                    cache_folder=str(self.cache_dir),
                    device=self.device_str,
                    trust_remote_code=False,
                )
                self._model.eval()
                self._model.max_seq_length = self.max_seq_length
                logger.info("Semantic model '%s' loaded via fallback.", self.model_name)
            except Exception as e:
                logger.exception("Failed to load semantic model '%s': %s", self.model_name, str(e))
                raise RuntimeError(
                    f"Semantic model loading failure. Ensure offline assets are prepared using scripts/prepare-offline-demo.ps1: {e}"
                ) from e

    def get_model_info(self) -> dict[str, Any]:
        """Returns model descriptor metadata."""
        settings = get_settings()
        return {
            "model_name": self.model_name,
            "revision": self.revision,
            "embedding_dim": self.embedding_dim,
            "embedding_dimension": self.embedding_dim,
            "max_seq_length": self.max_seq_length,
            "max_sequence_length": self.max_seq_length,
            "device": self.device_str,
            "runtime_device": self.device_str,
            "is_gpu": self.device_str == "cuda",
            "query_prefix": "query: ",
            "passage_prefix": "passage: ",
            "normalization": "L2",
            "model_path": str(self.cache_dir),
            "paraphrase_threshold": settings.SEMANTIC_PARAPHRASE_THRESHOLD,
            "translation_threshold": settings.SEMANTIC_TRANSLATION_THRESHOLD,
        }

    def encode_queries(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """
        Encodes query texts with E5 prefix 'query: ' and L2 normalization.
        """
        if not texts:
            return np.empty((0, self.embedding_dim), dtype=np.float32)

        # Handle empty/blank inputs deterministically
        prefixed = []
        for t in texts:
            clean = t.strip() if t else ""
            prefixed.append(f"query: {clean}" if clean else "query: empty")

        with torch.inference_mode():
            embeddings = self._model.encode(
                prefixed,
                batch_size=batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )

        return embeddings.astype(np.float32)

    def encode_passages(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """
        Encodes reference passages with E5 prefix 'passage: ' and L2 normalization.
        """
        if not texts:
            return np.empty((0, self.embedding_dim), dtype=np.float32)

        prefixed = []
        for t in texts:
            clean = t.strip() if t else ""
            prefixed.append(f"passage: {clean}" if clean else "passage: empty")

        with torch.inference_mode():
            embeddings = self._model.encode(
                prefixed,
                batch_size=batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )

        return embeddings.astype(np.float32)


# Singleton instance for process-level model sharing
_provider_instance: SemanticEmbeddingProvider | None = None


def get_embedding_provider() -> SemanticEmbeddingProvider:
    """Returns singleton semantic embedding provider."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = LocalSentenceTransformerProvider()
    return _provider_instance


def reset_embedding_provider_for_test(mock_provider: SemanticEmbeddingProvider | None = None) -> None:
    """Allows test fixtures to inject mock providers."""
    global _provider_instance
    _provider_instance = mock_provider
