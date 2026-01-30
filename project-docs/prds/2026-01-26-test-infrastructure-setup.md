# PRD: Test Infrastructure Setup

**Date:** 2026-01-26
**Status:** Implemented
**Spec Reference:** Testing Requirements section of SPEC.md

## Overview

Set up proper test infrastructure with Redis to fix the 15 failing tests and achieve the >80% coverage target required by the MVP success criteria. The current test failures stem from complex async Redis mocking that doesn't reliably simulate Redis behavior.

## Context

### Current State
- MVP middleware API is functionally complete (all 13 endpoints implemented)
- Test suite exists with 61 tests total
- 46 tests passing, 15 tests failing
- Coverage at 66% (target: >80%)
- Tests use fragile `AsyncMock` patterns for Redis that fail with async pipeline context managers

### Gap Being Addressed
The test infrastructure is incomplete:
1. No `docker-compose.yml` for local Redis
2. Redis mocking uses complex async patterns that don't work reliably
3. No simple way to run tests locally or in CI/CD
4. MVP success criteria requires ">80% coverage, all critical paths tested"

## Requirements

### Docker Compose Setup
1. Create `docker-compose.yml` with Redis service for local development and testing
2. Add `docker-compose.test.yml` override for test-specific configuration (if needed)
3. Document how to start services for local development

### Test Redis Configuration
4. Add `fakeredis[aioredis]` package for unit tests (in-memory Redis that works with async)
5. Update `tests/conftest.py` to use fakeredis instead of complex AsyncMock patterns
6. Ensure rate limiter tests use the fake Redis instance properly

### Fix Failing Tests
7. Fix all 15 failing tests related to Redis mocking
8. Ensure async pipeline operations work correctly in tests
9. Verify rate limiting behavior is properly tested

### Improve Test Coverage
10. Add missing tests for streaming responses (currently untested error paths)
11. Add tests for Redis connection failure scenarios (fail-open behavior)
12. Add edge case tests for PII redaction
13. Achieve >80% overall test coverage

### CI/CD Preparation
14. Add `pytest.ini` or update `pyproject.toml` with proper pytest configuration
15. Document test commands for CI/CD pipelines
16. Ensure tests can run in isolated environments

## Technical Approach

### Why fakeredis over Docker-only?
- `fakeredis` provides an in-memory Redis implementation that works with `redis-py`
- Tests run faster (no container startup)
- No external dependencies for unit tests
- Docker Redis still useful for integration/manual testing

### Test Fixture Strategy
```python
# conftest.py approach
import fakeredis.aioredis

@pytest.fixture
async def fake_redis():
    """Provide a fake Redis instance for testing."""
    server = fakeredis.FakeServer()
    redis_client = fakeredis.aioredis.FakeRedis(server=server)
    yield redis_client
    await redis_client.close()
```

### Rate Limiter Testing
The rate limiter's `check_rate_limit` method uses Redis pipelines:
```python
async with r.pipeline(transaction=True) as pipe:
    pipe.incr(key)
    pipe.expire(key, 3600)
    results = await pipe.execute()
```

fakeredis supports this pattern natively, eliminating the need for complex mocking.

## Files to Modify/Create

### New Files
- `docker-compose.yml` - Redis and optional Postgres for local dev
- `scripts/test.sh` - Helper script to run tests (optional)

### Modified Files
- `requirements.txt` - Add `fakeredis[aioredis]>=2.20.0`
- `pyproject.toml` - Update pytest configuration if needed
- `tests/conftest.py` - Replace AsyncMock Redis with fakeredis
- `tests/test_rate_limiting.py` - Update to work with fakeredis
- `tests/test_chat_completions.py` - Fix Redis-related test failures

## Database Changes

None - this PRD only affects test infrastructure.

## Testing Strategy

### Unit Tests (with fakeredis)
- Rate limiter increment/decrement
- Rate limit exceeded scenarios
- Fail-open behavior when Redis errors
- TTL expiration behavior

### Integration Tests (with Docker Redis)
- Full request flow with real Redis
- Rate limit headers in responses
- Concurrent request handling

### Critical Test Cases (Must Pass)
- `test_rate_limit_check_allowed` - Request within limit succeeds
- `test_rate_limit_check_exceeded` - Request over limit returns 429
- `test_rate_limit_fail_open` - Redis failure allows request with warning
- `test_rate_limit_headers` - Correct headers in response
- `test_chat_completion_rate_limited` - Full endpoint rate limiting works

### Coverage Targets
- Overall: >80%
- Rate limiter module: >90%
- Auth module: >90%
- Chat completions endpoint: >85%

## Dependencies

- `fakeredis[aioredis]>=2.20.0` - In-memory Redis for testing
- Docker (optional, for integration tests and local development)

## Out of Scope

- Production Redis configuration (already handled by REDIS_URL env var)
- Redis clustering or sentinel setup
- Performance/load testing infrastructure
- Supabase local emulator setup (tests already mock Supabase)

## Success Criteria

- [ ] All 61 tests pass (0 failures)
- [ ] Test coverage >80% overall
- [ ] `pytest tests/ -v` runs successfully without external dependencies
- [ ] Docker compose allows starting Redis for local development
- [ ] CI/CD can run tests in isolated environment
- [ ] Rate limiting behavior is properly verified by tests
