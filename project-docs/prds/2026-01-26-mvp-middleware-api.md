# PRD: MVP Middleware API

**Date:** 2026-01-26
**Status:** Draft

## Overview

Implement the complete MVP of Aptly - a compliance-as-a-service middleware API that proxies LLM requests while handling PII redaction and audit logging. This is a greenfield implementation based on the SPEC.md specification.

The MVP provides an OpenAI-compatible API interface for organizations that need to use LLMs while maintaining compliance and protecting sensitive data.

## Requirements

### Core Infrastructure
1. Create `requirements.txt` with all dependencies (FastAPI, Supabase, Redis, Presidio, LiteLLM, etc.)
2. Create `src/config.py` with Pydantic Settings for environment configuration
3. Create `src/supabase_client.py` for Supabase client initialization
4. Create `supabase/migrations/001_initial_schema.sql` with customers, api_keys, and audit_logs tables

### Authentication
5. Create `src/auth.py` with two authentication paths:
   - Admin Secret (`X-Admin-Secret` header) for customer creation
   - API Key authentication (`Authorization: Bearer apt_*`) for customer operations
6. Implement API key validation with hash lookup
7. Update `last_used_at` on each successful API key authentication

### Rate Limiting
8. Create `src/rate_limiter.py` with Redis-based distributed rate limiting
9. Implement fail-open behavior when Redis is unavailable
10. Return rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)

### PII Detection & Redaction
11. Create `src/compliance/pii_redactor.py` using Microsoft Presidio
12. Support three redaction modes: mask, hash, remove
13. Detect standard PII entities (PERSON, EMAIL, SSN, CREDIT_CARD, PHONE, LOCATION, etc.)

### Audit Logging
14. Create `src/compliance/audit_logger.py` for immutable audit log writing
15. Log all chat completion requests with redacted content
16. Track tokens, latency, cost, and PII detection results

### LLM Routing
17. Create `src/llm_router.py` with LiteLLM integration
18. Implement provider detection from model name (gpt-*, claude-*, gemini-*, etc.)
19. Support streaming responses via Server-Sent Events (SSE)

### API Endpoints (src/main.py)
20. `GET /v1/health` - Health check (no auth)
21. `POST /v1/admin/customers` - Create customer (Admin Secret auth)
22. `GET /v1/admin/customers` - List customers (Admin Secret auth)
23. `GET /v1/admin/customers/{id}` - Get customer details (Admin Secret auth)
24. `POST /v1/admin/customers/{id}/api-keys` - Create API key for customer (Admin Secret auth)
25. `POST /v1/chat/completions` - OpenAI-compatible chat completion with PII redaction (API Key auth)
26. `GET /v1/api-keys` - List customer's API keys (API Key auth)
27. `POST /v1/api-keys` - Create additional API key (API Key auth)
28. `DELETE /v1/api-keys/{id}` - Revoke API key (API Key auth)
29. `GET /v1/logs` - Query audit logs with pagination (API Key auth)
30. `GET /v1/logs/{id}` - Get single audit log detail (API Key auth)
31. `GET /v1/me` - Get customer profile (API Key auth)
32. `PATCH /v1/me` - Update customer settings (API Key auth)

### Testing
33. Create `tests/conftest.py` with fixtures for mocked Supabase, Redis, and test client
34. Create `tests/test_chat_completions.py` - Main feature tests including PII redaction
35. Create `tests/test_admin_endpoints.py` - Bootstrap flow tests
36. Create `tests/test_auth.py` - Authentication tests
37. Create `tests/test_pii_detection.py` - PII redaction unit tests
38. Create `tests/test_rate_limiting.py` - Rate limiter tests
39. Create `tests/test_audit_logs.py` - Audit log endpoint tests
40. Achieve >80% test coverage with all critical tests passing

### Deployment Configuration
41. Create `Dockerfile` for containerization
42. Create `railway.toml` for Railway deployment
43. Create `.env.example` with all environment variables documented
44. Create `.gitignore` for Python projects

## Technical Approach

### Architecture
```
Client Request → API Key Auth → Rate Limit Check → PII Redaction → LLM Provider (LiteLLM) → Audit Log → Response
```

### Key Design Decisions
1. **Supabase Client (No ORM)**: Use Supabase Python client directly for simplicity
2. **Redis Required**: Distributed rate limiting with fail-open fallback
3. **Customer-Provided LLM Keys**: Customers pass their own API keys per-request
4. **Presidio for PII**: Microsoft's battle-tested PII detection library with spaCy
5. **LiteLLM for Multi-Provider**: Single interface for OpenAI, Anthropic, Google, Cohere, Together

### API Key Format
- Production: `apt_live_*` (32+ character random suffix)
- Test: `apt_test_*` (32+ character random suffix)
- Store only SHA-256 hash in database, never raw keys

### Error Handling
- Standard error response format with type, message, code, details
- Proper HTTP status codes (400, 401, 402, 404, 409, 429, 500, 502)

## Files to Modify/Create

### Source Files
- `src/__init__.py` - Package init
- `src/config.py` - Settings configuration
- `src/supabase_client.py` - Supabase initialization
- `src/auth.py` - Authentication logic
- `src/rate_limiter.py` - Redis rate limiting
- `src/llm_router.py` - LiteLLM integration
- `src/main.py` - FastAPI app and routes
- `src/compliance/__init__.py` - Compliance package
- `src/compliance/pii_redactor.py` - Presidio PII detection
- `src/compliance/audit_logger.py` - Audit logging

### Test Files
- `tests/__init__.py` - Test package
- `tests/conftest.py` - Shared fixtures
- `tests/test_chat_completions.py` - Chat completion tests
- `tests/test_admin_endpoints.py` - Admin endpoint tests
- `tests/test_auth.py` - Auth tests
- `tests/test_pii_detection.py` - PII tests
- `tests/test_rate_limiting.py` - Rate limit tests
- `tests/test_audit_logs.py` - Audit log tests

### Database
- `supabase/migrations/001_initial_schema.sql` - Initial schema

### Configuration
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project configuration
- `.env.example` - Environment template
- `.gitignore` - Git ignore rules
- `Dockerfile` - Container build
- `railway.toml` - Railway deployment

## Testing Strategy

### Unit Tests
- PII redactor (all three modes)
- Provider detection
- API key generation and hashing
- Rate limit calculations

### Integration Tests
- Database operations (mocked Supabase client)
- Redis rate limiting (mocked Redis)
- Full request flow with mocked LLM

### Critical Test Cases (Must Pass)
- `test_chat_completion_pii_redaction` - PII detected before sending to LLM
- `test_chat_completion_audit_log_created` - Every request logged
- `test_chat_completion_streaming` - SSE streaming works
- `test_admin_create_customer` - Bootstrap flow works
- `test_api_key_validation` - Valid key authenticates

### Coverage Target
- Overall: >80%
- Critical paths: 100%

## Out of Scope

- Next.js dashboard (API only for MVP)
- Stripe billing integration
- PDF report generation
- Bias detection
- Custom compliance rules
- Webhook notifications
- TypeScript/JavaScript SDK
- Supabase Auth integration (using custom auth)
- Multi-language PII detection (English only)
