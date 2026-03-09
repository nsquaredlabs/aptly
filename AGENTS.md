# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project Overview

Aptly is an open-source compliance middleware for LLM requests. It sits between your app and LLM providers, automatically redacting PII, logging requests for audit trails, and providing an OpenAI-compatible API.

Self-hosted, works with any PostgreSQL database. Install via `pip install -e .` or clone from GitHub.

**Key principle:** Working software over theoretical completeness. Every endpoint must be usable from day one.

## Development Commands

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run a single test file
pytest tests/test_chat_completions.py -v

# Run a single test
pytest tests/test_chat_completions.py::test_chat_completion_basic -v

# Code quality
ruff check src/ tests/
mypy src/

# Start development server
aptly serve --reload
# or: uvicorn src.main:app --reload --port 8000

# Initialize database
aptly init-db

# Download spacy model (required for PII detection)
python -m spacy download en_core_web_sm
```

## Architecture

### Request Flow
```
Client Request → API Secret Auth → PII Redaction → LLM Provider (via LiteLLM) → PII Restoration → Audit Log → Response
```

### Core Components

- **src/main.py** - FastAPI app entry point with all route definitions
- **src/models.py** - SQLAlchemy ORM model (AuditLog)
- **src/db.py** - Async database engine + session factory + `get_db()` FastAPI dependency
- **src/config.py** - Pydantic settings loaded from environment variables
- **src/auth.py** - Single shared secret auth (`Authorization: Bearer <APTLY_API_SECRET>`)
- **src/compliance/pii_redactor.py** - Microsoft Presidio integration for PII detection and redaction (PERSON, EMAIL, SSN, CREDIT_CARD, etc.), plus un-redaction to restore original PII in LLM responses
- **src/compliance/audit_logger.py** - Immutable audit log writer (database trigger prevents modification)
- **src/llm_router.py** - LiteLLM abstraction for multi-provider support (OpenAI, Anthropic, Google, Cohere, Together)
- **src/rate_limiter.py** - Redis-based distributed rate limiting with fail-open behavior (disabled when Redis not configured)
- **src/analytics.py** - Analytics service for aggregating audit log data
- **src/cli.py** - Click CLI (`aptly serve`, `aptly init-db`, `aptly version`)

### Key Design Decisions

1. **Single-Tenant Auth**: One shared API secret (`APTLY_API_SECRET`) for all authenticated endpoints — designed for self-hosted use
2. **User-Provided LLM Keys**: Users pass their own provider keys per-request; Aptly never stores them
3. **SQLAlchemy + asyncpg**: Async ORM with any PostgreSQL database (no vendor lock-in)
4. **Redis Optional**: Rate limiting uses Redis when available, gracefully disabled without it
5. **Cross-DB Models**: ORM models use custom type decorators (UUIDType, JSONType) that work with both PostgreSQL and SQLite (for testing)
6. **Config via Environment**: PII redaction mode, compliance frameworks, rate limits all configured via env vars

### PII Redaction Modes
- `mask`: "John Smith" → "PERSON_A" (reversible — original restored in response)
- `hash`: "John Smith" → "HASH_a3f2c1b9" (reversible — original restored in response)
- `remove`: "John Smith" → "[REDACTED]" (irreversible — cannot restore in response)

### PII Un-redaction Flow
After the LLM responds, placeholders (e.g., "PERSON_A") are replaced back with original values before returning to the user. The audit log always stores the redacted version. Set `redact_response: true` to skip restoration and keep PII redacted in the user-facing response.

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/aptly
APTLY_API_SECRET=your-secret-here

# Optional
REDIS_URL=redis://localhost:6379/0  # No Redis = no rate limiting
PII_REDACTION_MODE=mask             # mask, hash, or remove
COMPLIANCE_FRAMEWORKS='["HIPAA"]'   # HIPAA, FINTECH, GDPR, SOC2
RATE_LIMIT_PER_HOUR=1000
CORS_ORIGINS='["http://localhost:3000"]'
ENVIRONMENT=development
LOG_LEVEL=info
PORT=8000
SENTRY_DSN=                         # Error tracking
```

## API Reference and Examples

All endpoints except `/v1/health` require `Authorization: Bearer <APTLY_API_SECRET>`.

### POST /v1/chat/completions

OpenAI-compatible chat completion with automatic PII redaction. Users pass their own LLM provider keys per-request.

