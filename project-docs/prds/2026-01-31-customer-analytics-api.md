# PRD: Customer Analytics API

**Date:** 2026-01-31
**Status:** Draft
**Spec Reference:** Phase 2 feature (enables future dashboard)

## Overview

Add analytics endpoints that provide customers with aggregated usage metrics, cost breakdowns, and PII detection statistics. These endpoints serve as the data layer for a future customer-facing dashboard and enable customers to build their own analytics views.

## Context

### Current State
- Audit logs capture all request data (tokens, cost, latency, PII detected)
- `GET /v1/logs` returns paginated raw logs
- `GET /v1/me` returns basic `usage` with `requests_this_month` and `tokens_this_month`
- `audit_logger.get_usage_stats()` provides simple aggregation internally
- No way for customers to get aggregated analytics or breakdowns

### Gap Being Addressed
Customers need to:
- Understand their usage patterns over time
- Track costs by model and provider
- Monitor PII detection rates
- Export data for compliance reporting
- Build their own dashboards on top of Aptly

## Requirements

### 1. Usage Summary Endpoint
**`GET /v1/analytics/usage`**

Returns aggregated usage metrics for a time period.

```
Query Parameters:
- start_date (optional): ISO date, default 30 days ago
- end_date (optional): ISO date, default today
- granularity (optional): "day" | "week" | "month", default "day"
```

Response:
```json
{
  "summary": {
    "total_requests": 15234,
    "total_tokens": 2456000,
    "total_cost_usd": 45.67,
    "avg_latency_ms": 1234,
    "period_start": "2026-01-01",
    "period_end": "2026-01-31"
  },
  "time_series": [
    {
      "date": "2026-01-01",
      "requests": 523,
      "tokens_input": 45000,
      "tokens_output": 32000,
      "cost_usd": 1.45,
      "avg_latency_ms": 1100
    },
    ...
  ]
}
```

### 2. Model Breakdown Endpoint
**`GET /v1/analytics/models`**

Returns usage breakdown by model.

```
Query Parameters:
- start_date (optional): ISO date, default 30 days ago
- end_date (optional): ISO date, default today
```

Response:
```json
{
  "models": [
    {
      "model": "gpt-4",
      "provider": "openai",
      "requests": 8234,
      "tokens_input": 1200000,
      "tokens_output": 800000,
      "cost_usd": 38.50,
      "avg_latency_ms": 1500,
      "percentage_of_requests": 54.1
    },
    {
      "model": "claude-3-sonnet",
      "provider": "anthropic",
      "requests": 4521,
      "tokens_input": 600000,
      "tokens_output": 400000,
      "cost_usd": 5.20,
      "avg_latency_ms": 980,
      "percentage_of_requests": 29.7
    },
    ...
  ],
  "period_start": "2026-01-01",
  "period_end": "2026-01-31"
}
```

### 3. User Breakdown Endpoint
**`GET /v1/analytics/users`**

Returns usage breakdown by end-user ID (the `user` field from chat completions).

```
Query Parameters:
- start_date (optional): ISO date, default 30 days ago
- end_date (optional): ISO date, default today
- limit (optional): number of top users, default 50, max 100
```

Response:
```json
{
  "users": [
    {
      "user_id": "user_123",
      "requests": 2341,
      "tokens_input": 340000,
      "tokens_output": 210000,
      "cost_usd": 12.30,
      "last_active": "2026-01-31T14:30:00Z"
    },
    ...
  ],
  "users_with_no_id": {
    "requests": 1234,
    "tokens_input": 100000,
    "tokens_output": 80000,
    "cost_usd": 3.50
  },
  "total_unique_users": 156,
  "period_start": "2026-01-01",
  "period_end": "2026-01-31"
}
```

### 4. PII Statistics Endpoint
**`GET /v1/analytics/pii`**

Returns PII detection statistics.

```
Query Parameters:
- start_date (optional): ISO date, default 30 days ago
- end_date (optional): ISO date, default today
```

Response:
```json
{
  "summary": {
    "requests_with_input_pii": 3456,
    "requests_with_response_pii": 892,
    "total_requests": 15234,
    "input_pii_rate": 22.7,
    "response_pii_rate": 5.9
  },
  "entity_types": [
    {
      "type": "PERSON",
      "input_count": 4521,
      "response_count": 654,
      "total_count": 5175
    },
    {
      "type": "EMAIL_ADDRESS",
      "input_count": 1234,
      "response_count": 123,
      "total_count": 1357
    },
    {
      "type": "PHONE_NUMBER",
      "input_count": 567,
      "response_count": 45,
      "total_count": 612
    },
    ...
  ],
  "time_series": [
    {
      "date": "2026-01-01",
      "requests_with_pii": 112,
      "total_requests": 523,
      "pii_rate": 21.4
    },
    ...
  ],
  "period_start": "2026-01-01",
  "period_end": "2026-01-31"
}
```

