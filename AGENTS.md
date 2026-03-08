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
Client Request → API Secret Auth → PII Redaction → LLM Provider (via LiteLLM) → Audit Log → Response
```

### Core Components

- **src/main.py** - FastAPI app entry point with all route definitions
- **src/models.py** - SQLAlchemy ORM model (AuditLog)
- **src/db.py** - Async database engine + session factory + `get_db()` FastAPI dependency
- **src/config.py** - Pydantic settings loaded from environment variables
- **src/auth.py** - Single shared secret auth (`Authorization: Bearer <APTLY_API_SECRET>`)
- **src/compliance/pii_redactor.py** - Microsoft Presidio integration for PII detection (PERSON, EMAIL, SSN, CREDIT_CARD, etc.)
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
- `mask`: "John Smith" → "PERSON_A"
- `hash`: "John Smith" → "HASH_a3f2c1b9"
- `remove`: "John Smith" → "[REDACTED]"

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

## Main Endpoints

- `POST /v1/chat/completions` - OpenAI-compatible chat completion with PII redaction
- `GET /v1/logs` - Query audit logs
- `GET /v1/logs/{id}` - Get log details
- `GET /v1/analytics/usage` - Usage summary
- `GET /v1/analytics/models` - Model breakdown
- `GET /v1/analytics/users` - User breakdown
- `GET /v1/analytics/pii` - PII statistics
- `GET /v1/analytics/export` - Export data (CSV/JSON)
- `GET /v1/health` - Health check (no auth)

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
