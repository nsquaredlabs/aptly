# PRD: Production Deployment

**Date:** 2026-01-27
**Status:** Implemented
**Spec Reference:** Deployment section of SPEC.md

## Overview

Deploy the Aptly MVP to production on Railway with all required services configured. This includes Sentry error tracking initialization, Supabase migration execution, Redis provisioning, and end-to-end verification.

## Context

### Current State
- MVP is functionally complete (95 tests passing, 84% coverage)
- All 13 API endpoints implemented and tested
- Railway project exists but not configured
- Supabase project exists but migrations not run
- Sentry integration stubbed but not initialized
- No production verification process

### Gap Being Addressed
- Application is not running in production
- No error tracking for production issues
- No documented deployment process
- No smoke test to verify deployment

## Requirements

### 1. Sentry Integration
1. Add Sentry SDK initialization to `src/main.py` lifespan
2. Configure Sentry to capture unhandled exceptions
3. Add environment and release tags for filtering
4. Exclude health check endpoint from transaction tracking

### 2. Supabase Setup
5. Document migration execution process
6. Create a migration verification query

### 3. Railway Configuration
7. Document all required environment variables
8. Document Redis add-on setup (Railway Redis or Upstash)

### 4. Deployment Verification
9. Create `scripts/smoke_test.py` that verifies:
   - Health check returns healthy
   - Admin can create a customer
   - Customer can authenticate
   - Chat completion endpoint responds (with mock or real LLM key)
10. Create `scripts/verify_deployment.sh` for quick manual checks

### 5. Documentation
11. Create `DEPLOYMENT.md` with step-by-step production setup guide

## Technical Approach

### Sentry Initialization

```python
# In src/main.py lifespan
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,  # 10% of transactions
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
        ],
    )
```

### Smoke Test Structure

```python
# scripts/smoke_test.py
async def main():
    # 1. Health check
    # 2. Create test customer (with admin secret)
    # 3. List API keys (with customer key)
    # 4. Get customer profile
    # 5. (Optional) Chat completion with real LLM key
    # 6. Query audit logs
    # 7. Clean up: Note customer ID for manual deletion
```

## Files to Modify/Create

### Modified Files
- `src/main.py` - Add Sentry initialization in lifespan
- `src/config.py` - Ensure `sentry_dsn` is Optional[str] with default None

### New Files
- `scripts/smoke_test.py` - Automated deployment verification
- `scripts/verify_deployment.sh` - Quick manual health check
- `DEPLOYMENT.md` - Step-by-step deployment guide

## Database Changes

None - migrations already exist. This PRD documents running them:
- `supabase/migrations/001_initial_schema.sql`
- `supabase/migrations/002_response_pii.sql`

## Testing Strategy

### Pre-Deployment
- All existing tests pass locally: `pytest tests/ -v`
- Code quality checks pass: `ruff check src/ tests/`

### Post-Deployment
- Health check returns `{"status": "healthy"}`
- Smoke test passes against production URL
- Sentry receives a test error (can trigger manually)

### Critical Verification Points
- `GET /v1/health` returns database: ok, redis: ok
- `POST /v1/admin/customers` creates customer and returns API key
- `GET /v1/me` authenticates with returned API key
- Sentry dashboard shows the application connected

## Dependencies

- Railway account with project created
- Supabase project with service role key
- Redis service (Railway Redis add-on or Upstash)
- Sentry account (free tier sufficient)

## Out of Scope

- Custom domain setup (can be added later)
- CI/CD pipeline (manual deployment for now)
- Auto-scaling configuration
- Database backups (Supabase handles this)
- Log aggregation beyond Sentry

## Success Criteria

- [ ] `GET https://<railway-url>/v1/health` returns `{"status": "healthy"}`
- [ ] Health check shows `database: ok` and `redis: ok`
- [ ] Sentry dashboard shows application connected
- [ ] Smoke test script passes against production URL
- [ ] Admin can create a customer via API
- [ ] Customer can authenticate and call `/v1/me`
- [ ] `DEPLOYMENT.md` documents complete setup process

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Supabase service role key |
| `REDIS_URL` | Yes | Redis connection string |
| `APTLY_ADMIN_SECRET` | Yes | Secret for admin endpoints |
| `ENVIRONMENT` | No | `production` (default: development) |
| `LOG_LEVEL` | No | `info` (default: info) |
| `PORT` | No | Set by Railway automatically |
| `SENTRY_DSN` | No | Sentry project DSN |
