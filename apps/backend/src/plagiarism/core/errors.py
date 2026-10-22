"""
Canonical Error Handling and RFC 7807 Problem Serialization
Adheres to contracts/openapi.yaml ErrorEnvelope schema
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: str | None = None
    issue: str
    location: str | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    status: int
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    request_id: str | None = None
    details: list[dict[str, Any]] | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class AppError(Exception):
    """Base application exception for standardized error envelopes."""
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: list[dict[str, Any]] | None = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


class NotFoundError(AppError):
    def __init__(self, message: str = "Requested resource not found", code: str = "NOT_FOUND"):
        super().__init__(code=code, message=message, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required or invalid token", code: str = "AUTH_UNAUTHORIZED"):
        super().__init__(code=code, message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Insufficient permissions to access resource", code: str = "AUTH_FORBIDDEN"):
        super().__init__(code=code, message=message, status_code=status.HTTP_403_FORBIDDEN)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict detected", code: str = "CONFLICT"):
        super().__init__(code=code, message=message, status_code=status.HTTP_409_CONFLICT)


class ValidationError(AppError):
    def __init__(self, message: str = "Invalid request payload", details: list[dict[str, Any]] | None = None):
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)


class BadRequestError(AppError):
    def __init__(self, message: str = "Bad request", code: str = "BAD_REQUEST", details: list[dict[str, Any]] | None = None):
        super().__init__(code=code, message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class PayloadTooLargeError(AppError):
    def __init__(self, message: str = "File or request payload exceeds allowed limit", code: str = "PAYLOAD_TOO_LARGE"):
        super().__init__(code=code, message=message, status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)


class UnsupportedMediaTypeError(AppError):
    def __init__(self, message: str = "Unsupported media type", code: str = "UNSUPPORTED_MEDIA_TYPE"):
        super().__init__(code=code, message=message, status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str | None = None,
    details: list[dict[str, Any]] | None = None
) -> JSONResponse:
    """Builds an RFC 7807 compliant JSONResponse matching openapi.yaml ErrorEnvelope."""
    body = ErrorBody(
        code=code,
        message=message,
        status=status_code,
        timestamp=datetime.now(UTC).isoformat(),
        request_id=request_id,
        details=details
    )
    envelope = ErrorEnvelope(error=body)
    return JSONResponse(status_code=status_code, content=envelope.model_dump(exclude_none=True))


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """FastAPI exception handler for application domain exceptions."""
    request_id = getattr(request.state, "request_id", None)
    return create_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        request_id=request_id,
        details=exc.details
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI fallback handler for unexpected unhandled errors (hides internal stack trace)."""
    request_id = getattr(request.state, "request_id", None)
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred. Please contact system support.",
        request_id=request_id
    )
