"""
Pytest Test Fixtures and Test Environment Configuration
"""

import os
from typing import Any

import pytest

# Ensure test environment variables are set before any application import
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["POSTGRES_DB"] = "plagiarism_test"
os.environ["POSTGRES_USER"] = "postgres_test"
os.environ["POSTGRES_PASSWORD"] = "test_postgres_password_12345"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["JWT_SECRET_KEY"] = "test_super_secure_jwt_secret_key_minimum_32_characters_long_for_security"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["STORAGE_ROOT"] = "./test_storage"


@pytest.fixture(scope="session")
def test_settings():
    """Provides cached application settings configured for test execution."""
    from plagiarism.core.config import get_settings
    return get_settings()


@pytest.fixture
def mock_user_student() -> dict[str, Any]:
    return {
        "sub": "00000000-0000-0000-0000-000000000001",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "email": "student@university.edu",
        "role": "STUDENT",
        "display_name": "Test Student",
    }


@pytest.fixture
def mock_user_faculty() -> dict[str, Any]:
    return {
        "sub": "00000000-0000-0000-0000-000000000002",
        "user_id": "00000000-0000-0000-0000-000000000002",
        "email": "faculty@university.edu",
        "role": "FACULTY",
        "display_name": "Test Professor",
    }


@pytest.fixture
def mock_user_admin() -> dict[str, Any]:
    return {
        "sub": "00000000-0000-0000-0000-000000000003",
        "user_id": "00000000-0000-0000-0000-000000000003",
        "email": "admin@university.edu",
        "role": "ADMIN",
        "display_name": "System Administrator",
    }


@pytest.fixture
def student_token(mock_user_student) -> str:
    from plagiarism.core.security import create_access_token
    return create_access_token(mock_user_student)


@pytest.fixture
def faculty_token(mock_user_faculty) -> str:
    from plagiarism.core.security import create_access_token
    return create_access_token(mock_user_faculty)


@pytest.fixture
def admin_token(mock_user_admin) -> str:
    from plagiarism.core.security import create_access_token
    return create_access_token(mock_user_admin)


@pytest.fixture
def student_auth_headers(student_token) -> dict[str, str]:
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture
def faculty_auth_headers(faculty_token) -> dict[str, str]:
    return {"Authorization": f"Bearer {faculty_token}"}


@pytest.fixture
def admin_auth_headers(admin_token) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}
