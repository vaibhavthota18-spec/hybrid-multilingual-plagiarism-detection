"""
Typed Application Configuration using Pydantic Settings
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_repo_root() -> Path:
    config_file = Path(__file__).resolve()
    for parent in config_file.parents:
        if (parent / "apps").exists() and (parent / "storage").exists():
            return parent
    return config_file.parents[4] if len(config_file.parents) > 4 else Path.cwd()


class Settings(BaseSettings):
    """
    Central application configuration loaded from environment variables and .env files.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # General App Settings
    APP_NAME: str = "Hybrid Multilingual Plagiarism Detection Platform"
    APP_VERSION: str = "1.0.0"
    SERVICE_NAME: str = "plagiarism-backend"
    ENVIRONMENT: str = Field(default="development", description="development | test | testing | staging | production")
    DEBUG: bool = Field(default=False, description="Enable debug mode (disables in production)")

    HOST: str = Field(default="0.0.0.0", description="API server bind host")
    PORT: int = Field(default=8000, description="API server bind port")

    # API Routing
    API_V1_PREFIX: str = "/api/v1"

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS requests")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database Configuration (PostgreSQL + pgvector)
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: Optional[str] = None

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/plagiarism_platform",
        description="SQLAlchemy asyncpg database connection string"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Database connection pool max overflow")

    @property
    def database_url(self) -> str:
        """Returns the formatted asyncpg database URL."""
        if self.POSTGRES_USER and self.POSTGRES_HOST and self.POSTGRES_DB:
            pwd = f":{self.POSTGRES_PASSWORD}" if self.POSTGRES_PASSWORD else ""
            return f"postgresql+asyncpg://{self.POSTGRES_USER}{pwd}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return self.DATABASE_URL

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and RQ background jobs"
    )
    WORKER_QUEUE_NAME: str = Field(default="default", description="Default RQ queue name")

    # Security & JWT Configuration
    JWT_SECRET_KEY: str = Field(
        default="insecure-dev-secret-key-change-in-production-minimum-32-chars",
        description="HMAC secret key for JWT token signing"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expiration in minutes")

    # Storage Configuration (Private Uploads & Artifacts)
    STORAGE_ROOT_DIR: Path = Field(
        default=Path("./storage"),
        description="Root directory for private uploads and generated reports"
    )
    APP_RUNTIME_MODE: str = Field(
        default="local",
        description="Runtime mode: 'local' (SQLite + local executor) or 'production' (PostgreSQL + Redis RQ)"
    )
    LOCAL_PRIVATE_STORAGE_ROOT: Path = Field(
        default=Path("./storage/private"),
        description="Private storage directory for uploaded documents (outside static web paths)"
    )
    LOCAL_SQLITE_PATH: Path = Field(
        default=Path("./storage/local_metadata.db"),
        description="SQLite database path for local metadata persistence"
    )
    MAX_UPLOAD_SIZE_BYTES: int = Field(
        default=30 * 1024 * 1024,
        description="Maximum file upload size in bytes (30 MiB matching OpenAPI contract)"
    )

    @field_validator("STORAGE_ROOT_DIR", "LOCAL_PRIVATE_STORAGE_ROOT", "LOCAL_SQLITE_PATH", mode="before")
    @classmethod
    def resolve_storage_paths(cls, v):
        if v is None:
            return v
        p = Path(v)
        if p.is_absolute():
            return p
        root = _find_repo_root()
        return (root / p).resolve()

    # Phase 4 Semantic AI Model Settings
    SEMANTIC_MODEL_NAME: str = Field(
        default="intfloat/multilingual-e5-small",
        description="HuggingFace model ID for multilingual embeddings"
    )
    SEMANTIC_MODEL_REVISION: str = Field(
        default="614241f622f53c4eeff9890bdc4f31cfecc418b3",
        description="Pinned model revision for deterministic reproducibility"
    )
    SEMANTIC_MODEL_CACHE_DIR: Path = Field(
        default=Path("./storage/model_cache"),
        description="Private local cache directory for model weights"
    )

    @field_validator("SEMANTIC_MODEL_CACHE_DIR", mode="before")
    @classmethod
    def resolve_model_cache_dir(cls, v):
        # 1. If explicit env var or absolute path provided and exists, honor it
        if v is not None and str(v).strip():
            p = Path(v)
            if p.is_absolute() and p.exists():
                return p
        # 2. Check persistent Windows LOCALAPPDATA directory outside OneDrive
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            appdata_cache = Path(local_app_data) / "plagiarism_engine" / "model_cache"
            if (appdata_cache / "models--intfloat--multilingual-e5-small").exists():
                return appdata_cache
        # 3. Check canonical repo root storage
        root = _find_repo_root()
        root_cache = root / "storage" / "model_cache"
        if (root_cache / "models--intfloat--multilingual-e5-small").exists():
            return root_cache
        # 4. Fallback
        if v is not None:
            p = Path(v)
            return (root / p).resolve() if not p.is_absolute() else p
        return root_cache
    SEMANTIC_EMBEDDING_DIM: int = Field(
        default=384,
        description="Dense vector dimension for multilingual-e5-small"
    )
    SEMANTIC_MAX_SEQ_LENGTH: int = Field(
        default=512,
        description="Max token sequence length for tokenizer and encoder"
    )
    SEMANTIC_DEVICE: str = Field(
        default="auto",
        description="'auto' (detect CUDA, fallback CPU), 'cuda', or 'cpu'"
    )
    SEMANTIC_PARAPHRASE_THRESHOLD: float = Field(
        default=0.82,
        description="Minimum cosine similarity for same-language paraphrase candidate"
    )
    SEMANTIC_TRANSLATION_THRESHOLD: float = Field(
        default=0.80,
        description="Minimum cosine similarity for cross-language translation candidate"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT.lower() in ("test", "testing")

    @model_validator(mode="after")
    def validate_production_readiness(self) -> "Settings":
        """Enforces security rules for production environments."""
        if self.is_production:
            if self.DEBUG:
                raise ValueError("DEBUG must not be enabled in production environment")
            if len(self.JWT_SECRET_KEY) < 32 or "insecure" in self.JWT_SECRET_KEY.lower():
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
        return self

    def __repr__(self) -> str:
        """Custom representation masking sensitive secrets."""
        redacted = {}
        for k, v in self.__dict__.items():
            if any(term in k.lower() for term in ("secret", "password", "key", "token")):
                redacted[k] = "******"
            else:
                redacted[k] = v
        return f"Settings({redacted})"


@lru_cache()
def get_settings() -> Settings:
    """Returns cached application settings instance."""
    return Settings()
