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

## API Endpoints

All endpoints (except health check) require `Authorization: Bearer <APTLY_API_SECRET>`.

### Chat Completions
- `POST /v1/chat/completions` - OpenAI-compatible chat completion with automatic PII redaction

### Audit Logs
- `GET /v1/logs` - Query audit logs (with filtering by date, user, model)
- `GET /v1/logs/{id}` - Get detailed log entry

### Analytics
- `GET /v1/analytics/usage` - Usage summary with time series
- `GET /v1/analytics/models` - Breakdown by model/provider
- `GET /v1/analytics/users` - Breakdown by end-user
- `GET /v1/analytics/pii` - PII detection statistics
- `GET /v1/analytics/export` - Export data (CSV/JSON)

### Health
- `GET /v1/health` - Health check (no auth required)

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
