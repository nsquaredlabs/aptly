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

### Prerequisites

- Python 3.11+
- Supabase account (database)
- Redis instance (rate limiting)

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/aptly.git
cd aptly

# Install dependencies
pip install -r requirements.txt

# Download spaCy model for PII detection
python -m spacy download en_core_web_sm

# Set up environment variables
cp .env.example .env
# Edit .env with your Supabase and Redis credentials
```

### Environment Variables

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
REDIS_URL=redis://localhost:6379/0
APTLY_ADMIN_SECRET=your-secure-admin-secret
ENVIRONMENT=development
```

### Run Locally

```bash
uvicorn src.main:app --reload --port 8000
```

---

## Usage Example

### 1. Create a Customer (Admin)

```bash
curl -X POST http://localhost:8000/v1/admin/customers \
  -H "X-Admin-Secret: your-admin-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "company_name": "Company Inc",
    "plan": "pro"
  }'
```

**Response:**
```json
{
  "customer": {
    "id": "cus_abc123",
    "email": "admin@company.com",
    "company_name": "Company Inc"
  },
  "api_key": {
    "key": "apt_live_xyz789...",
    "key_id": "key_123"
  }
}
```

### 2. Make a Chat Completion Request (Customer)

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={
        "Authorization": "Bearer apt_live_xyz789...",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "My SSN is 123-45-6789. What should I know about credit cards?"}
        ],
        "api_keys": {
            "openai": "sk-your-openai-key"
        }
    }
)

print(response.json())
```

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
    "http://localhost:8000/v1/chat/completions",
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
curl http://localhost:8000/v1/logs \
  -H "Authorization: Bearer apt_live_..."
```

Logs include: timestamps, models used, token counts, costs, PII detections, and full request/response payloads.

---

## API Endpoints

### Admin (X-Admin-Secret)
- `POST /v1/admin/customers` - Create customer
- `GET /v1/admin/customers` - List customers
- `GET /v1/admin/customers/{id}` - Get customer details
- `POST /v1/admin/customers/{id}/api-keys` - Create API key for customer

### Customer (Authorization: Bearer apt_live_*)
- `POST /v1/chat/completions` - Chat completion with PII redaction
- `GET /v1/api-keys` - List your API keys
- `POST /v1/api-keys` - Create new API key
- `DELETE /v1/api-keys/{id}` - Revoke API key
- `GET /v1/logs` - Query audit logs
- `GET /v1/logs/{id}` - Get log details
- `GET /v1/me` - Get profile
- `PATCH /v1/me` - Update settings

### Public
- `GET /v1/health` - Health check

---

## Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_chat_completions.py -v

# Code quality
ruff check src/ tests/
mypy src/
```

**Current Status:** 95 tests passing, 84% coverage

---

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment instructions (Railway, Supabase, Redis setup).

Quick deploy checklist:
1. Set up Supabase project and run migrations
2. Add Redis service (Railway Redis or Upstash)
3. Configure environment variables
4. Deploy to Railway
5. Run verification scripts

---

## Documentation

Full documentation available at: *(coming soon - Mintlify docs)*

For development guidance, see:
- [SPEC.md](SPEC.md) - Product specification
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [CLAUDE.md](CLAUDE.md) - AI assistant guidance

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
