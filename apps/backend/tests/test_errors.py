"""
Unit Tests for Error Handling and RFC 7807 ErrorEnvelope Serializer
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from plagiarism.core.errors import (
    AppError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
    ValidationError,
    ErrorEnvelope,
    ErrorBody,
    create_error_response,
    app_error_handler,
)


def test_error_envelope_structure():
    """Verify ErrorEnvelope adheres to openapi.yaml schema."""
    body = ErrorBody(
        code="TEST_ERROR",
        message="Detailed explanation of error",
        status=400,
        request_id="test-req-1234",
        details=[{"field": "document_id", "issue": "UUID required"}]
    )
    envelope = ErrorEnvelope(error=body)
    data = envelope.model_dump(exclude_none=True)

    assert "error" in data
    assert data["error"]["code"] == "TEST_ERROR"
    assert data["error"]["status"] == 400
    assert data["error"]["request_id"] == "test-req-1234"
    assert len(data["error"]["details"]) == 1


def test_domain_exception_defaults():
    """Verify HTTP status codes and default error codes across exception types."""
    not_found = NotFoundError("Item not found")
    assert not_found.status_code == 404
    assert not_found.code == "NOT_FOUND"

    unauthorized = UnauthorizedError()
    assert unauthorized.status_code == 401
    assert unauthorized.code == "AUTH_UNAUTHORIZED"

    forbidden = ForbiddenError()
    assert forbidden.status_code == 403
    assert forbidden.code == "AUTH_FORBIDDEN"

    conflict = ConflictError()
    assert conflict.status_code == 409
    assert conflict.code == "CONFLICT"

    val_error = ValidationError("Validation failed", details=[{"field": "x", "issue": "missing"}])
    assert val_error.status_code == 422
    assert val_error.code == "VALIDATION_ERROR"
    assert len(val_error.details) == 1


def test_exception_handler_middleware():
    """Verify FastAPI application exception handler converts AppError into RFC 7807 response."""
    test_app = FastAPI()
    test_app.add_exception_handler(AppError, app_error_handler)

    @test_app.get("/trigger-error")
    def trigger():
        raise NotFoundError("The document record 1234 does not exist")

    client = TestClient(test_app)
    response = client.get("/trigger-error")

    assert response.status_code == 404
    payload = response.json()
    assert "error" in payload
    assert payload["error"]["code"] == "NOT_FOUND"
    assert payload["error"]["message"] == "The document record 1234 does not exist"
    assert payload["error"]["status"] == 404
