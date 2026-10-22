"""
Main Application Entry Point — FastAPI Server
Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System
"""

import logging
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from plagiarism.api.v1.health import get_health_status
from plagiarism.api.v1.router import api_v1_router
from plagiarism.core.config import get_settings
from plagiarism.core.errors import (
    AppError,
    app_error_handler,
    create_error_response,
    unhandled_exception_handler,
)
from plagiarism.core.logging import setup_logging
from plagiarism.db.session import engine
from plagiarism.domain.models import HealthStatus
from plagiarism.jobs.queue import close_redis_connection

logger = logging.getLogger("plagiarism.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager handling startup and shutdown hooks."""
    settings = get_settings()
    setup_logging(level=settings.LOG_LEVEL, service_name=settings.SERVICE_NAME)
    logger.info("Initializing Plagiarism Detection Backend API", extra={"version": settings.APP_VERSION, "env": settings.ENVIRONMENT})
    yield
    logger.info("Shutting down Plagiarism Detection Backend API: releasing resources")
    await engine.dispose()
    await close_redis_connection()


def create_application() -> FastAPI:
    """Factory creating and configuring the primary FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title="Hybrid AI-Powered Multilingual Plagiarism Detection API",
        description="Production REST API for multilingual plagiarism detection across English, Hindi, and Telugu.",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure Cross-Origin Resource Sharing (CORS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Request ID Correlation and Latency Middleware
    @app.middleware("http")
    async def correlation_and_metrics_middleware(request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()

        response: Response = await call_next(request)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(latency_ms)
        return response

    # Global Exception Handlers adhering to RFC 7807 ErrorEnvelope
    app.add_exception_handler(AppError, app_error_handler)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> Response:
        request_id = getattr(request.state, "request_id", None)
        error_details = []
        for err in exc.errors():
            loc = " -> ".join(str(item) for item in err.get("loc", []))
            error_details.append({
                "field": loc,
                "issue": err.get("msg", "Invalid value"),
                "type": err.get("type", "value_error"),
            })
        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Request validation failed. Inspect details for invalid parameters.",
            request_id=request_id,
            details=error_details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> Response:
        request_id = getattr(request.state, "request_id", None)
        code_map = {
            401: "AUTH_UNAUTHORIZED",
            403: "AUTH_FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            429: "RATE_LIMITED",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        return create_error_response(
            status_code=exc.status_code,
            code=code,
            message=str(exc.detail),
            request_id=request_id,
        )

    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Direct Health Probes for Container Orchestrators
    @app.get(
        "/health",
        response_model=HealthStatus,
        status_code=status.HTTP_200_OK,
        summary="Root Health Probe",
        tags=["System"],
        include_in_schema=False,
    )
    async def root_health_probe() -> HealthStatus:
        return await get_health_status()

    # Informational Service Index
    @app.get("/", tags=["System"], summary="API Root Information")
    async def root_info() -> dict[str, Any]:
        return {
            "name": "Hybrid AI-Powered Multilingual Plagiarism Detection API",
            "version": settings.APP_VERSION,
            "status": "operational",
            "documentation": "/docs",
            "health": "/api/v1/health",
        }

    # Mount API v1 Routers
    app.include_router(api_v1_router)

    return app


app = create_application()
