"""Tests for rate limiting using fakeredis."""

import pytest
from datetime import datetime, timezone

import fakeredis.aioredis


@pytest.fixture
def rate_limiter_with_fake_redis():
    """Create a RateLimiter with a fake Redis instance."""
    from src.rate_limiter import RateLimiter

    server = fakeredis.FakeServer()
    fake_redis = fakeredis.aioredis.FakeRedis(
        server=server,
        encoding="utf-8",
        decode_responses=True,
    )

    limiter = RateLimiter("redis://localhost:6379/0")
    limiter._redis = fake_redis

    return limiter, fake_redis


@pytest.mark.asyncio
async def test_rate_limit_allowed(rate_limiter_with_fake_redis):
    """Request within rate limit is allowed."""
    limiter, _ = rate_limiter_with_fake_redis

    result = await limiter.check_rate_limit("cus_test123", 1000)

    assert result.allowed is True
    assert result.current_count == 1
    assert result.limit == 1000


@pytest.mark.asyncio
async def test_rate_limit_exceeded(rate_limiter_with_fake_redis):
    """Request exceeding rate limit is denied."""
    limiter, fake_redis = rate_limiter_with_fake_redis

    # Pre-set the counter to be at the limit
    hour_bucket = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
    key = f"rate_limit:cus_test123:{hour_bucket}"
    await fake_redis.set(key, "1000")

    result = await limiter.check_rate_limit("cus_test123", 1000)

    assert result.allowed is False
    assert result.current_count == 1001
    assert result.limit == 1000


@pytest.mark.asyncio
async def test_rate_limit_redis_unavailable():
    """Rate limiter fails open when Redis is unavailable."""
    import redis.asyncio as redis_lib
    from src.rate_limiter import RateLimiter
    from unittest.mock import MagicMock

    limiter = RateLimiter("redis://localhost:6379/0")

    # Create a mock that raises RedisError when pipeline context is used
    mock_redis = MagicMock()

    # Create an async context manager that raises on execute
    class FailingPipeline:
        def incr(self, key):
            pass

        def expire(self, key, ttl):
            pass

        async def execute(self):
            raise redis_lib.RedisError("Connection refused")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    mock_redis.pipeline.return_value = FailingPipeline()
    limiter._redis = mock_redis

    result = await limiter.check_rate_limit("cus_test123", 1000)

    # Should fail open
    assert result.allowed is True
    assert result.current_count == 0


@pytest.mark.asyncio
async def test_rate_limit_first_request(rate_limiter_with_fake_redis):
    """First request in a new hour creates the key with count 1."""
    limiter, fake_redis = rate_limiter_with_fake_redis

    result = await limiter.check_rate_limit("cus_test123", 1000)

    assert result.allowed is True
    assert result.current_count == 1

    # Verify key was created
    hour_bucket = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
    key = f"rate_limit:cus_test123:{hour_bucket}"
    value = await fake_redis.get(key)
    assert value == "1"


@pytest.mark.asyncio
async def test_rate_limit_increments(rate_limiter_with_fake_redis):
    """Multiple requests increment the counter."""
    limiter, _ = rate_limiter_with_fake_redis

    # Make 5 requests
    for i in range(5):
        result = await limiter.check_rate_limit("cus_test123", 1000)
        assert result.allowed is True
        assert result.current_count == i + 1


@pytest.mark.asyncio
async def test_rate_limit_different_customers(rate_limiter_with_fake_redis):
    """Different customers have separate rate limits."""
    limiter, _ = rate_limiter_with_fake_redis

    # Customer A makes 3 requests
    for _ in range(3):
        await limiter.check_rate_limit("cus_a", 1000)

    # Customer B makes 2 requests
    for _ in range(2):
        await limiter.check_rate_limit("cus_b", 1000)

    # Check counts
    result_a = await limiter.check_rate_limit("cus_a", 1000)
    result_b = await limiter.check_rate_limit("cus_b", 1000)

    assert result_a.current_count == 4  # 3 + 1
    assert result_b.current_count == 3  # 2 + 1


@pytest.mark.asyncio
async def test_get_current_usage(rate_limiter_with_fake_redis):
    """Can retrieve current usage count."""
    limiter, _ = rate_limiter_with_fake_redis

    # Make some requests
    await limiter.check_rate_limit("cus_test123", 1000)
    await limiter.check_rate_limit("cus_test123", 1000)
    await limiter.check_rate_limit("cus_test123", 1000)

    usage = await limiter.get_current_usage("cus_test123")

    assert usage == 3


@pytest.mark.asyncio
async def test_get_current_usage_no_key(rate_limiter_with_fake_redis):
    """Current usage returns 0 when no key exists."""
    limiter, _ = rate_limiter_with_fake_redis

    usage = await limiter.get_current_usage("cus_nonexistent")

    assert usage == 0


@pytest.mark.asyncio
async def test_get_current_usage_redis_error():
    """Current usage returns 0 on Redis error."""
    import redis.asyncio as redis_lib
    from src.rate_limiter import RateLimiter
    from unittest.mock import AsyncMock

    limiter = RateLimiter("redis://localhost:6379/0")

    mock_redis = AsyncMock()
    mock_redis.get.side_effect = redis_lib.RedisError("Connection refused")
    limiter._redis = mock_redis

    usage = await limiter.get_current_usage("cus_test123")

    assert usage == 0


def test_rate_limit_headers():
    """Rate limit headers are correctly generated."""
    from src.rate_limiter import get_rate_limit_headers, RateLimitResult

    reset_time = datetime(2026, 1, 26, 15, 0, 0, tzinfo=timezone.utc)

    result = RateLimitResult(
        allowed=True,
        current_count=42,
        limit=1000,
        reset_at=reset_time,
    )

    headers = get_rate_limit_headers(result)

    assert headers["X-RateLimit-Limit"] == "1000"
    assert headers["X-RateLimit-Remaining"] == "958"
    assert "X-RateLimit-Reset" in headers


def test_rate_limit_headers_at_limit():
    """Rate limit headers show 0 remaining when at limit."""
    from src.rate_limiter import get_rate_limit_headers, RateLimitResult

    result = RateLimitResult(
        allowed=False,
        current_count=1000,
        limit=1000,
        reset_at=datetime.now(timezone.utc),
    )

    headers = get_rate_limit_headers(result)

    assert headers["X-RateLimit-Remaining"] == "0"


def test_rate_limit_headers_over_limit():
    """Rate limit headers don't go negative."""
    from src.rate_limiter import get_rate_limit_headers, RateLimitResult

    result = RateLimitResult(
        allowed=False,
        current_count=1500,
        limit=1000,
        reset_at=datetime.now(timezone.utc),
    )

    headers = get_rate_limit_headers(result)

    assert headers["X-RateLimit-Remaining"] == "0"  # Not negative


@pytest.mark.asyncio
async def test_rate_limiter_close(rate_limiter_with_fake_redis):
    """Rate limiter can close its Redis connection."""
    limiter, _ = rate_limiter_with_fake_redis

    # Should not raise
    await limiter.close()

    # Redis should be None after close
    assert limiter._redis is None


@pytest.mark.asyncio
async def test_rate_limit_reset_time(rate_limiter_with_fake_redis):
    """Rate limit result includes proper reset time."""
    limiter, _ = rate_limiter_with_fake_redis

    result = await limiter.check_rate_limit("cus_test123", 1000)

    # Reset time should be in the future (top of next hour)
    assert result.reset_at > datetime.now(timezone.utc)
    # Reset time should be within 1 hour
    time_diff = result.reset_at - datetime.now(timezone.utc)
    assert time_diff.total_seconds() <= 3600
