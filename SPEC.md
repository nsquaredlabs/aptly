# Aptly API Specification v3

**Product:** Aptly (by NSquared Labs)
**Version:** 3.0.0
**Last Updated:** 2026-01-24

---

## Overview

Aptly is a compliance-as-a-service middleware API that proxies LLM requests while handling PII redaction and audit logging. It provides an OpenAI-compatible API interface.

**Key Principle:** This spec prioritizes working software over theoretical completeness. Every endpoint must be usable from day one.

---

## Critical Design Decisions

### 1. Customer Onboarding (Bootstrap Problem - SOLVED)

The previous implementation had a chicken-and-egg problem: you needed an API key to create an API key. This spec solves it with a clear separation:

**Two authentication paths:**

1. **Admin Secret** - A server-side secret (`APTLY_ADMIN_SECRET` env var) used ONLY for:
   - Creating new customers (`POST /v1/admin/customers`)
   - Initial API key generation for a customer

2. **Customer API Keys** - Standard `apt_live_*` / `apt_test_*` keys used for:
   - All customer-facing operations
   - Chat completions, audit logs, managing their own additional API keys

**Onboarding Flow:**
```
1. Admin creates customer:
   POST /v1/admin/customers
   X-Admin-Secret: {APTLY_ADMIN_SECRET}
   Body: { "email": "...", "company_name": "..." }

   Returns: { "customer_id": "...", "api_key": "apt_live_..." }

2. Customer uses their API key for everything else
```

### 2. Customer-Provided LLM Keys

Customers pass their own LLM provider API keys in each request. Aptly never stores them.

```json
{
  "model": "gpt-4",
  "messages": [...],
  "api_keys": {
    "openai": "sk-..."
  }
}
```

