# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Aptly is a compliance-as-a-service middleware API that proxies LLM requests while handling PII redaction and audit logging. It provides an OpenAI-compatible API interface for organizations that need to use LLMs while maintaining compliance and protecting sensitive data.

**API Base URL:** https://aptly-api.nsquaredlabs.com
**Website Base URL:** https://aptly.nsquaredlabs.com
**Documentation Base URL:** https://aptly.nsquaredlabs.com/docs

**Key principle:** Working software over theoretical completeness. Every endpoint must be usable from day one.

## Development Commands

```bash
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
uvicorn src.main:app --reload --port 8000

# Download spacy model (required for PII detection)
python -m spacy download en_core_web_sm
```

## Architecture

### Request Flow
```
Client Request → API Key Auth → PII Redaction → LLM Provider (via LiteLLM) → Audit Log → Response
```

### Core Components

- **src/main.py** - FastAPI app entry point with all route definitions
- **src/supabase_client.py** - Supabase client initialization (uses service role key)
- **src/auth.py** - Two auth paths: Admin Secret (`X-Admin-Secret` header) for customer creation, API Keys (`Authorization: Bearer apt_live_*`) for all customer operations
- **src/compliance/pii_redactor.py** - Microsoft Presidio integration for PII detection (PERSON, EMAIL, SSN, CREDIT_CARD, etc.)
- **src/compliance/audit_logger.py** - Immutable audit log writer (database trigger prevents modification)
- **src/llm_router.py** - LiteLLM abstraction for multi-provider support (OpenAI, Anthropic, Google, Cohere, Together)
- **src/rate_limiter.py** - Redis-based distributed rate limiting with fail-open behavior

### Key Design Decisions

1. **Bootstrap Problem Solution**: Admin Secret env var creates customers; customers use API keys for everything else
2. **Customer-Provided LLM Keys**: Customers pass their own provider keys per-request; Aptly never stores them
3. **Supabase Client (No ORM)**: Uses Supabase Python client directly instead of SQLAlchemy - simpler, less boilerplate
4. **Redis Required**: Rate limiting uses Redis (not in-memory) to support multiple workers
5. **No Scopes**: All API keys have full access to their customer's resources (simplification for MVP)

### PII Redaction Modes
- `mask`: "John Smith" → "PERSON_A"
- `hash`: "John Smith" → "HASH_a3f2c1b9"
- `remove`: "John Smith" → "[REDACTED]"

## Environment Variables

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...   # Service role key (bypasses RLS)
REDIS_URL=redis://localhost:6379/0
APTLY_ADMIN_SECRET=your-secure-admin-secret-here

# Optional
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=info          # debug, info, warning, error
PORT=8000
SENTRY_DSN=             # Error tracking
```

## API Key Format

- Production: `apt_live_*`
- Test: `apt_test_*`

## Main Endpoints

- `POST /v1/admin/customers` - Create customer (Admin Secret auth)
- `POST /v1/chat/completions` - OpenAI-compatible chat completion with PII redaction
- `GET /v1/logs` - Query audit logs
- `GET /v1/health` - Health check (no auth)

## Testing

Tests mock the Supabase client and external dependencies. Critical test cases that must pass:

- `test_chat_completion_pii_redaction` - PII detected before sending to LLM
- `test_chat_completion_audit_log_created` - Every request logged
- `test_admin_create_customer` - Bootstrap flow works
- `test_api_key_validation` - Valid key authenticates

Coverage target: >80%

## Database

Migrations live in `supabase/migrations/`. The schema includes three tables:
- `customers` - Customer accounts with plan and compliance settings
- `api_keys` - API keys with hash storage (never store raw keys)
- `audit_logs` - Immutable request logs (database trigger prevents modification/deletion)
