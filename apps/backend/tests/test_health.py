"""
Unit and Integration Tests for System Health Probe Conformance
Adheres to contracts/openapi.yaml /health endpoint schema
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from plagiarism.main import app
from plagiarism.domain.models import HealthStatus


@pytest.fixture
def client():
    return TestClient(app)


def test_health_status_model_validation():
    """Verify HealthStatus Pydantic model enforces required contract fields."""
    now_iso = datetime.utcnow().isoformat() + "Z"
    model = HealthStatus(
        status="healthy",
        timestamp=now_iso,
        database="connected",
        redis="connected",
        worker_pool="operational",
        version="1.0.0",
    )
    data = model.model_dump()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["redis"] == "connected"
    assert data["worker_pool"] == "operational"
    assert data["version"] == "1.0.0"


@patch("plagiarism.api.v1.health.check_db_health", new_callable=AsyncMock)
@patch("plagiarism.api.v1.health.check_redis_health", new_callable=AsyncMock)
def test_health_endpoint_healthy(mock_redis, mock_db, client):
    """Verify /api/v1/health returns HTTP 200 and healthy status when all dependencies are up."""
    mock_db.return_value = True
    mock_redis.return_value = True

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "healthy"
    assert payload["database"] == "connected"
    assert payload["redis"] == "connected"
    assert payload["worker_pool"] == "operational"
    assert "version" in payload
    assert "timestamp" in payload


@patch("plagiarism.api.v1.health.check_db_health", new_callable=AsyncMock)
@patch("plagiarism.api.v1.health.check_redis_health", new_callable=AsyncMock)
def test_health_endpoint_degraded_db(mock_redis, mock_db, client):
    """Verify /api/v1/health gracefully reports degraded when database is unreachable."""
    mock_db.return_value = False
    mock_redis.return_value = True

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "degraded"
    assert payload["database"] == "disconnected"
    assert payload["redis"] == "connected"


@patch("plagiarism.api.v1.health.check_db_health", new_callable=AsyncMock)
@patch("plagiarism.api.v1.health.check_redis_health", new_callable=AsyncMock)
def test_health_endpoint_degraded_redis(mock_redis, mock_db, client):
    """Verify /api/v1/health gracefully reports degraded when redis/worker is unreachable."""
    mock_db.return_value = True
    mock_redis.return_value = False

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "degraded"
    assert payload["database"] == "connected"
    assert payload["redis"] == "disconnected"
    assert payload["worker_pool"] == "degraded"


def test_root_health_route_alias(client):
    """Verify root /health route is available for load balancers and container healthchecks."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
