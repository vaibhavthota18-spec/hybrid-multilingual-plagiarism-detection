"""
Unit Tests for Security, JWT Cryptography, and Role-Based Access Control (RBAC)
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from plagiarism.core.errors import UnauthorizedError
from plagiarism.core.security import (
    UserPrincipal,
    create_access_token,
    decode_token,
)
from plagiarism.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_jwt_token_creation_and_decoding():
    """Verify standard JWT token creation and successful claims decoding."""
    payload = {
        "sub": "user-uuid-1234",
        "user_id": "user-uuid-1234",
        "email": "test@university.edu",
        "role": "FACULTY",
    }
    token = create_access_token(payload, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)

    principal = decode_token(token)
    assert isinstance(principal, UserPrincipal)
    assert principal.user_id == "user-uuid-1234"
    assert principal.email == "test@university.edu"
    assert principal.role == "FACULTY"


def test_jwt_token_expiration_rejection():
    """Verify expired JWT tokens are strictly rejected with UnauthorizedError."""
    payload = {
        "sub": "expired-user",
        "user_id": "expired-user",
        "role": "STUDENT",
    }
    # Create token already expired in the past
    token = create_access_token(payload, expires_delta=timedelta(seconds=-10))

    with pytest.raises(UnauthorizedError, match="Token has expired"):
        decode_token(token)


def test_jwt_invalid_signature_rejection():
    """Verify tokens signed with a different key are strictly rejected."""
    payload = {
        "sub": "tampered-user",
        "user_id": "tampered-user",
        "role": "ADMIN",
        "exp": datetime.now(UTC) + timedelta(minutes=10)
    }
    fraudulent_token = jwt.encode(payload, "fraudulent_foreign_secret_key_32_bytes_long", algorithm="HS256")

    with pytest.raises(UnauthorizedError, match="Invalid token signature"):
        decode_token(fraudulent_token)


def test_jwt_algorithm_pinning():
    """Verify tokens attempting algorithm tampering (e.g. 'none' algorithm) are rejected."""
    # Construct unsigned token with none algorithm
    tampered_token = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhdHRhY2tlciIsInVzZXJfaWQiOiJhdHRhY2tlciIsInJvbGUiOiJBRE1JTiJ9."

    with pytest.raises(UnauthorizedError):
        decode_token(tampered_token)


def test_auth_me_authenticated(client, student_token):
    """Verify GET /api/v1/auth/me returns current user identity when valid bearer provided."""
    headers = {"Authorization": f"Bearer {student_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "STUDENT"
    assert "user_id" in data


def test_auth_me_unauthenticated(client):
    """Verify GET /api/v1/auth/me rejects missing credentials with HTTP 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    payload = response.json()
    assert payload["error"]["code"] == "AUTH_UNAUTHORIZED"


def test_rbac_admin_probe_authorized(client, admin_token):
    """Verify ADMIN role accesses admin-protected endpoint successfully."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/auth/admin-probe", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "authorized"


def test_rbac_admin_probe_forbidden_for_student(client, student_token):
    """Verify STUDENT role is forbidden (HTTP 403) from admin-protected endpoint."""
    headers = {"Authorization": f"Bearer {student_token}"}
    response = client.get("/api/v1/auth/admin-probe", headers=headers)
    assert response.status_code == 403
    payload = response.json()
    assert payload["error"]["code"] == "AUTH_FORBIDDEN"
