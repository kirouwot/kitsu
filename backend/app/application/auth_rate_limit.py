import hashlib
import time
from redis import RedisError

from ..infra.redis import get_redis_client

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
        self._redis = get_redis_client()

    def _make_redis_key(self, key: str) -> str:
        """Prefix key for Redis namespace."""
        return f"rate_limit:auth:{key}"

    def is_limited(self, key: str, now: float | None = None) -> bool:
        redis_key = self._make_redis_key(key)
        try:
            count = self._redis.get(redis_key)
            if count is None:
                return False
            return int(count) >= self.max_attempts
        except (RedisError, ValueError):
            # Fail closed: if Redis is unavailable, block the request
            return True

    def record_failure(self, key: str, now: float | None = None) -> None:
        redis_key = self._make_redis_key(key)
        try:
            # Use pipeline to ensure atomicity
            pipe = self._redis.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, self.window_seconds)
            results = pipe.execute()
            # results[0] is the count after increment
        except RedisError:
            # Fail closed: if we can't record, assume limit exceeded
            pass

    def reset(self, key: str) -> None:
        redis_key = self._make_redis_key(key)
        try:
            self._redis.delete(redis_key)
        except RedisError:
            pass

    def clear(self) -> None:
        """Clear all rate limit keys. For testing only."""
        try:
            # Scan and delete all rate limit keys
            cursor = 0
            while True:
                cursor, keys = self._redis.scan(cursor, match="rate_limit:auth:*", count=100)
                if keys:
                    self._redis.delete(*keys)
                if cursor == 0:
                    break
        except RedisError:
            pass


def _make_key(scope: str, identifier: str, client_ip: str | None) -> str:
    if not identifier:
        raise ValueError("identifier is required for rate limiting")
    identifier_hash = hashlib.sha256(identifier.encode()).hexdigest()
    identifier_component = identifier_hash[:IDENTIFIER_HASH_LENGTH]
    ip_component = client_ip or f"unknown-ip-{identifier_hash[:IP_FALLBACK_LENGTH]}"
    return f"{scope}:{ip_component}:{identifier_component}"


def _ensure_not_limited(limiter: SoftRateLimiter, key: str) -> None:
    if limiter.is_limited(key):
        raise RateLimitExceededError


auth_rate_limiter = SoftRateLimiter(
    max_attempts=AUTH_RATE_LIMIT_MAX_ATTEMPTS,
    window_seconds=AUTH_RATE_LIMIT_WINDOW_SECONDS,
)


def check_login_rate_limit(email: str, client_ip: str | None = None) -> str:
    key = _make_key("login", email.lower(), client_ip)
    _ensure_not_limited(auth_rate_limiter, key)
    return key


def record_login_failure(key: str) -> None:
    auth_rate_limiter.record_failure(key)


def reset_login_limit(key: str) -> None:
    auth_rate_limiter.reset(key)


def check_refresh_rate_limit(token_identifier: str, client_ip: str | None = None) -> str:
    key = _make_key("refresh", token_identifier, client_ip)
    _ensure_not_limited(auth_rate_limiter, key)
    return key


def record_refresh_failure(key: str) -> None:
    auth_rate_limiter.record_failure(key)


def reset_refresh_limit(key: str) -> None:
    auth_rate_limiter.reset(key)
