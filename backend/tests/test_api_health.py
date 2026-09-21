"""
API integration tests for FinGuard AI — health endpoint only.

These tests use FastAPI's TestClient (Starlette's built-in ASGI test runner)
and do NOT require a live database or Gemini key.

The settings module requires DATABASE_URL and GEMINI_API_KEY at import time.
We set them as environment variables before the app is imported to satisfy
pydantic-settings validation without real credentials.
"""

import os

# Provide fake env vars BEFORE the app module is imported so pydantic-settings
# does not raise ValidationError during collection.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("GEMINI_API_KEY", "test_key_placeholder")

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


def test_health_endpoint_returns_200():
    """GET /health must return HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_status_is_ok():
    """GET /health JSON must contain status == 'ok'."""
    response = client.get("/health")
    data = response.json()
    assert data.get("status") == "ok"


def test_health_returns_version():
    """GET /health JSON must include a 'version' key."""
    response = client.get("/health")
    data = response.json()
    assert "version" in data


def test_health_version_is_string():
    """The version value must be a non-empty string."""
    response = client.get("/health")
    version = response.json().get("version")
    assert isinstance(version, str)
    assert len(version) > 0


def test_health_content_type_is_json():
    """Response Content-Type should be application/json."""
    response = client.get("/health")
    assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# 404 handler
# ---------------------------------------------------------------------------


def test_unknown_route_returns_404():
    """A request to a non-existent path should return 404."""
    response = client.get("/this-path-does-not-exist")
    assert response.status_code == 404


def test_unknown_route_json_body():
    """The 404 response body must contain an 'error' key."""
    response = client.get("/this-path-does-not-exist")
    data = response.json()
    assert "error" in data


# ---------------------------------------------------------------------------
# Method not allowed
# ---------------------------------------------------------------------------


def test_health_post_not_allowed():
    """POST /health is not a registered route — should return 405 or 404."""
    response = client.post("/health")
    assert response.status_code in (404, 405)


# ---------------------------------------------------------------------------
# /api/v1/system/info
# ---------------------------------------------------------------------------


def test_system_info_endpoint():
    """GET /api/v1/system/info returns dataset metadata and data-as-of date."""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "data_as_of_date" in data
    assert "data_as_of_display" in data
    assert "dataset_type" in data
    assert "Synthetic demonstration dataset" in data["dataset_type"]
    assert "record_counts" in data


def test_forecast_comparison_endpoint():
    """GET /api/v1/forecast/comparison returns multi-model benchmark results."""
    response = client.get("/api/v1/forecast/comparison")
    assert response.status_code == 200
    data = response.json()
    assert "champion_model" in data
    assert "benchmark_table" in data
    assert len(data["benchmark_table"]) >= 4


