# Aptly

**Compliance middleware for LLMs.** Aptly sits between your application and LLM providers, automatically redacting PII, logging every request for audit trails, and providing an OpenAI-compatible API.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/littlenishal/aptly.git
cd aptly
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
```

### 2. Start Postgres and Redis

```bash
docker compose up -d
```

This starts PostgreSQL 16 and Redis 7 locally via Docker.

### 3. Configure and run

```bash
export DATABASE_URL=postgresql+asyncpg://aptly:aptly@localhost/aptly
export REDIS_URL=redis://localhost:6379/0
export APTLY_API_SECRET=my-test-secret

aptly init-db
aptly serve
```

### 4. Verify it's running

```bash
curl http://localhost:8000/v1/health
```

### 5. Make your first request

In a separate terminal:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-test-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "My name is John Smith and my SSN is 123-45-6789"}],
    "api_keys": {"openai": "sk-YOUR_OPENAI_KEY"}
  }'
```

Aptly detects `John Smith` and `123-45-6789` as PII, redacts them before sending to OpenAI, logs the request, and returns the response with PII metadata.

### 6. Check audit logs

```bash
curl http://localhost:8000/v1/logs \
  -H "Authorization: Bearer my-test-secret"
```

---

## Why Aptly?

Organizations need LLMs but can't risk sending sensitive data to external APIs. Aptly solves this by:

- **Automatic PII Redaction** - Detects and redacts sensitive data (SSN, emails, names, credit cards) before sending to LLMs
- **Immutable Audit Logs** - Every request logged with database-enforced immutability for compliance
- **Multi-Provider Support** - Works with OpenAI, Anthropic, Google, Cohere, and more via unified API
- **OpenAI-Compatible** - Drop-in replacement requiring minimal code changes
- **Self-Hosted** - Runs on your infrastructure, your data never leaves your control
- **Rate Limiting** - Optional Redis-based distributed rate limiting with fail-open behavior

---

## How It Works

```
Client Request → Auth → PII Redaction → LLM Provider → Audit Log → Response
```

### PII Redaction Modes

| Mode | Example |
|------|---------|
| `mask` (default) | `"John Smith"` → `"PERSON_A"` |
| `hash` | `"John Smith"` → `"HASH_a3f2c1b9"` |
| `remove` | `"John Smith"` → `"[REDACTED]"` |

Supported entity types: PERSON, EMAIL, PHONE_NUMBER, SSN, CREDIT_CARD, and more via Microsoft Presidio.

### Compliance Frameworks

Set `COMPLIANCE_FRAMEWORKS` to automatically detect framework-specific entity types:

- `HIPAA` - Healthcare (medical record numbers, etc.)
- `FINTECH` / `PCI` - Financial (credit cards, routing numbers, etc.)
- `GDPR` - EU privacy (national IDs, EU passports, etc.)
- `SOC2` - General security (API keys, credentials, etc.)

---

## Configuration

All configuration is via environment variables (or `.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://localhost/aptly` | PostgreSQL connection string |
| `APTLY_API_SECRET` | Yes | - | Shared secret for API authentication |
| `REDIS_URL` | No | `None` | Redis URL for rate limiting (disabled without it) |
| `PII_REDACTION_MODE` | No | `mask` | PII redaction mode: `mask`, `hash`, or `remove` |
| `COMPLIANCE_FRAMEWORKS` | No | `[]` | Compliance frameworks: `HIPAA`, `FINTECH`, `GDPR`, `SOC2` |
| `RATE_LIMIT_PER_HOUR` | No | `1000` | Global rate limit per hour |
| `CORS_ORIGINS` | No | `["http://localhost:3000", "http://localhost:8000"]` | Allowed CORS origins |
| `ENVIRONMENT` | No | `development` | Environment name |
| `SENTRY_DSN` | No | `None` | Sentry error tracking |

---

## API Usage

All endpoints (except health check) require `Authorization: Bearer <APTLY_API_SECRET>`.

### Chat Completions

`POST /v1/chat/completions` — OpenAI-compatible chat completion with automatic PII redaction.

**Basic request:**

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-test-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Summarize this report for John Smith, SSN 123-45-6789"}],
    "api_keys": {"openai": "sk-YOUR_OPENAI_KEY"}
  }'
```

**With optional parameters:**

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-test-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Hello from user alice@example.com"}],
    "api_keys": {"anthropic": "sk-ant-YOUR_KEY"},
    "user": "user-123",
    "temperature": 0.7,
    "max_tokens": 500,
    "redact_response": true,
    "stream": false
  }'
```

**Response:**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1709900000,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "Here is the summary..."},
      "finish_reason": "stop"
    }
  ],
  "usage": {"prompt_tokens": 25, "completion_tokens": 50, "total_tokens": 75},
  "aptly": {
    "audit_log_id": "a1b2c3d4-...",
    "pii_detected": true,
    "pii_entities": ["PERSON", "US_SSN"],
    "response_pii_detected": false,
    "response_pii_entities": [],
    "compliance_framework": null,
    "latency_ms": 1200
  }
}
```

**Streaming:**

```bash
curl -N -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-test-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "api_keys": {"openai": "sk-YOUR_OPENAI_KEY"},
    "stream": true
  }'
