"""Tests for audit log endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from tests.conftest import TEST_API_SECRET


@pytest.mark.asyncio
async def test_query_logs(client):
    """Can query audit logs with pagination."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.query_logs = AsyncMock(
            return_value=(
                [
                    {
                        "id": "log_1",
                        "user_id": "user_123",
                        "provider": "openai",
                        "model": "gpt-4",
                        "tokens_input": 100,
                        "tokens_output": 200,
                        "latency_ms": 500,
                        "cost_usd": 0.01,
                        "pii_detected": [{"type": "PERSON"}],
                        "compliance_framework": "HIPAA",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                ],
                1,
            )
        )

        response = await client.get(
            "/v1/logs",
            headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["logs"]) == 1
    assert data["pagination"]["total"] == 1


@pytest.mark.asyncio
async def test_query_logs_empty(client):
    """Returns empty list when no logs found."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.query_logs = AsyncMock(return_value=([], 0))

        response = await client.get(
            "/v1/logs",
            headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["logs"]) == 0
    assert data["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_get_log_detail(client):
    """Can get detailed audit log entry."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.get_log = AsyncMock(
            return_value={
                "id": "log_test123",
                "user_id": "user_123",
                "provider": "openai",
                "model": "gpt-4",
                "request_data": {"messages": [{"role": "user", "content": "PERSON_A has diabetes."}]},
                "response_data": {"content": "I understand PERSON_A has..."},
                "tokens_input": 100,
                "tokens_output": 200,
                "latency_ms": 500,
                "cost_usd": 0.01,
                "pii_detected": [{"type": "PERSON", "replacement": "PERSON_A", "confidence": 0.95}],
                "response_pii_detected": [],
                "compliance_framework": "HIPAA",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        response = await client.get(
            "/v1/logs/log_test123",
            headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "log_test123"
    assert "request_data" in data


@pytest.mark.asyncio
async def test_get_log_detail_not_found(client):
    """Returns 404 for non-existent log."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.get_log = AsyncMock(return_value=None)

        response = await client.get(
            "/v1/logs/log_nonexistent",
            headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_query_logs_unauthorized(client):
    """Returns 401 without authentication."""
    response = await client.get("/v1/logs")
    assert response.status_code == 401