**Why:**
- Reduces liability (we don't hold their keys)
- Customers control their own billing with providers
- Simpler security model

### 3. Rate Limiting (Scalable from Day One)

Use Redis for rate limiting. In-memory caching breaks with multiple workers.

```python
# Required: REDIS_URL environment variable
# Rate limits stored in Redis with TTL
# Key format: rate_limit:{customer_id}:{hour_bucket}
```

### 4. Supabase Client (Not ORM)

Use the Supabase Python client directly instead of SQLAlchemy. Simpler, less boilerplate, and leverages Supabase's built-in features.

```python
# Simple queries with Supabase client
from src.supabase_client import supabase

# Insert
result = supabase.table("customers").insert({"email": "...", "company_name": "..."}).execute()

# Select
result = supabase.table("customers").select("*").eq("id", customer_id).single().execute()

# Update
result = supabase.table("customers").update({"plan": "pro"}).eq("id", customer_id).execute()
```

**If Redis is unavailable:** Fall back to allowing requests (fail open) but log a warning. Don't break the service.

### 5. Simplified Scopes

Remove the `scopes` field from API keys entirely. All API keys have full access to their customer's resources. Scopes add complexity without clear value for an MVP.

**If you need limited access later:** Add it as a v2 feature with a clear use case.

---

## Database Schema

### Tables

```sql
-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    plan VARCHAR(50) DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
    compliance_frameworks TEXT[] DEFAULT '{}',
    retention_days INTEGER DEFAULT 2555,
    pii_redaction_mode VARCHAR(20) DEFAULT 'mask' CHECK (pii_redaction_mode IN ('mask', 'hash', 'remove')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- API Keys table (simplified - no scopes)
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    rate_limit_per_hour INTEGER DEFAULT 1000,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash) WHERE NOT is_revoked;
CREATE INDEX idx_api_keys_customer ON api_keys(customer_id);

-- Audit Logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    user_id VARCHAR(255),

    -- Request metadata
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,

    -- Redacted content (NEVER store original PII)
    request_data JSONB NOT NULL,
    response_data JSONB,

    -- PII detection results
    pii_detected JSONB DEFAULT '[]',

    -- Metrics
    tokens_input INTEGER,
    tokens_output INTEGER,
    latency_ms INTEGER,
    cost_usd DECIMAL(10, 6),

    -- Compliance
    compliance_framework VARCHAR(20),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_customer_time ON audit_logs(customer_id, created_at DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(customer_id, user_id, created_at DESC);

-- Immutability: audit logs cannot be updated or deleted
CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable and cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_logs_immutable
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();
```

### Row-Level Security

```sql
-- Enable RLS
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Backend uses service role key which bypasses RLS
-- These policies are for direct Supabase access (dashboard)

CREATE POLICY "customers_own_data" ON customers
    FOR ALL USING (id = auth.uid());

CREATE POLICY "api_keys_own_data" ON api_keys
    FOR ALL USING (customer_id = auth.uid());

CREATE POLICY "audit_logs_own_data" ON audit_logs
    FOR SELECT USING (customer_id = auth.uid());
```

---

## API Endpoints

### Base URL
```
Production: https://api.aptly.dev
Local:      http://localhost:8000
```

### Authentication

**Admin endpoints:** `X-Admin-Secret` header
**Customer endpoints:** `Authorization: Bearer apt_live_*` or `apt_test_*`

---

### Health Check

```http
GET /v1/health

Response 200:
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

No authentication required.

---

### Admin: Create Customer

**This is the ONLY way to create a new customer.**

```http
POST /v1/admin/customers
X-Admin-Secret: {APTLY_ADMIN_SECRET}
Content-Type: application/json

Request:
{
  "email": "admin@healthtech.com",
  "company_name": "HealthTech Inc",
  "plan": "pro",
  "compliance_frameworks": ["HIPAA"]
}

Response 201:
{
  "customer": {
    "id": "cus_abc123",
    "email": "admin@healthtech.com",
    "company_name": "HealthTech Inc",
    "plan": "pro",
    "compliance_frameworks": ["HIPAA"],
    "retention_days": 2555,
    "pii_redaction_mode": "mask",
    "created_at": "2026-01-24T10:00:00Z"
  },
  "api_key": {
    "id": "key_xyz789",
    "key": "apt_live_abc123def456...",  // ONLY SHOWN ONCE
    "key_prefix": "apt_live_abc123",
    "name": "Default API Key",
    "created_at": "2026-01-24T10:00:00Z"
  }
}

Errors:
400 - Invalid request body
401 - Missing or invalid admin secret
409 - Customer with email already exists
```

---

### Admin: List Customers

```http
GET /v1/admin/customers?limit=50&offset=0
X-Admin-Secret: {APTLY_ADMIN_SECRET}

Response 200:
{
  "customers": [...],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

---

### Admin: Get Customer

```http
GET /v1/admin/customers/{customer_id}
X-Admin-Secret: {APTLY_ADMIN_SECRET}

Response 200:
{
  "customer": {...},
  "api_keys": [
    {
      "id": "key_xyz789",
      "key_prefix": "apt_live_abc123",
      "name": "Default API Key",
      "is_revoked": false,
      "created_at": "...",
      "last_used_at": "..."
    }
  ],
  "usage": {
    "requests_this_month": 1523,
    "tokens_this_month": 245000
  }
}
```

---

### Admin: Create API Key for Customer

```http
POST /v1/admin/customers/{customer_id}/api-keys
X-Admin-Secret: {APTLY_ADMIN_SECRET}
Content-Type: application/json

Request:
{
  "name": "Production Key",
  "rate_limit_per_hour": 5000
}

Response 201:
{
  "id": "key_abc123",
  "key": "apt_live_newkey...",  // ONLY SHOWN ONCE
  "key_prefix": "apt_live_newk",
  "name": "Production Key",
  "rate_limit_per_hour": 5000,
  "created_at": "2026-01-24T10:00:00Z"
}
```

---

### Chat Completions (Main Endpoint)

OpenAI-compatible proxy endpoint.

```http
POST /v1/chat/completions
Authorization: Bearer apt_live_abc123...
Content-Type: application/json

Request:
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Patient John Smith has diabetes."}
  ],
  "api_keys": {
    "openai": "sk-proj-..."
  },
  "user": "user_123",
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}

Response 200 (non-streaming):
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1706097600,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I understand PERSON_A has CONDITION_A..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 50,
    "total_tokens": 75
  },
  "aptly": {
    "audit_log_id": "log_xyz789",
    "pii_detected": true,
    "pii_entities": ["PERSON", "MEDICAL_CONDITION"],
    "compliance_framework": "HIPAA",
    "latency_ms": 1234
  }
}

Response 200 (streaming):
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","choices":[{"delta":{"content":"I"}}]}
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","choices":[{"delta":{"content":" understand"}}]}
...
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","choices":[{"delta":{},"finish_reason":"stop"}],"aptly":{"audit_log_id":"log_xyz789","pii_detected":true}}
data: [DONE]

Errors:
400 - Invalid request (missing api_keys, invalid model, etc.)
401 - Invalid or missing API key
402 - LLM provider rejected key (payment required)
429 - Rate limit exceeded
500 - Internal error
502 - LLM provider error
```

**Required fields:**
- `model` - The model to use (gpt-4, claude-3-opus, etc.)
- `messages` - Array of message objects
- `api_keys` - Object with provider keys (at minimum, the key for the detected provider)

**Optional fields:**
- `user` - End-user identifier for audit logs
- `stream` - Enable streaming (default: false)
- `temperature`, `max_tokens`, etc. - Passed through to provider

---

### List API Keys (Customer)

Customers can list and manage their own API keys.

```http
GET /v1/api-keys
Authorization: Bearer apt_live_abc123...

Response 200:
{
  "api_keys": [
    {
      "id": "key_xyz789",
      "key_prefix": "apt_live_abc123",
      "name": "Default API Key",
      "rate_limit_per_hour": 1000,
      "is_revoked": false,
      "created_at": "2026-01-24T10:00:00Z",
      "last_used_at": "2026-01-24T14:30:00Z"
    }
  ]
}
```

---

### Create API Key (Customer)

Customers can create additional API keys for themselves.

```http
POST /v1/api-keys
Authorization: Bearer apt_live_abc123...
Content-Type: application/json

Request:
{
  "name": "CI/CD Pipeline Key"
}

Response 201:
{
  "id": "key_newkey",
  "key": "apt_live_newkey...",  // ONLY SHOWN ONCE
  "key_prefix": "apt_live_newk",
  "name": "CI/CD Pipeline Key",
  "rate_limit_per_hour": 1000,
  "created_at": "2026-01-24T10:00:00Z"
}
```

---

### Revoke API Key (Customer)

```http
DELETE /v1/api-keys/{key_id}
Authorization: Bearer apt_live_abc123...

Response 204: (no content)

Errors:
404 - Key not found or doesn't belong to customer
409 - Cannot revoke the key you're currently using
```

---

### Query Audit Logs

```http
GET /v1/logs?start_date=2026-01-01&end_date=2026-01-24&user_id=user_123&limit=50&page=1
Authorization: Bearer apt_live_abc123...

Response 200:
{
  "logs": [
    {
      "id": "log_abc123",
      "user_id": "user_123",
      "provider": "openai",
      "model": "gpt-4",
      "tokens_input": 25,
      "tokens_output": 50,
      "latency_ms": 1234,
      "cost_usd": 0.00225,
      "pii_detected": ["PERSON", "MEDICAL_CONDITION"],
      "compliance_framework": "HIPAA",
      "created_at": "2026-01-24T14:30:00Z"
    }
  ],
  "pagination": {
    "total": 1523,
    "page": 1,
    "per_page": 50,
    "total_pages": 31
  }
}

Query Parameters:
- start_date: ISO date (YYYY-MM-DD), default: 30 days ago
- end_date: ISO date, default: today
- user_id: Filter by end-user ID
- model: Filter by model name
- limit: Results per page (1-100, default: 50)
- page: Page number (default: 1)
```

---

### Get Audit Log Detail

```http
GET /v1/logs/{log_id}
Authorization: Bearer apt_live_abc123...

Response 200:
{
  "id": "log_abc123",
  "user_id": "user_123",
  "provider": "openai",
  "model": "gpt-4",
  "request_data": {
    "messages": [
      {"role": "user", "content": "Patient PERSON_A has CONDITION_A."}
    ]
  },
  "response_data": {
    "content": "I understand PERSON_A has CONDITION_A..."
  },
  "pii_detected": [
    {"type": "PERSON", "replacement": "PERSON_A", "confidence": 0.95},
    {"type": "MEDICAL_CONDITION", "replacement": "CONDITION_A", "confidence": 0.87}
  ],
  "tokens_input": 25,
  "tokens_output": 50,
  "latency_ms": 1234,
  "cost_usd": 0.00225,
  "compliance_framework": "HIPAA",
  "created_at": "2026-01-24T14:30:00Z"
}

Errors:
404 - Log not found or doesn't belong to customer
```

---

### Get Customer Profile

```http
GET /v1/me
Authorization: Bearer apt_live_abc123...

Response 200:
{
  "id": "cus_abc123",
  "email": "admin@healthtech.com",
  "company_name": "HealthTech Inc",
  "plan": "pro",
  "compliance_frameworks": ["HIPAA"],
  "retention_days": 2555,
  "pii_redaction_mode": "mask",
  "created_at": "2026-01-24T10:00:00Z",
  "usage": {
    "requests_this_month": 1523,
    "tokens_this_month": 245000,
    "rate_limit_per_hour": 1000,
    "requests_this_hour": 42
  }
}
```

---

### Update Customer Settings

```http
PATCH /v1/me
Authorization: Bearer apt_live_abc123...
Content-Type: application/json

Request:
{
  "pii_redaction_mode": "hash",
  "compliance_frameworks": ["HIPAA", "GDPR"]
}

Response 200:
{
  "id": "cus_abc123",
  "email": "admin@healthtech.com",
  ...updated fields...
}

Errors:
400 - Invalid field values
```

---

## PII Detection & Redaction

### Implementation

Use Microsoft Presidio for PII detection.

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

SUPPORTED_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "US_SSN",
    "CREDIT_CARD",
    "IBAN_CODE",
    "MEDICAL_LICENSE",
    "US_PASSPORT",
    "LOCATION",
    "DATE_TIME",
]

class PIIRedactor:
    def __init__(self, mode: str = "mask"):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.mode = mode

    def redact(self, text: str) -> tuple[str, list[dict]]:
        """
        Redact PII from text.

        Returns:
            (redacted_text, list of detected entities)
        """
        # Detect PII
        results = self.analyzer.analyze(
            text=text,
            entities=SUPPORTED_ENTITIES,
            language="en"
        )

        # Track replacements for consistent labeling
        entity_counts = {}
        detections = []

        for result in sorted(results, key=lambda x: x.start):
            entity_type = result.entity_type
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            label = chr(ord('A') + entity_counts[entity_type] - 1)

            if self.mode == "mask":
                replacement = f"{entity_type}_{label}"
            elif self.mode == "hash":
                import hashlib
                hash_val = hashlib.sha256(text[result.start:result.end].encode()).hexdigest()[:8]
                replacement = f"HASH_{hash_val}"
            else:  # remove
                replacement = "[REDACTED]"

            detections.append({
                "type": entity_type,
                "replacement": replacement,
                "confidence": result.score,
                "start": result.start,
                "end": result.end
            })

        # Apply redactions (in reverse order to preserve positions)
        redacted = text
        for detection in sorted(detections, key=lambda x: x["start"], reverse=True):
            redacted = redacted[:detection["start"]] + detection["replacement"] + redacted[detection["end"]:]

        return redacted, detections
```

### Redaction Modes

| Mode | Input | Output |
|------|-------|--------|
| mask | "John Smith" | "PERSON_A" |
| hash | "John Smith" | "HASH_a3f2c1b9" |
| remove | "John Smith" | "[REDACTED]" |

---

## LLM Routing

### Provider Detection

```python
def detect_provider(model: str) -> str:
    """Detect LLM provider from model name."""
    model_lower = model.lower()

    if model_lower.startswith(("gpt", "o1", "o3")):
        return "openai"
    elif model_lower.startswith("claude"):
        return "anthropic"
    elif model_lower.startswith("gemini"):
        return "google"
    elif model_lower.startswith("command"):
        return "cohere"
    elif "llama" in model_lower or "mixtral" in model_lower:
        return "together"
    else:
        raise ValueError(f"Unknown model: {model}")
```

### LiteLLM Integration

```python
import litellm
from litellm import acompletion

async def call_llm(
    model: str,
    messages: list[dict],
    api_key: str,
    stream: bool = False,
    **kwargs
) -> dict:
    """Call LLM provider via LiteLLM."""

    response = await acompletion(
        model=model,
        messages=messages,
        api_key=api_key,
        stream=stream,
        **kwargs
    )

    return response
```

### Streaming Support

Streaming MUST be implemented from the start. Use Server-Sent Events (SSE).

```python
from fastapi import Response
from fastapi.responses import StreamingResponse

async def stream_completion(
    model: str,
    messages: list[dict],
    api_key: str,
    **kwargs
):
    """Stream LLM response as SSE."""

    response = await acompletion(
        model=model,
        messages=messages,
        api_key=api_key,
        stream=True,
        **kwargs
    )

    async def generate():
        async for chunk in response:
            yield f"data: {json.dumps(chunk.dict())}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

---

## Rate Limiting

### Redis-Based Implementation

```python
import redis.asyncio as redis
from datetime import datetime

class RateLimiter:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def check_rate_limit(
        self,
        customer_id: str,
        limit_per_hour: int
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Returns:
            (allowed, current_count, limit)
        """
        hour_bucket = datetime.utcnow().strftime("%Y-%m-%d-%H")
        key = f"rate_limit:{customer_id}:{hour_bucket}"

        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, 3600)  # 1 hour TTL

            allowed = current <= limit_per_hour
            return allowed, current, limit_per_hour

        except redis.RedisError:
            # Redis unavailable - fail open but log warning
            logger.warning(f"Redis unavailable for rate limiting, allowing request")
            return True, 0, limit_per_hour
```

### Rate Limit Headers

Include rate limit info in response headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 958
X-RateLimit-Reset: 1706101200
```

---

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "type": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Limit: 1000 requests per hour.",
    "code": "RATE_LIMIT_EXCEEDED",
    "details": {
      "limit": 1000,
      "current": 1001,
      "reset_at": "2026-01-24T15:00:00Z"
    }
  }
}
```

### Error Codes

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | INVALID_REQUEST | Missing or invalid parameters |
| 401 | INVALID_API_KEY | API key missing or invalid |
| 401 | INVALID_ADMIN_SECRET | Admin secret missing or invalid |
| 402 | PAYMENT_REQUIRED | LLM provider rejected API key |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Resource already exists |
| 429 | RATE_LIMIT_EXCEEDED | Rate limit exceeded |
| 500 | INTERNAL_ERROR | Server error |
| 502 | PROVIDER_ERROR | LLM provider error |
| 503 | SERVICE_UNAVAILABLE | Service temporarily unavailable |

---

## Configuration

### Environment Variables

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...      # Service role key (bypasses RLS)
REDIS_URL=redis://localhost:6379/0
APTLY_ADMIN_SECRET=your-secure-admin-secret-here

# Optional
ENVIRONMENT=production          # development, staging, production
LOG_LEVEL=info                  # debug, info, warning, error
PORT=8000
SENTRY_DSN=                     # Error tracking
```

### Config Class

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Required
    supabase_url: str
    supabase_service_key: str
    redis_url: str
    aptly_admin_secret: str

    # Optional with defaults
    environment: str = "development"
    log_level: str = "info"
    port: int = 8000
    sentry_dsn: str | None = None

    # Rate limits by plan
    rate_limit_free: int = 100
    rate_limit_pro: int = 1000
    rate_limit_enterprise: int = 10000

    class Config:
        env_file = ".env"
```

### Supabase Client

```python
# src/supabase_client.py
from supabase import create_client, Client
from src.config import settings

supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_key
)
```

---

## Project Structure

```
aptly/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app and routes
│   ├── config.py               # Settings and configuration
│   ├── supabase_client.py      # Supabase client initialization
│   ├── auth.py                 # Authentication (admin + API key)
│   ├── rate_limiter.py         # Redis rate limiting
│   ├── llm_router.py           # LiteLLM integration
│   └── compliance/
│       ├── __init__.py
│       ├── pii_redactor.py     # Presidio PII detection
│       └── audit_logger.py     # Audit log writing
├── tests/
│   ├── conftest.py             # Fixtures
│   ├── test_auth.py
│   ├── test_chat_completions.py  # CRITICAL - test the main endpoint!
│   ├── test_pii_detection.py
│   ├── test_rate_limiting.py
│   ├── test_audit_logs.py
│   └── test_admin_endpoints.py
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── README.md
```

---

## Testing Requirements

### Test Categories

1. **Unit Tests** - Individual functions
2. **Integration Tests** - Database operations
3. **API Tests** - Full endpoint testing
4. **E2E Tests** - Complete request flow

### Critical Test Cases

The following MUST have test coverage:

```python
# test_chat_completions.py - THE MAIN FEATURE

def test_chat_completion_basic():
    """Basic chat completion works."""

def test_chat_completion_pii_redaction():
    """PII is detected and redacted before sending to LLM."""

def test_chat_completion_audit_log_created():
    """Every request creates an audit log entry."""

def test_chat_completion_streaming():
    """Streaming responses work correctly."""

def test_chat_completion_missing_api_keys():
    """Returns 400 when api_keys not provided."""

def test_chat_completion_invalid_model():
    """Returns 400 for unknown model."""

def test_chat_completion_rate_limited():
    """Returns 429 when rate limit exceeded."""

# test_admin_endpoints.py - BOOTSTRAP FLOW

def test_admin_create_customer():
    """Admin can create customer and receives API key."""

def test_admin_create_customer_invalid_secret():
    """Returns 401 for invalid admin secret."""

def test_admin_create_customer_duplicate_email():
    """Returns 409 for duplicate email."""

# test_auth.py - AUTHENTICATION

def test_api_key_validation():
    """Valid API key authenticates successfully."""

def test_api_key_revoked():
    """Revoked API key returns 401."""

def test_api_key_updates_last_used():
    """last_used_at is updated on each request."""
```

### Test Configuration

```python
# conftest.py
import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    with patch("src.supabase_client.supabase") as mock:
        yield mock

@pytest.fixture
async def client(mock_supabase):
    """Test client with mocked Supabase."""
    from src.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def test_customer(mock_supabase):
    """Pre-created test customer with mocked data."""
    customer = {
        "id": "cus_test123",
        "email": "test@example.com",
        "company_name": "Test Co",
        "plan": "pro"
    }
    api_key = "apt_test_abc123def456"
    return {"customer": customer, "api_key": api_key}

@pytest.fixture
async def authenticated_client(client, test_customer):
    """Client with valid API key in headers."""
    client.headers["Authorization"] = f"Bearer {test_customer['api_key']}"
    return client
```

---

## Deployment

### Railway Configuration

```toml
# railway.toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt && python -m spacy download en_core_web_sm"

[deploy]
startCommand = "uvicorn src.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/v1/health"
healthcheckTimeout = 30
```

### Docker (Alternative)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY src/ ./src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Dependencies

```
# requirements.txt

# Web framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6

# Database (Supabase)
supabase>=2.3.0

# Redis (rate limiting)
redis>=5.0.0

# PII Detection
presidio-analyzer>=2.2.0
presidio-anonymizer>=2.2.0
spacy>=3.7.0

# LLM Integration
litellm>=1.21.0

# Configuration
pydantic-settings>=2.1.0
python-dotenv>=1.0.0

# Logging & Monitoring
structlog>=24.1.0
sentry-sdk[fastapi]>=1.39.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
httpx>=0.26.0

# Code quality
ruff>=0.1.15
mypy>=1.8.0
```

---

## Success Criteria

### MVP Complete When:

1. **Bootstrap works**: Admin can create customer, customer gets API key
2. **Chat completions work**: Full request/response cycle with real LLM
3. **PII redaction works**: Sensitive data never reaches LLM
4. **Audit logs work**: Every request logged, queryable
5. **Rate limiting works**: Distributed via Redis
6. **Streaming works**: SSE streaming responses
7. **Tests pass**: >80% coverage, all critical paths tested
8. **Deployed**: Running on Railway with health checks passing

### Verification Commands

```bash
# Run tests
pytest tests/ -v --cov=src --cov-report=term-missing

# Check code quality
ruff check src/ tests/
mypy src/

# Health check
curl https://api.aptly.dev/v1/health

# Create customer (admin)
curl -X POST https://api.aptly.dev/v1/admin/customers \
  -H "X-Admin-Secret: $APTLY_ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "company_name": "Test Co"}'

# Make chat completion
curl -X POST https://api.aptly.dev/v1/chat/completions \
  -H "Authorization: Bearer apt_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}],
    "api_keys": {"openai": "sk-..."}
  }'
```

---

## What's NOT in MVP

Explicitly out of scope for v1:

- Next.js dashboard (API only)
- Stripe billing integration
- PDF report generation
- Bias detection
- Custom compliance rules
- Webhook notifications
- TypeScript SDK (Python only)
- Supabase Auth integration (using custom auth)

These are Phase 2+ features.

---

## Changelog

**v3.0.0 (2026-01-24)**
- Added admin secret authentication for customer creation (fixes bootstrap problem)
- Removed scopes from API keys (simplification)
- Made Redis required for rate limiting (scalability)
- Added streaming as a required feature
- Clarified all endpoint behaviors
- Added comprehensive test requirements
- Removed dashboard/billing from MVP scope
