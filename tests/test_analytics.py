"""Tests for customer analytics endpoints and AnalyticsService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from tests.conftest import TEST_API_KEY, setup_auth_mocks


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

SAMPLE_LOGS = [
    {
        "id": "log_1",
        "customer_id": "cus_test123",
        "user_id": "user_123",
        "provider": "openai",
        "model": "gpt-4",
        "tokens_input": 100,
        "tokens_output": 200,
        "latency_ms": 500,
        "cost_usd": "0.01",
        "pii_detected": [{"type": "PERSON", "replacement": "PERSON_A", "confidence": 0.95}],
        "response_pii_detected": [],
        "created_at": "2026-01-15T10:00:00+00:00",
    },
    {
        "id": "log_2",
        "customer_id": "cus_test123",
        "user_id": "user_123",
        "provider": "openai",
        "model": "gpt-4",
        "tokens_input": 150,
        "tokens_output": 100,
        "latency_ms": 600,
        "cost_usd": "0.02",
        "pii_detected": [],
        "response_pii_detected": [{"type": "EMAIL_ADDRESS", "replacement": "HASH_abc", "confidence": 0.9}],
        "created_at": "2026-01-16T12:00:00+00:00",
    },
    {
        "id": "log_3",
        "customer_id": "cus_test123",
        "user_id": "user_456",
        "provider": "anthropic",
        "model": "claude-3-sonnet",
        "tokens_input": 200,
        "tokens_output": 300,
        "latency_ms": 800,
        "cost_usd": "0.01",
        "pii_detected": [{"type": "PERSON", "replacement": "PERSON_B", "confidence": 0.88}],
        "response_pii_detected": [],
        "created_at": "2026-01-16T14:00:00+00:00",
    },
    {
        "id": "log_4",
        "customer_id": "cus_test123",
        "user_id": None,
        "provider": "openai",
        "model": "gpt-4",
        "tokens_input": 50,
        "tokens_output": 75,
        "latency_ms": 400,
        "cost_usd": "0.01",
        "pii_detected": [],
        "response_pii_detected": [],
        "created_at": "2026-01-17T09:00:00+00:00",
    },
]


def _mock_supabase_with_logs(logs: list[dict]):
    """Create a mock supabase that returns the given logs for any query."""
    mock_sb = MagicMock()
    mock_table = MagicMock()
    mock_sb.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.gte.return_value = mock_table
    mock_table.lte.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.execute.return_value = MagicMock(data=logs)
    return mock_sb


# ---------------------------------------------------------------------------
# Endpoint tests — patch analytics_service at the route level
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analytics_usage_endpoint(client, mock_supabase):
    """GET /v1/analytics/usage returns usage summary."""
    setup_auth_mocks(mock_supabase)

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
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
            params={"start_date": "2026-01-01", "end_date": "2026-01-31", "granularity": "day"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_requests"] == 4
    assert len(data["time_series"]) == 1
    mock_svc.get_usage_summary.assert_called_once()


@pytest.mark.asyncio
async def test_analytics_usage_invalid_granularity(client, mock_supabase):
    """GET /v1/analytics/usage rejects invalid granularity."""
    setup_auth_mocks(mock_supabase)

    response = await client.get(
        "/v1/analytics/usage",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        params={"granularity": "hour"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_analytics_models_endpoint(client, mock_supabase):
    """GET /v1/analytics/models returns model breakdown."""
    setup_auth_mocks(mock_supabase)

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
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        )

    assert response.status_code == 200
    assert len(response.json()["models"]) == 1


@pytest.mark.asyncio
async def test_analytics_users_endpoint(client, mock_supabase):
    """GET /v1/analytics/users returns user breakdown and passes limit."""
    setup_auth_mocks(mock_supabase)

    users_response = {
        "users": [
            {"user_id": "user_123", "requests": 2, "tokens_input": 250, "tokens_output": 300, "cost_usd": 0.03, "last_active": "2026-01-16T12:00:00+00:00"},
        ],
        "users_with_no_id": {"requests": 1, "tokens_input": 50, "tokens_output": 75, "cost_usd": 0.01},
        "total_unique_users": 2,
        "period_start": "2026-01-01",
        "period_end": "2026-01-31",
    }

    with patch("src.main.analytics_service") as mock_svc:
        mock_svc.get_user_breakdown = AsyncMock(return_value=users_response)

        response = await client.get(
            "/v1/analytics/users",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
            params={"limit": "10"},
        )

    assert response.status_code == 200
    assert response.json()["total_unique_users"] == 2
    assert mock_svc.get_user_breakdown.call_args[1]["limit"] == 10


@pytest.mark.asyncio
async def test_analytics_users_limit_clamped(client, mock_supabase):
    """GET /v1/analytics/users clamps limit to max 100."""
    setup_auth_mocks(mock_supabase)

    with patch("src.main.analytics_service") as mock_svc:
        mock_svc.get_user_breakdown = AsyncMock(return_value={
            "users": [], "users_with_no_id": {"requests": 0, "tokens_input": 0, "tokens_output": 0, "cost_usd": 0.0},
            "total_unique_users": 0, "period_start": "2026-01-01", "period_end": "2026-01-31",
        })

        response = await client.get(
            "/v1/analytics/users",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
            params={"limit": "500"},
        )

    assert response.status_code == 200
    assert mock_svc.get_user_breakdown.call_args[1]["limit"] == 100


@pytest.mark.asyncio
async def test_analytics_pii_endpoint(client, mock_supabase):
    """GET /v1/analytics/pii returns PII statistics."""
    setup_auth_mocks(mock_supabase)

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
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        )

    assert response.status_code == 200
    assert response.json()["summary"]["input_pii_rate"] == 50.0


@pytest.mark.asyncio
async def test_analytics_export_csv(client, mock_supabase):
    """GET /v1/analytics/export returns valid CSV with header and data rows."""
    setup_auth_mocks(mock_supabase)

    export_rows = [
        {"date": "2026-01-15", "requests": 1, "tokens_input": 100, "tokens_output": 200, "cost_usd": 0.01, "avg_latency_ms": 500, "pii_detected_count": 1, "top_model": "gpt-4"},
        {"date": "2026-01-16", "requests": 2, "tokens_input": 350, "tokens_output": 400, "cost_usd": 0.03, "avg_latency_ms": 700, "pii_detected_count": 2, "top_model": "gpt-4"},
    ]

    with patch("src.main.analytics_service") as mock_svc:
        mock_svc.get_export_data = AsyncMock(return_value=export_rows)

        response = await client.get(
            "/v1/analytics/export",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
            params={"start_date": "2026-01-01", "end_date": "2026-01-31", "format": "csv"},
        )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    lines = response.text.strip().split("\n")
    assert lines[0].startswith("date,")
    assert len(lines) == 3  # header + 2 data rows


@pytest.mark.asyncio
async def test_analytics_export_csv_empty(client, mock_supabase):
    """CSV export with no data still returns a header row."""
    setup_auth_mocks(mock_supabase)

    with patch("src.main.analytics_service") as mock_svc:
        mock_svc.get_export_data = AsyncMock(return_value=[])

        response = await client.get(
            "/v1/analytics/export",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        )

    assert response.status_code == 200
    lines = response.text.strip().split("\n")
    assert len(lines) == 1
    assert "date" in lines[0]


@pytest.mark.asyncio
async def test_analytics_export_json(client, mock_supabase):
    """GET /v1/analytics/export returns valid JSON when format=json."""
    setup_auth_mocks(mock_supabase)

    export_rows = [
        {"date": "2026-01-15", "requests": 1, "tokens_input": 100, "tokens_output": 200, "cost_usd": 0.01, "avg_latency_ms": 500, "pii_detected_count": 1, "top_model": "gpt-4"},
    ]

    with patch("src.main.analytics_service") as mock_svc:
        mock_svc.get_export_data = AsyncMock(return_value=export_rows)

        response = await client.get(
            "/v1/analytics/export",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
            params={"start_date": "2026-01-01", "end_date": "2026-01-31", "format": "json"},
        )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert response.json() == export_rows


@pytest.mark.asyncio
async def test_analytics_export_missing_dates(client, mock_supabase):
    """GET /v1/analytics/export returns 422 when required dates are missing."""
    setup_auth_mocks(mock_supabase)

    response = await client.get(
        "/v1/analytics/export",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analytics_export_invalid_format(client, mock_supabase):
    """GET /v1/analytics/export returns 400 for unsupported format."""
    setup_auth_mocks(mock_supabase)

    response = await client.get(
        "/v1/analytics/export",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        params={"start_date": "2026-01-01", "end_date": "2026-01-31", "format": "xml"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_analytics_export_include_filter(client, mock_supabase):
    """GET /v1/analytics/export passes include filter to service."""
    setup_auth_mocks(mock_supabase)

    with patch("src.main.analytics_service") as mock_svc:
        mock_svc.get_export_data = AsyncMock(return_value=[])

        response = await client.get(
            "/v1/analytics/export",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
            params={"start_date": "2026-01-01", "end_date": "2026-01-31", "include": "usage,pii"},
        )

    assert response.status_code == 200
    assert mock_svc.get_export_data.call_args[1]["include"] == ["usage", "pii"]


@pytest.mark.asyncio
async def test_analytics_unauthorized(client, mock_supabase):
    """All analytics endpoints return 401 without authentication."""
    for path in ["/v1/analytics/usage", "/v1/analytics/models", "/v1/analytics/users", "/v1/analytics/pii"]:
        response = await client.get(path)
        assert response.status_code == 401, f"Expected 401 for {path}"


# ---------------------------------------------------------------------------
# AnalyticsService unit tests — patch supabase directly
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analytics_service_usage_summary():
    """AnalyticsService correctly aggregates usage totals and time series."""
    with patch("src.analytics.supabase", _mock_supabase_with_logs(SAMPLE_LOGS)):
        from src.analytics import AnalyticsService

        svc = AnalyticsService()
        result = await svc.get_usage_summary(
            "cus_test123",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 31, tzinfo=timezone.utc),
            granularity="day",
        )

    assert result["summary"]["total_requests"] == 4
    # (100+200) + (150+100) + (200+300) + (50+75) = 1175
    assert result["summary"]["total_tokens"] == 1175
    # 0.01 + 0.02 + 0.01 + 0.01 = 0.05
    assert result["summary"]["total_cost_usd"] == 0.05
    # (500+600+800+400) / 4 = 575
    assert result["summary"]["avg_latency_ms"] == 575
    # 3 distinct days: Jan 15, 16, 17
    assert len(result["time_series"]) == 3
    assert result["time_series"][0]["date"] == "2026-01-15"
    assert result["time_series"][1]["date"] == "2026-01-16"
    assert result["time_series"][2]["date"] == "2026-01-17"


@pytest.mark.asyncio
async def test_analytics_usage_totals_match_timeseries():
    """Summary totals equal the sum of time_series values."""
    with patch("src.analytics.supabase", _mock_supabase_with_logs(SAMPLE_LOGS)):
        from src.analytics import AnalyticsService

        svc = AnalyticsService()
        result = await svc.get_usage_summary(
            "cus_test123",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 31, tzinfo=timezone.utc),
        )

    ts = result["time_series"]
    assert result["summary"]["total_requests"] == sum(p["requests"] for p in ts)
    assert result["summary"]["total_tokens"] == sum(p["tokens_input"] + p["tokens_output"] for p in ts)


@pytest.mark.asyncio
async def test_analytics_service_usage_weekly_granularity():
    """Weekly granularity buckets all sample logs into the same week."""
    with patch("src.analytics.supabase", _mock_supabase_with_logs(SAMPLE_LOGS)):
        from src.analytics import AnalyticsService

        svc = AnalyticsService()
        result = await svc.get_usage_summary(
            "cus_test123",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 31, tzinfo=timezone.utc),
            granularity="week",
        )

    # Jan 15 (Thu), 16 (Fri), 17 (Sat) → Monday Jan 12
    assert len(result["time_series"]) == 1
    assert result["time_series"][0]["date"] == "2026-01-12"
    assert result["time_series"][0]["requests"] == 4


@pytest.mark.asyncio
async def test_analytics_service_usage_monthly_granularity():
    """Monthly granularity buckets dates to the first of the month."""
    with patch("src.analytics.supabase", _mock_supabase_with_logs(SAMPLE_LOGS)):
        from src.analytics import AnalyticsService

        svc = AnalyticsService()
        result = await svc.get_usage_summary(
            "cus_test123",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 31, tzinfo=timezone.utc),
            granularity="month",
        )

    assert len(result["time_series"]) == 1
    assert result["time_series"][0]["date"] == "2026-01-01"
    assert result["time_series"][0]["requests"] == 4


@pytest.mark.asyncio
async def test_analytics_service_model_breakdown():
    """AnalyticsService groups by model+provider, sorted by request count."""
    with patch("src.analytics.supabase", _mock_supabase_with_logs(SAMPLE_LOGS)):
        from src.analytics import AnalyticsService

        svc = AnalyticsService()
        result = await svc.get_model_breakdown(
            "cus_test123",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 31, tzinfo=timezone.utc),
        )

    models = result["models"]
    assert len(models) == 2
    # gpt-4 has 3 requests (logs 1,2,4); claude-3-sonnet has 1 (log 3)
    assert models[0]["model"] == "gpt-4"
    assert models[0]["provider"] == "openai"
    assert models[0]["requests"] == 3
    assert models[0]["percentage_of_requests"] == 75.0
    assert models[1]["model"] == "claude-3-sonnet"
    assert models[1]["requests"] == 1
    assert models[1]["percentage_of_requests"] == 25.0


@pytest.mark.asyncio
async def test_analytics_service_user_breakdown():
    """AnalyticsService groups by user_id; None users go to users_with_no_id."""
    with patch("src.analytics.supabase", _mock_supabase_with_logs(SAMPLE_LOGS)):
        from src.analytics import AnalyticsService

        svc = AnalyticsService()
        result = await svc.get_user_breakdown(
            "cus_test123",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 31, tzinfo=timezone.utc),
        )

    assert result["total_unique_users"] == 2
    assert len(result["users"]) == 2
    # user_123 has 2 requests, user_456 has 1; sorted desc
    assert result["users"][0]["user_id"] == "user_123"
    assert result["users"][0]["requests"] == 2
    assert result["users"][1]["user_id"] == "user_456"
    assert result["users"][1]["requests"] == 1
    # log_4 has user_id=None
    assert result["users_with_no_id"]["requests"] == 1
    assert result["users_with_no_id"]["tokens_input"] == 50


@pytest.mark.asyncio
async def test_analytics_service_user_breakdown_limit():
    """User breakdown returns only top N users; total_unique_users is unaffected."""
    with patch("src.analytics.supabase", _mock_supabase_with_logs(SAMPLE_LOGS)):
        from src.analytics import AnalyticsService

        svc = AnalyticsService()
        result = await svc.get_user_breakdown(
            "cus_test123",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 31, tzinfo=timezone.utc),
            limit=1,
        )

    assert len(result["users"]) == 1
    assert result["total_unique_users"] == 2
    assert result["users"][0]["user_id"] == "user_123"


@pytest.mark.asyncio
async def test_analytics_service_pii_stats():
    """AnalyticsService correctly counts input/response PII and entity types."""
    with patch("src.analytics.supabase", _mock_supabase_with_logs(SAMPLE_LOGS)):
        from src.analytics import AnalyticsService

        svc = AnalyticsService()
        result = await svc.get_pii_stats(
            "cus_test123",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 31, tzinfo=timezone.utc),
        )

    summary = result["summary"]
    assert summary["total_requests"] == 4
    # log_1 and log_3 have input PII
    assert summary["requests_with_input_pii"] == 2
    # log_2 has response PII
    assert summary["requests_with_response_pii"] == 1
    assert summary["input_pii_rate"] == 50.0
    assert summary["response_pii_rate"] == 25.0

    entity_map = {e["type"]: e for e in result["entity_types"]}
    assert entity_map["PERSON"]["input_count"] == 2
    assert entity_map["PERSON"]["total_count"] == 2
    assert entity_map["EMAIL_ADDRESS"]["response_count"] == 1
    assert entity_map["EMAIL_ADDRESS"]["total_count"] == 1


@pytest.mark.asyncio
async def test_analytics_pii_rate_calculation():
    """PII rates are calculated as correct percentages."""
    logs = [
        {
            "id": "a", "customer_id": "c", "user_id": None, "provider": "openai",
            "model": "gpt-4", "tokens_input": 10, "tokens_output": 10,
            "latency_ms": 100, "cost_usd": "0.001",
            "pii_detected": [{"type": "PERSON", "replacement": "X", "confidence": 0.9}],
            "response_pii_detected": [],
            "created_at": "2026-01-15T10:00:00+00:00",
        },
        {
            "id": "b", "customer_id": "c", "user_id": None, "provider": "openai",
            "model": "gpt-4", "tokens_input": 10, "tokens_output": 10,
            "latency_ms": 100, "cost_usd": "0.001",
            "pii_detected": [],
            "response_pii_detected": [],
            "created_at": "2026-01-15T11:00:00+00:00",
        },
    ]

    with patch("src.analytics.supabase", _mock_supabase_with_logs(logs)):
        from src.analytics import AnalyticsService

        svc = AnalyticsService()
        result = await svc.get_pii_stats(
            "c",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 31, tzinfo=timezone.utc),
        )

    assert result["summary"]["input_pii_rate"] == 50.0
    assert result["summary"]["response_pii_rate"] == 0.0


@pytest.mark.asyncio
async def test_analytics_cost_calculation():
    """Total cost is accurately summed across all logs."""
    with patch("src.analytics.supabase", _mock_supabase_with_logs(SAMPLE_LOGS)):
        from src.analytics import AnalyticsService

        svc = AnalyticsService()
        result = await svc.get_usage_summary(
            "cus_test123",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 31, tzinfo=timezone.utc),
        )

    # 0.01 + 0.02 + 0.01 + 0.01 = 0.05
    assert result["summary"]["total_cost_usd"] == 0.05
    for point in result["time_series"]:
        assert point["cost_usd"] >= 0


@pytest.mark.asyncio
async def test_analytics_service_export_data():
    """Export returns correctly aggregated daily rows with all fields."""
    with patch("src.analytics.supabase", _mock_supabase_with_logs(SAMPLE_LOGS)):
        from src.analytics import AnalyticsService

        svc = AnalyticsService()
        rows = await svc.get_export_data(
            "cus_test123",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 31, tzinfo=timezone.utc),
        )

    assert len(rows) == 3  # 3 distinct days

    # Jan 16 has 2 logs (log_2 + log_3)
    jan16 = next(r for r in rows if r["date"] == "2026-01-16")
    assert jan16["requests"] == 2
    assert jan16["tokens_input"] == 350  # 150 + 200
    assert jan16["tokens_output"] == 400  # 100 + 300
    # Both logs on Jan 16 have PII (log_2 response, log_3 input)
    assert jan16["pii_detected_count"] == 2

    # All required export fields present
    for row in rows:
        assert "date" in row
        assert "requests" in row
        assert "pii_detected_count" in row
        assert "top_model" in row


@pytest.mark.asyncio
async def test_analytics_service_empty_data():
    """All service methods return valid empty responses when no logs exist."""
    with patch("src.analytics.supabase", _mock_supabase_with_logs([])):
        from src.analytics import AnalyticsService

        svc = AnalyticsService()
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)

        usage = await svc.get_usage_summary("cus_test123", start, end)
        assert usage["summary"]["total_requests"] == 0
        assert usage["summary"]["avg_latency_ms"] == 0
        assert usage["time_series"] == []

        models = await svc.get_model_breakdown("cus_test123", start, end)
        assert models["models"] == []

        users = await svc.get_user_breakdown("cus_test123", start, end)
        assert users["users"] == []
        assert users["total_unique_users"] == 0
        assert users["users_with_no_id"]["requests"] == 0

        pii = await svc.get_pii_stats("cus_test123", start, end)
        assert pii["summary"]["total_requests"] == 0
        assert pii["summary"]["input_pii_rate"] == 0.0
        assert pii["entity_types"] == []
        assert pii["time_series"] == []

        export = await svc.get_export_data("cus_test123", start, end)
        assert export == []


@pytest.mark.asyncio
async def test_analytics_service_date_bucket():
    """Static _date_bucket produces correct keys for all granularities."""
    from src.analytics import AnalyticsService

    dt = datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc)  # Thursday
    assert AnalyticsService._date_bucket(dt, "day") == "2026-01-15"
    assert AnalyticsService._date_bucket(dt, "week") == "2026-01-12"  # Monday
    assert AnalyticsService._date_bucket(dt, "month") == "2026-01-01"
