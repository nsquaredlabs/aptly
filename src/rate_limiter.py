import structlog
import redis.asyncio as redis
from datetime import datetime, timezone
from dataclasses import dataclass

from src.config import settings

logger = structlog.get_logger()


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    current_count: int
    limit: int
    reset_at: datetime


class RateLimiter:
    """Redis-based distributed rate limiter."""

    def __init__(self, redis_url: str | None):
        self.redis_url = redis_url
        self._redis: redis.Redis | None = None
        self._disabled = redis_url is None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _make_reset_at(self) -> datetime:
        """Calculate reset time (top of next hour)."""
        now = datetime.now(timezone.utc)
        reset_at = now.replace(minute=0, second=0, microsecond=0)
        reset_at = reset_at.replace(hour=reset_at.hour + 1) if reset_at.hour < 23 else reset_at.replace(
            day=reset_at.day + 1, hour=0
        )
        return reset_at

    async def check_rate_limit(
        self,
        customer_id: str,
        limit_per_hour: int,
    ) -> RateLimitResult:
        """Check if request is within rate limit."""
        reset_at = self._make_reset_at()

        if self._disabled:
            return RateLimitResult(allowed=True, current_count=0, limit=limit_per_hour, reset_at=reset_at)

        now = datetime.now(timezone.utc)
        hour_bucket = now.strftime("%Y-%m-%d-%H")
        key = f"rate_limit:{customer_id}:{hour_bucket}"

        try:
            r = await self._get_redis()

            async with r.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, 3600)
                results = await pipe.execute()

            current_count = results[0]
            allowed = current_count <= limit_per_hour

            if not allowed:
                logger.warning(
                    "rate_limit_exceeded",
                    customer_id=customer_id,
                    current=current_count,
                    limit=limit_per_hour,
                )

            return RateLimitResult(
                allowed=allowed,
                current_count=current_count,
                limit=limit_per_hour,
                reset_at=reset_at,
            )

        except redis.RedisError as e:
            logger.warning(
                "redis_unavailable_failing_open",
                error=str(e),
                customer_id=customer_id,
            )
            return RateLimitResult(
                allowed=True,
                current_count=0,
                limit=limit_per_hour,
                reset_at=reset_at,
            )

    async def get_current_usage(self, customer_id: str) -> int:
        """Get current usage count for the current hour."""
        if self._disabled:
            return 0

        now = datetime.now(timezone.utc)
        hour_bucket = now.strftime("%Y-%m-%d-%H")
        key = f"rate_limit:{customer_id}:{hour_bucket}"

        try:
            r = await self._get_redis()
            count = await r.get(key)
            return int(count) if count else 0
        except redis.RedisError:
            return 0

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Global rate limiter instance
rate_limiter = RateLimiter(settings.redis_url)


def get_rate_limit_headers(result: RateLimitResult) -> dict[str, str]:
    """Generate rate limit headers for response."""
    return {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(max(0, result.limit - result.current_count)),
        "X-RateLimit-Reset": str(int(result.reset_at.timestamp())),
    }
