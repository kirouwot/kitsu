import hashlib
import time

from app.infra.redis import get_redis

AUTH_RATE_LIMIT_MAX_ATTEMPTS = 5
AUTH_RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MESSAGE = "Too many attempts, try again later"
IDENTIFIER_HASH_LENGTH = 64
IP_FALLBACK_LENGTH = 8


class RateLimitExceededError(Exception):
    """Raised when the rate limit is exceeded for a given key."""


class SoftRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

    async def is_limited(self, key: str, now: float | None = None) -> bool:
        """Check if the given key is rate limited."""
        try:
            redis_client = await get_redis()
            redis_key = f"rate_limit:auth:{key}"
            
            # Get current count
            count_str = await redis_client.get(redis_key)
            count = int(count_str) if count_str else 0
            
            return count >= self.max_attempts
        except Exception:
            # Fail closed: if Redis is unavailable, deny access
            return True

    async def record_failure(self, key: str, now: float | None = None) -> None:
        """Record a failed attempt for the given key."""
        try:
            redis_client = await get_redis()
            redis_key = f"rate_limit:auth:{key}"
            
            # Increment counter atomically
            count = await redis_client.incr(redis_key)
            
            # Set expiry only on first attempt (when count == 1)
            if count == 1:
                await redis_client.expire(redis_key, self.window_seconds)
        except Exception:
            # Fail closed: if Redis is unavailable, silently fail
            # The next is_limited() check will fail closed anyway
            pass

    async def reset(self, key: str) -> None:
        """Reset the rate limit for the given key."""
        try:
            redis_client = await get_redis()
            redis_key = f"rate_limit:auth:{key}"
            await redis_client.delete(redis_key)
        except Exception:
            # Silently fail on reset errors
            pass

    async def clear(self) -> None:
        """Clear all rate limit keys. For testing only."""
        try:
            redis_client = await get_redis()
            # Find all rate limit keys
            cursor = 0
            while True:
                cursor, keys = await redis_client.scan(
                    cursor, match="rate_limit:auth:*", count=100
                )
                if keys:
                    await redis_client.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            # Silently fail on clear errors
            pass


def _make_key(scope: str, identifier: str, client_ip: str | None) -> str:
    if not identifier:
        raise ValueError("identifier is required for rate limiting")
    identifier_hash = hashlib.sha256(identifier.encode()).hexdigest()
    identifier_component = identifier_hash[:IDENTIFIER_HASH_LENGTH]
    ip_component = client_ip or f"unknown-ip-{identifier_hash[:IP_FALLBACK_LENGTH]}"
    return f"{scope}:{ip_component}:{identifier_component}"


async def _ensure_not_limited(limiter: SoftRateLimiter, key: str) -> None:
    if await limiter.is_limited(key):
        raise RateLimitExceededError


auth_rate_limiter = SoftRateLimiter(
    max_attempts=AUTH_RATE_LIMIT_MAX_ATTEMPTS,
    window_seconds=AUTH_RATE_LIMIT_WINDOW_SECONDS,
)


async def check_login_rate_limit(email: str, client_ip: str | None = None) -> str:
    key = _make_key("login", email.lower(), client_ip)
    await _ensure_not_limited(auth_rate_limiter, key)
    return key


async def record_login_failure(key: str) -> None:
    await auth_rate_limiter.record_failure(key)


async def reset_login_limit(key: str) -> None:
    await auth_rate_limiter.reset(key)


async def check_refresh_rate_limit(token_identifier: str, client_ip: str | None = None) -> str:
    key = _make_key("refresh", token_identifier, client_ip)
    await _ensure_not_limited(auth_rate_limiter, key)
    return key


async def record_refresh_failure(key: str) -> None:
    await auth_rate_limiter.record_failure(key)


async def reset_refresh_limit(key: str) -> None:
    await auth_rate_limiter.reset(key)

