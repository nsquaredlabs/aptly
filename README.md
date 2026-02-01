# Aptly

**Compliance-as-a-service middleware for LLMs.** Aptly sits between your application and LLM providers, automatically redacting PII, logging requests for audit trails, and providing OpenAI-compatible APIs.

[![Tests](https://img.shields.io/badge/tests-95%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-84%25-green)](tests/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## Why Aptly?

Organizations need LLMs but can't risk sending sensitive data to external APIs. Aptly solves this by:

- **🔒 Automatic PII Redaction** - Detects and redacts sensitive data (SSN, emails, names, credit cards) before sending to LLMs
- **📋 Immutable Audit Logs** - Every request logged with database-enforced immutability for compliance
- **🔄 Multi-Provider Support** - Works with OpenAI, Anthropic, Google, Cohere, and more via unified API
- **⚡ OpenAI-Compatible** - Drop-in replacement requiring minimal code changes
- **🛡️ Customer-Controlled Keys** - Customers provide their own LLM API keys (never stored by Aptly)
- **📊 Rate Limiting** - Redis-based distributed rate limiting with fail-open behavior

---

## Quick Start

Aptly is a **hosted service** - no installation or infrastructure setup required!

### Get Your API Key

Contact the Aptly team to receive your API key:
- **Email:** sales@aptly.dev
- **Website:** https://aptly.dev

You'll receive an API key in the format `apt_live_*` or `apt_test_*`.

### Make Your First Request

```bash
curl -X POST https://api-aptly.nsquaredlabs.com/v1/chat/completions \
  -H "Authorization: Bearer apt_live_YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "My SSN is 123-45-6789"}],
    "api_keys": {"openai": "sk-YOUR_OPENAI_KEY"}
  }'
```

### Python Example

```python
from openai import OpenAI

client = OpenAI(
    api_key="apt_live_YOUR_API_KEY",
    base_url="https://api-aptly.nsquaredlabs.com/v1"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "My email is user@example.com"}],
    extra_body={"api_keys": {"openai": "sk-YOUR_OPENAI_KEY"}}
)

print(response.choices[0].message.content)
# Output: "My email is EMAIL_A" (PII automatically redacted!)
```

---

## How It Works

**What happens:**
1. Aptly detects "123-45-6789" as PII
2. Redacts it to "SSN_A" before sending to OpenAI
3. Logs the request with PII metadata
4. Returns the response with original PII mapping

---

## Key Features

### PII Redaction Modes

- **mask** (default): `"John Smith"` → `"PERSON_A"`
- **hash**: `"John Smith"` → `"HASH_a3f2c1b9"`
- **remove**: `"John Smith"` → `"[REDACTED]"`

Supported entity types: PERSON, EMAIL, PHONE_NUMBER, SSN, CREDIT_CARD, and more via Microsoft Presidio.

### Streaming Support

```python
response = requests.post(
    "https://api-aptly.nsquaredlabs.com/v1/chat/completions",
    headers={"Authorization": "Bearer apt_live_..."},
    json={
        "model": "gpt-4",
        "messages": [...],
        "stream": true,
        "api_keys": {"openai": "sk-..."}
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

### Audit Logs

Query all requests with pagination:

```bash
curl https://api-aptly.nsquaredlabs.com/v1/logs \
  -H "Authorization: Bearer apt_live_..."
```

Logs include: timestamps, models used, token counts, costs, PII detections, and full request/response payloads.

---

## API Endpoints

All requests use `https://api-aptly.nsquaredlabs.com` as the base URL.

### Chat & LLM Operations
- `POST /v1/chat/completions` - Chat completion with automatic PII redaction

### Your Account
- `GET /v1/api-keys` - List your API keys
- `POST /v1/api-keys` - Create new API key
- `DELETE /v1/api-keys/{id}` - Revoke API key
- `GET /v1/me` - Get your profile
- `PATCH /v1/me` - Update your settings

### Audit Logs
- `GET /v1/logs` - Query your audit logs
- `GET /v1/logs/{id}` - Get log details

### Public
- `GET /v1/health` - Health check (no auth required)

---

## Documentation

📚 **Full documentation:** https://docs.aptly.dev *(coming soon)*

- [API Reference](https://docs.aptly.dev/api) - Complete API documentation
- [Guides](https://docs.aptly.dev/guides) - PII redaction, compliance, rate limiting
- [Architecture](https://docs.aptly.dev/deployment/architecture) - How Aptly works internally

---

## For Contributors & Developers

If you're contributing to Aptly or want to self-host:

- [SPEC.md](SPEC.md) - Product specification
- [DEPLOYMENT.md](DEPLOYMENT.md) - Self-hosting deployment guide
- [CLAUDE.md](CLAUDE.md) - Development guidance

**Running tests:**
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Architecture

```
Client Request
    ↓
API Key Authentication
    ↓
PII Redaction (Presidio)
    ↓
LLM Provider (via LiteLLM)
    ↓
Response PII Detection
    ↓
Audit Log (immutable)
    ↓
Response to Client
```

**Tech Stack:**
- FastAPI - Web framework
- Supabase - PostgreSQL database
- Redis - Rate limiting
- LiteLLM - Multi-provider LLM abstraction
- Microsoft Presidio - PII detection
- Sentry - Error tracking (optional)

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- Issues: [GitHub Issues](https://github.com/your-org/aptly/issues)
- Email: support@aptly.dev

**Built by NSquared Labs**
