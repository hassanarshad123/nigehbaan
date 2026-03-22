"""Tests for the /health endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_returns_200():
    """GET /health should return HTTP 200."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_response_has_expected_keys():
    """Health response must contain 'status' and 'version' keys."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        data = resp.json()
        assert "status" in data, "Response missing 'status' key"
        assert "version" in data, "Response missing 'version' key"
        assert data["status"] == "healthy"
        assert isinstance(data["version"], str)