**Request body:**

```json
{
  "model": "gpt-4",                          // Required: LLM model name
  "messages": [                               // Required: OpenAI-format messages
    {"role": "user", "content": "Hello"}
  ],
  "api_keys": {"openai": "sk-..."},          // Required: provider API keys
  "user": "user-123",                         // Optional: end-user ID for audit logs
  "stream": false,                            // Optional: enable SSE streaming
  "temperature": 0.7,                         // Optional: sampling temperature
  "max_tokens": 500,                          // Optional: max response tokens
  "top_p": 1.0,                              // Optional
  "frequency_penalty": 0.0,                   // Optional
  "presence_penalty": 0.0,                    // Optional
  "stop": null,                               // Optional: stop sequences
  "redact_response": false                    // Optional: redact PII in LLM response too
}
```

**Provider key mapping** — the `api_keys` dict key must match the provider:

| Provider | Models (examples) | Key name |
|----------|-------------------|----------|
| OpenAI | `gpt-4`, `gpt-4o`, `gpt-3.5-turbo` | `openai` |
| Anthropic | `claude-3-5-sonnet-20241022` | `anthropic` |
| Google | `gemini/gemini-pro` | `google` |
| Cohere | `command-r`, `command-r-plus` | `cohere` |
| Together | `together_ai/meta-llama/...` | `together_ai` |

**Example curl:**

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $APTLY_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "My name is John Smith and my SSN is 123-45-6789"}],
    "api_keys": {"openai": "sk-YOUR_KEY"},
    "user": "user-123"
  }'
```

**Response shape:**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1709900000,
  "model": "gpt-4",
  "choices": [{"index": 0, "message": {"role": "assistant", "content": "..."}, "finish_reason": "stop"}],
  "usage": {"prompt_tokens": 25, "completion_tokens": 50, "total_tokens": 75},
  "aptly": {
    "audit_log_id": "uuid-here",
    "pii_detected": true,
    "pii_entities": ["PERSON", "US_SSN"],
    "response_pii_detected": false,
    "response_pii_entities": [],
    "compliance_framework": null,
    "latency_ms": 1200
  }
}
```

The `aptly` field is Aptly-specific metadata added to every response.

**Using the OpenAI Python SDK:**

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="my-test-secret")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello from alice@example.com"}],
    extra_body={"api_keys": {"openai": "sk-YOUR_KEY"}},
)
```

**Streaming** — set `"stream": true`. Returns SSE in OpenAI format. The final chunk includes `aptly` metadata.

### GET /v1/logs

Query audit logs. All query params are optional.

```
GET /v1/logs?start_date=2025-01-01&end_date=2025-01-31&user_id=user-123&model=gpt-4&limit=50&page=1
```

Defaults to last 30 days if no dates provided.

### GET /v1/logs/{id}

Get full audit log detail including `request_data` and `response_data`.

### GET /v1/analytics/usage

```
GET /v1/analytics/usage?start_date=2025-01-01&end_date=2025-01-31&granularity=day
```

`granularity`: `day`, `week`, or `month`.

### GET /v1/analytics/models

Model/provider breakdown for the given date range.

### GET /v1/analytics/users

End-user breakdown. `limit` param (max 100).

### GET /v1/analytics/pii

PII detection statistics: rates, entity type counts, time series.

### GET /v1/analytics/export

```
GET /v1/analytics/export?start_date=2025-01-01&end_date=2025-01-31&format=csv&include=usage,pii
```

`format`: `csv` or `json`. `include`: comma-separated filter (optional).

### GET /v1/health

No auth required. Returns `{"status": "healthy", "version": "...", "checks": {"database": "ok", "redis": "ok"}}`.

## Testing

Tests use SQLite (via aiosqlite) with the `get_db` dependency overridden. No external services needed.

Critical test cases that must pass:

- `test_chat_completion_pii_redaction` - PII detected before sending to LLM
- `test_chat_completion_audit_log_created` - Every request logged
- `test_api_secret_valid` - Valid secret authenticates
- `test_api_secret_missing` - Missing auth returns 401

Coverage target: >80%

## Database

Migrations managed by Alembic in `alembic/versions/`. Single table:
- `audit_logs` - Immutable request logs (database trigger prevents modification/deletion)

Run `aptly init-db` (or `alembic upgrade head`) to apply migrations.
