"""Tests for audit log endpoints."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone, timedelta

from tests.conftest import (
    TEST_CUSTOMER,
    TEST_API_KEY,
    TEST_API_KEY_DATA,
    setup_auth_mocks,
)


@pytest.mark.asyncio
async def test_query_logs(client, mock_supabase):
    """Can query audit logs with pagination."""
    setup_auth_mocks(mock_supabase)

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
                    {
                        "id": "log_2",
                        "user_id": "user_456",
                        "provider": "anthropic",
                        "model": "claude-3-opus",
                        "tokens_input": 50,
                        "tokens_output": 100,
                        "latency_ms": 300,
                        "cost_usd": 0.005,
                        "pii_detected": [],
                        "compliance_framework": None,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                ],
                2,  # total count
            )
        )

        response = await client.get(
            "/v1/logs",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["logs"]) == 2
    assert data["pagination"]["total"] == 2
    assert data["pagination"]["page"] == 1


@pytest.mark.asyncio
async def test_query_logs_with_filters(client, mock_supabase):
    """Can filter logs by date, user, and model."""
    setup_auth_mocks(mock_supabase)

    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.query_logs = AsyncMock(return_value=([], 0))

        response = await client.get(
            "/v1/logs",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "user_id": "user_123",
                "model": "gpt-4",
                "limit": 25,
                "page": 2,
            },
        )

    assert response.status_code == 200

    # Verify the audit logger was called with correct params
    mock_audit.query_logs.assert_called_once()
    call_kwargs = mock_audit.query_logs.call_args[1]
    assert call_kwargs["user_id"] == "user_123"
    assert call_kwargs["model"] == "gpt-4"
    assert call_kwargs["limit"] == 25
    assert call_kwargs["page"] == 2


@pytest.mark.asyncio
async def test_query_logs_empty(client, mock_supabase):
    """Returns empty list when no logs found."""
    setup_auth_mocks(mock_supabase)

    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.query_logs = AsyncMock(return_value=([], 0))

        response = await client.get(
            "/v1/logs",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["logs"]) == 0
    assert data["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_get_log_detail(client, mock_supabase):
    """Can get detailed audit log entry."""
    setup_auth_mocks(mock_supabase)

    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.get_log = AsyncMock(
            return_value={
                "id": "log_test123",
                "user_id": "user_123",
                "provider": "openai",
                "model": "gpt-4",
                "request_data": {
                    "messages": [{"role": "user", "content": "PERSON_A has diabetes."}]
                },
                "response_data": {"content": "I understand PERSON_A has..."},
                "tokens_input": 100,
                "tokens_output": 200,
                "latency_ms": 500,
                "cost_usd": 0.01,
                "pii_detected": [
                    {"type": "PERSON", "replacement": "PERSON_A", "confidence": 0.95}
                ],
                "compliance_framework": "HIPAA",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        response = await client.get(
            "/v1/logs/log_test123",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "log_test123"
    assert "request_data" in data
    assert "response_data" in data


@pytest.mark.asyncio
async def test_get_log_detail_not_found(client, mock_supabase):
    """Returns 404 for non-existent log."""
    setup_auth_mocks(mock_supabase)

    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.get_log = AsyncMock(return_value=None)

        response = await client.get(
            "/v1/logs/log_nonexistent",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_query_logs_unauthorized(client, mock_supabase):
    """Returns 401 without authentication."""
    response = await client.get("/v1/logs")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_audit_logger_creates_entry():
    """Audit logger creates entries correctly."""
    with patch("src.compliance.audit_logger.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = MagicMock(
            data=[{"id": "log_new123"}]
        )

        from src.compliance.audit_logger import AuditLogger, AuditLogEntry
        from decimal import Decimal

        logger = AuditLogger()

        entry = AuditLogEntry(
            customer_id="cus_test123",
            provider="openai",
            model="gpt-4",
            request_data={"messages": [{"role": "user", "content": "Hello"}]},
            response_data={"content": "Hi there!"},
            user_id="user_123",
            pii_detected=[{"type": "PERSON"}],
            tokens_input=10,
            tokens_output=20,
            latency_ms=500,
            cost_usd=Decimal("0.001"),
            compliance_framework="HIPAA",
        )

        log_id = await logger.log(entry)

        assert log_id == "log_new123"
        mock_table.insert.assert_called_once()


@pytest.mark.asyncio
async def test_audit_logger_query_logs():
    """Audit logger queries logs correctly."""
    with patch("src.compliance.audit_logger.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.range.return_value = mock_table
        mock_table.execute.return_value = MagicMock(
            data=[{"id": "log_1"}, {"id": "log_2"}],
            count=2,
        )

        from src.compliance.audit_logger import AuditLogger

        logger = AuditLogger()

        logs, total = await logger.query_logs(
            customer_id="cus_test123",
            start_date=datetime.now(timezone.utc) - timedelta(days=7),
            end_date=datetime.now(timezone.utc),
            limit=50,
            page=1,
        )

        assert len(logs) == 2
        assert total == 2


@pytest.mark.asyncio
async def test_audit_logger_get_single_log():
    """Audit logger retrieves single log correctly."""
    with patch("src.compliance.audit_logger.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.single.return_value = mock_table
        mock_table.execute.return_value = MagicMock(
            data={"id": "log_test123", "provider": "openai"}
        )

        from src.compliance.audit_logger import AuditLogger

        logger = AuditLogger()

        log = await logger.get_log("cus_test123", "log_test123")

        assert log is not None
        assert log["id"] == "log_test123"


@pytest.mark.asyncio
async def test_audit_logger_get_usage_stats():
    """Audit logger calculates usage stats correctly."""
    with patch("src.compliance.audit_logger.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.execute.return_value = MagicMock(
            data=[
                {"id": "1", "tokens_input": 100, "tokens_output": 200},
                {"id": "2", "tokens_input": 50, "tokens_output": 100},
            ],
            count=2,
        )

        from src.compliance.audit_logger import AuditLogger

        logger = AuditLogger()

        now = datetime.now(timezone.utc)
        stats = await logger.get_usage_stats(
            "cus_test123",
            now - timedelta(days=30),
            now,
        )

        assert stats["requests"] == 2
        assert stats["tokens"] == 450  # 100+200+50+100
