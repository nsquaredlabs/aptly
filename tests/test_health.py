"""Tests for health check endpoint."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.mark.asyncio
async def test_health_check_healthy(client, mock_supabase):
    """Health check returns healthy when all services are up."""
    mock_table = mock_supabase.table.return_value
    mock_table.execute.return_value = MagicMock(data=[{"id": "test"}])

    with patch("src.main.redis") as mock_redis_module:
        mock_redis = AsyncMock()
        mock_redis_module.from_url.return_value = mock_redis
        mock_redis.ping = AsyncMock()
        mock_redis.close = AsyncMock()

        response = await client.get("/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["redis"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check_database_error(client, mock_supabase):
    """Health check shows database error when DB is down."""
    mock_table = mock_supabase.table.return_value
    mock_table.execute.side_effect = Exception("Database error")

    with patch("src.main.redis") as mock_redis_module:
        mock_redis = AsyncMock()
        mock_redis_module.from_url.return_value = mock_redis
        mock_redis.ping = AsyncMock()
        mock_redis.close = AsyncMock()

        response = await client.get("/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["database"] == "error"
    assert data["checks"]["redis"] == "ok"


@pytest.mark.asyncio
async def test_health_check_redis_error(client, mock_supabase):
    """Health check shows Redis error when Redis is down."""
    mock_table = mock_supabase.table.return_value
    mock_table.execute.return_value = MagicMock(data=[{"id": "test"}])

    with patch("src.main.redis") as mock_redis_module:
        mock_redis = AsyncMock()
        mock_redis_module.from_url.return_value = mock_redis
        mock_redis.ping.side_effect = Exception("Redis error")
        mock_redis.close = AsyncMock()

        response = await client.get("/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["redis"] == "error"


@pytest.mark.asyncio
async def test_health_check_no_auth_required(client, mock_supabase):
    """Health check does not require authentication."""
    mock_table = mock_supabase.table.return_value
    mock_table.execute.return_value = MagicMock(data=[{"id": "test"}])

    with patch("src.main.redis") as mock_redis_module:
        mock_redis = AsyncMock()
        mock_redis_module.from_url.return_value = mock_redis
        mock_redis.ping = AsyncMock()
        mock_redis.close = AsyncMock()

        # No Authorization header
        response = await client.get("/v1/health")

    # Should still succeed without auth
    assert response.status_code == 200