```

Returns Server-Sent Events (SSE) in the same format as OpenAI's streaming API. The final chunk includes an `aptly` metadata field with PII detection results and the audit log ID.

**Using with Python (OpenAI SDK):**

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="my-test-secret",
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello, my email is alice@example.com"}],
    extra_body={"api_keys": {"openai": "sk-YOUR_OPENAI_KEY"}},
)
print(response.choices[0].message.content)
```

**Supported providers and models:**

Pass the appropriate key in `api_keys` for the model you choose:

| Provider | Example Models | `api_keys` key |
|----------|---------------|----------------|
| OpenAI | `gpt-4`, `gpt-4o`, `gpt-3.5-turbo` | `openai` |
| Anthropic | `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307` | `anthropic` |
| Google | `gemini/gemini-pro`, `gemini/gemini-1.5-flash` | `google` |
| Cohere | `command-r`, `command-r-plus` | `cohere` |
| Together | `together_ai/meta-llama/...` | `together_ai` |

### Audit Logs

**List logs with filtering:**

```bash
curl "http://localhost:8000/v1/logs?start_date=2025-01-01&end_date=2025-01-31&user_id=user-123&model=gpt-4&limit=20&page=1" \
  -H "Authorization: Bearer my-test-secret"
```

**Get a specific log entry:**

```bash
curl http://localhost:8000/v1/logs/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Authorization: Bearer my-test-secret"
```

### Analytics

```bash
# Usage summary with time series (granularity: day, week, or month)
curl "http://localhost:8000/v1/analytics/usage?start_date=2025-01-01&end_date=2025-01-31&granularity=day" \
  -H "Authorization: Bearer my-test-secret"

# Breakdown by model/provider
curl "http://localhost:8000/v1/analytics/models?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer my-test-secret"

# Breakdown by end-user
curl "http://localhost:8000/v1/analytics/users?start_date=2025-01-01&end_date=2025-01-31&limit=50" \
  -H "Authorization: Bearer my-test-secret"

# PII detection statistics
curl "http://localhost:8000/v1/analytics/pii?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer my-test-secret"

# Export data as CSV or JSON
curl "http://localhost:8000/v1/analytics/export?start_date=2025-01-01&end_date=2025-01-31&format=csv" \
  -H "Authorization: Bearer my-test-secret" -o analytics.csv
```

### Health Check

```bash
curl http://localhost:8000/v1/health
# {"status": "healthy", "version": "1.0.0", "checks": {"database": "ok", "redis": "ok"}}
```

---

## CLI

```bash
aptly serve              # Start the API server
aptly serve --port 9000  # Custom port
aptly serve --reload     # Development mode with auto-reload
aptly init-db            # Run database migrations
aptly version            # Print version
```

---

## Deploying to Production

Aptly ships with a `Dockerfile` that handles installation, spaCy model download, and database migrations automatically.

### Railway (recommended)

1. Push your repo to GitHub
2. Create a new project on [Railway](https://railway.app)
3. Add a **PostgreSQL** database and **Redis** service
4. Create a new service from your GitHub repo
5. Set these environment variables on the service:

   | Variable | Value |
   |----------|-------|
   | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (Railway auto-fills this) |
   | `REDIS_URL` | `${{Redis.REDIS_URL}}` (Railway auto-fills this) |
   | `APTLY_API_SECRET` | A strong random secret |
   | `ENVIRONMENT` | `production` |

6. Railway auto-detects the Dockerfile and deploys. Migrations run on every deploy.

   Aptly automatically converts `postgresql://` and `postgres://` URLs to the `postgresql+asyncpg://` format needed by asyncpg.

### Docker (any cloud)

```bash
docker build -t aptly .

docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@your-db-host/aptly \
  -e REDIS_URL=redis://your-redis-host:6379/0 \
  -e APTLY_API_SECRET=your-secret \
  -e ENVIRONMENT=production \
  aptly
```

Works on any platform that runs containers: Fly.io, Render, AWS ECS, Google Cloud Run, etc.

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Download spacy model
python -m spacy download en_core_web_sm

# Run tests
pytest tests/ -v

# Code quality
ruff check src/ tests/
```

---

## Tech Stack

- **FastAPI** - Web framework
- **PostgreSQL** - Database (via SQLAlchemy + asyncpg)
- **Alembic** - Database migrations
- **Redis** - Rate limiting (optional)
- **LiteLLM** - Multi-provider LLM abstraction
- **Microsoft Presidio** - PII detection
- **Sentry** - Error tracking (optional)

---

## License

MIT License - see [LICENSE](LICENSE) for details.
