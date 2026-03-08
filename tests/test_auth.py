"""Tests for authentication - API SECRET VALIDATION."""

import pytest

from tests.conftest import TEST_API_SECRET


@pytest.mark.asyncio
async def test_api_secret_valid(client):
    """Valid API secret authenticates successfully."""
    response = await client.get(
        "/v1/logs",
        headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
    )
    # Should not be 401
    assert response.status_code != 401


@pytest.mark.asyncio
async def test_api_secret_missing(client):
    """Missing authorization returns 401."""
    response = await client.get("/v1/logs")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_api_secret_invalid(client):
    """Invalid API secret returns 401."""
    response = await client.get(
        "/v1/logs",
        headers={"Authorization": "Bearer wrong-secret"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_api_secret_bearer_format_required(client):
    """API secret must use Bearer format."""
    response = await client.get(
        "/v1/logs",
        headers={"Authorization": TEST_API_SECRET},
    )
    assert response.status_code == 401
    data = response.json()
    assert "Bearer" in data["detail"]["error"]["message"]
