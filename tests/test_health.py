"""Tests for health check endpoint."""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_health_check_healthy(client):
    """Health check returns healthy when all services are up."""
    with patch("src.main.redis") as mock_redis_module:
        mock_redis = AsyncMock()
        mock_redis_module.from_url.return_value = mock_redis
        mock_redis.ping = AsyncMock()
        mock_redis.close = AsyncMock()

        response = await client.get("/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["checks"]["database"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check_no_auth_required(client):
    """Health check does not require authentication."""
    with patch("src.main.redis") as mock_redis_module:
        mock_redis = AsyncMock()
        mock_redis_module.from_url.return_value = mock_redis
        mock_redis.ping = AsyncMock()
        mock_redis.close = AsyncMock()

        response = await client.get("/v1/health")
    assert response.status_code == 200
