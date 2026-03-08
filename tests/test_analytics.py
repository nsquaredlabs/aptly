"""Tests for analytics endpoints."""

import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import TEST_API_SECRET


@pytest.mark.asyncio
async def test_analytics_usage_endpoint(client):
    """GET /v1/analytics/usage returns usage summary."""
    usage_response = {
        "summary": {
            "total_requests": 4,
            "total_tokens": 1125,
            "total_cost_usd": 0.05,
            "avg_latency_ms": 575,
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
        },
        "time_series": [
            {"date": "2026-01-15", "requests": 1, "tokens_input": 100, "tokens_output": 200, "cost_usd": 0.01, "avg_latency_ms": 500},
        ],
    }

    with patch("src.main.analytics_service") as mock_svc:
        mock_svc.get_usage_summary = AsyncMock(return_value=usage_response)

        response = await client.get(
            "/v1/analytics/usage",
            headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
            params={"start_date": "2026-01-01", "end_date": "2026-01-31", "granularity": "day"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_requests"] == 4
    mock_svc.get_usage_summary.assert_called_once()


@pytest.mark.asyncio
async def test_analytics_usage_invalid_granularity(client):
    """GET /v1/analytics/usage rejects invalid granularity."""
    response = await client.get(
        "/v1/analytics/usage",
        headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
        params={"granularity": "hour"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_analytics_models_endpoint(client):
    """GET /v1/analytics/models returns model breakdown."""
    models_response = {
        "models": [
            {
                "model": "gpt-4", "provider": "openai", "requests": 3,
                "tokens_input": 300, "tokens_output": 375, "cost_usd": 0.04,
                "avg_latency_ms": 500, "percentage_of_requests": 75.0,
            },
        ],
        "period_start": "2026-01-01",
        "period_end": "2026-01-31",
    }

    with patch("src.main.analytics_service") as mock_svc:
        mock_svc.get_model_breakdown = AsyncMock(return_value=models_response)

        response = await client.get(
            "/v1/analytics/models",
            headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
        )

    assert response.status_code == 200
    assert len(response.json()["models"]) == 1


@pytest.mark.asyncio
async def test_analytics_pii_endpoint(client):
    """GET /v1/analytics/pii returns PII statistics."""
    pii_response = {
        "summary": {
            "requests_with_input_pii": 2,
            "requests_with_response_pii": 1,
            "total_requests": 4,
            "input_pii_rate": 50.0,
            "response_pii_rate": 25.0,
        },
        "entity_types": [
            {"type": "PERSON", "input_count": 2, "response_count": 0, "total_count": 2},
        ],
        "time_series": [
            {"date": "2026-01-15", "requests_with_pii": 1, "total_requests": 1, "pii_rate": 100.0},
        ],
        "period_start": "2026-01-01",
        "period_end": "2026-01-31",
    }

    with patch("src.main.analytics_service") as mock_svc:
        mock_svc.get_pii_stats = AsyncMock(return_value=pii_response)

        response = await client.get(
            "/v1/analytics/pii",
            headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
        )

    assert response.status_code == 200
    assert response.json()["summary"]["input_pii_rate"] == 50.0


@pytest.mark.asyncio
async def test_analytics_export_csv(client):
    """GET /v1/analytics/export returns valid CSV."""
    export_rows = [
        {"date": "2026-01-15", "requests": 1, "tokens_input": 100, "tokens_output": 200, "cost_usd": 0.01, "avg_latency_ms": 500, "pii_detected_count": 1, "top_model": "gpt-4"},
    ]

    with patch("src.main.analytics_service") as mock_svc:
        mock_svc.get_export_data = AsyncMock(return_value=export_rows)

        response = await client.get(
            "/v1/analytics/export",
            headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
            params={"start_date": "2026-01-01", "end_date": "2026-01-31", "format": "csv"},
        )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_analytics_export_json(client):
    """GET /v1/analytics/export returns valid JSON when format=json."""
    export_rows = [
        {"date": "2026-01-15", "requests": 1, "tokens_input": 100, "tokens_output": 200, "cost_usd": 0.01, "avg_latency_ms": 500, "pii_detected_count": 1, "top_model": "gpt-4"},
    ]

    with patch("src.main.analytics_service") as mock_svc:
        mock_svc.get_export_data = AsyncMock(return_value=export_rows)

        response = await client.get(
            "/v1/analytics/export",
            headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
            params={"start_date": "2026-01-01", "end_date": "2026-01-31", "format": "json"},
        )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_analytics_export_missing_dates(client):
    """GET /v1/analytics/export returns 422 when required dates are missing."""
    response = await client.get(
        "/v1/analytics/export",
        headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analytics_export_invalid_format(client):
    """GET /v1/analytics/export returns 400 for unsupported format."""
    response = await client.get(
        "/v1/analytics/export",
        headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
        params={"start_date": "2026-01-01", "end_date": "2026-01-31", "format": "xml"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_analytics_unauthorized(client):
    """All analytics endpoints return 401 without authentication."""
    for path in ["/v1/analytics/usage", "/v1/analytics/models", "/v1/analytics/users", "/v1/analytics/pii"]:
        response = await client.get(path)
        assert response.status_code == 401, f"Expected 401 for {path}"
