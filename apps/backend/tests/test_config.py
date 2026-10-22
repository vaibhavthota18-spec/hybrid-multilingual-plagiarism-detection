"""
Unit Tests for Configuration, Environment, and Production Guardrails
"""

import os
import pytest
from pydantic import ValidationError
from plagiarism.core.config import Settings, get_settings


def test_default_settings():
    """Verify default development configuration loads successfully."""
    settings = get_settings()
    assert settings.APP_NAME == "Hybrid Multilingual Plagiarism Detection Platform"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.POSTGRES_PORT == 5432
    assert settings.REDIS_PORT == 6379


def test_database_url_formatting():
    """Verify async PostgreSQL connection URL is constructed with asyncpg driver."""
    settings = Settings(
        POSTGRES_USER="test_usr",
        POSTGRES_PASSWORD="test_password_123",
        POSTGRES_HOST="db.internal",
        POSTGRES_PORT=5433,
        POSTGRES_DB="test_db",
        JWT_SECRET_KEY="a" * 32,
    )
    expected_url = "postgresql+asyncpg://test_usr:test_password_123@db.internal:5433/test_db"
    assert settings.database_url == expected_url


def test_cors_origins_parsing():
    """Verify CORS origins parses stringified JSON or comma-separated domains."""
    settings = Settings(
        CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"],
        JWT_SECRET_KEY="a" * 32,
    )
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://localhost:5173" in settings.CORS_ORIGINS


def test_production_guardrail_weak_secret():
    """Verify production mode rejects short or insecure JWT secret keys."""
    with pytest.raises(ValueError, match="JWT_SECRET_KEY must be at least 32 characters"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="too_short_secret",
            DEBUG=False,
        )


def test_production_guardrail_debug_mode():
    """Verify production mode strictly forbids enabling DEBUG mode."""
    with pytest.raises(ValueError, match="DEBUG must not be enabled in production"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="a" * 32,
            DEBUG=True,
        )


def test_secret_string_masking():
    """Verify raw JWT secret keys and passwords are never exposed in loggable string representations."""
    settings = Settings(
        JWT_SECRET_KEY="super_sensitive_key_value_that_must_not_leak",
        POSTGRES_PASSWORD="sensitive_db_password",
    )
    repr_str = repr(settings)
    assert "super_sensitive_key_value_that_must_not_leak" not in repr_str
    assert "sensitive_db_password" not in repr_str