### 5. Export Endpoint
**`GET /v1/analytics/export`**

Export analytics data in CSV format for compliance reporting.

```
Query Parameters:
- start_date (required): ISO date
- end_date (required): ISO date
- format (optional): "csv" | "json", default "csv"
- include (optional): comma-separated list of "usage,models,users,pii", default all
```

Response:
- `Content-Type: text/csv` or `application/json`
- `Content-Disposition: attachment; filename="aptly-analytics-2026-01.csv"`

CSV includes columns:
```
date,requests,tokens_input,tokens_output,cost_usd,avg_latency_ms,pii_detected_count,top_model
```

## Technical Approach

### Database Queries
All analytics queries will aggregate from the `audit_logs` table. For MVP, we'll use Supabase queries directly. If performance becomes an issue, we can add materialized views or a separate analytics table later.

Example aggregation query for usage summary:
```sql
SELECT
  DATE(created_at) as date,
  COUNT(*) as requests,
  SUM(tokens_input) as tokens_input,
  SUM(tokens_output) as tokens_output,
  SUM(cost_usd) as cost_usd,
  AVG(latency_ms) as avg_latency_ms
FROM audit_logs
WHERE customer_id = $1
  AND created_at >= $2
  AND created_at <= $3
GROUP BY DATE(created_at)
ORDER BY date
```

### Implementation Pattern
Create a new `src/analytics.py` module with an `AnalyticsService` class:

```python
class AnalyticsService:
    async def get_usage_summary(
        self,
        customer_id: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "day"
    ) -> UsageSummary: ...

    async def get_model_breakdown(
        self,
        customer_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> ModelBreakdown: ...

    # etc.
```

### Response Models
Use Pydantic models for type safety and automatic OpenAPI docs:

```python
class UsageDataPoint(BaseModel):
    date: str
    requests: int
    tokens_input: int
    tokens_output: int
    cost_usd: float
    avg_latency_ms: int

class UsageSummaryResponse(BaseModel):
    summary: UsageSummary
    time_series: list[UsageDataPoint]
```

## Files to Modify/Create

### New Files
- `src/analytics.py` - AnalyticsService with aggregation methods
- `tests/test_analytics.py` - Analytics endpoint tests

### Modified Files
- `src/main.py` - Add 5 new analytics endpoints
- `docs/api/analytics/` - Documentation for new endpoints (4 files)

## Database Changes

None required. All analytics are derived from existing `audit_logs` table.

**Future optimization (not in this PRD):** If queries become slow, add:
- Database indexes on `(customer_id, created_at)`
- Daily aggregation table updated by cron/trigger

## Testing Strategy

### Unit Tests
- `test_analytics_usage_summary` - Correct aggregation
- `test_analytics_model_breakdown` - Group by model
- `test_analytics_user_breakdown` - Group by user_id
- `test_analytics_pii_stats` - PII counting logic
- `test_analytics_date_filtering` - Date range handling

### Integration Tests
- `test_analytics_empty_data` - New customer with no logs
- `test_analytics_unauthorized` - Requires valid API key
- `test_analytics_export_csv` - CSV format correct
- `test_analytics_granularity` - Day/week/month grouping

### Critical Test Cases
- `test_analytics_usage_aggregation` - Totals match sum of time series
- `test_analytics_cost_calculation` - Cost sums are accurate
- `test_analytics_pii_rate` - Percentage calculations correct

## Dependencies

- Existing `audit_logs` table with data
- No new external dependencies

## Out of Scope

- Real-time analytics (WebSocket updates)
- Custom date ranges beyond 1 year
- Cross-customer analytics (admin only, future feature)
- Scheduled email reports
- Anomaly detection / alerts
- Data retention / archival
- Materialized views for performance (optimization for later)

## Success Criteria

- [ ] `GET /v1/analytics/usage` returns correct aggregated metrics
- [ ] `GET /v1/analytics/models` shows breakdown by model with percentages
- [ ] `GET /v1/analytics/users` shows top users by usage
- [ ] `GET /v1/analytics/pii` shows PII detection rates and entity breakdown
- [ ] `GET /v1/analytics/export` returns valid CSV/JSON
- [ ] All endpoints respect date filters
- [ ] All endpoints require customer API key auth
- [ ] Time series data matches the requested granularity
- [ ] Tests achieve >80% coverage of new code
- [ ] Documentation added for all new endpoints

## API Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/analytics/usage` | GET | Usage summary with time series |
| `/v1/analytics/models` | GET | Breakdown by model |
| `/v1/analytics/users` | GET | Breakdown by end-user |
| `/v1/analytics/pii` | GET | PII detection statistics |
| `/v1/analytics/export` | GET | Export data as CSV/JSON |
