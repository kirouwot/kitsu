import hashlib

from ..infrastructure.redis import get_sync_redis

AUTH_RATE_LIMIT_MAX_ATTEMPTS = 5
AUTH_RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MESSAGE = "Too many attempts, try again later"
IDENTIFIER_HASH_LENGTH = 64
IP_FALLBACK_LENGTH = 8


class RateLimitExceededError(Exception):
    """Raised when the rate limit is exceeded for a given key."""


class RedisRateLimiter:
    """Redis-based rate limiter for distributed environments.
    
    Uses Redis counters with TTL for rate limiting across multiple workers.
    Synchronous API for compatibility with existing code.
    """
    
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

    def is_limited(self, key: str) -> bool:
        """Check if the key is rate limited.
        
        Args:
            key: Rate limit key
            
        Returns:
            True if rate limited, False otherwise
        """
        redis = get_sync_redis()
        counter_key = f"ratelimit:{key}"
        current = redis.get_counter(counter_key)
        return current >= self.max_attempts

    def record_failure(self, key: str) -> None:
        """Record a failed attempt.
        
        Args:
            key: Rate limit key
        """
        redis = get_sync_redis()
        counter_key = f"ratelimit:{key}"
        redis.increment_counter(counter_key, ttl_seconds=self.window_seconds)

    def reset(self, key: str) -> None:
        """Reset the rate limit for a key.
        
        Args:
            key: Rate limit key
        """
        redis = get_sync_redis()
        counter_key = f"ratelimit:{key}"
        redis.delete_counter(counter_key)


def _make_key(scope: str, identifier: str, client_ip: str | None) -> str:
    if not identifier:
        raise ValueError("identifier is required for rate limiting")
    identifier_hash = hashlib.sha256(identifier.encode()).hexdigest()
    identifier_component = identifier_hash[:IDENTIFIER_HASH_LENGTH]
    ip_component = client_ip or f"unknown-ip-{identifier_hash[:IP_FALLBACK_LENGTH]}"
    return f"{scope}:{ip_component}:{identifier_component}"


def _ensure_not_limited(limiter: RedisRateLimiter, key: str) -> None:
    if limiter.is_limited(key):
        raise RateLimitExceededError


auth_rate_limiter = RedisRateLimiter(
    max_attempts=AUTH_RATE_LIMIT_MAX_ATTEMPTS,
    window_seconds=AUTH_RATE_LIMIT_WINDOW_SECONDS,
)


def check_login_rate_limit(email: str, client_ip: str | None = None) -> str:
    """Check if login rate limit is exceeded.
    
    Args:
        email: User email
        client_ip: Client IP address
        
    Returns:
        Rate limit key for future operations
        
    Raises:
        RateLimitExceededError: If rate limit exceeded
    """
    key = _make_key("login", email.lower(), client_ip)
    _ensure_not_limited(auth_rate_limiter, key)
    return key


def record_login_failure(key: str) -> None:
    """Record a failed login attempt.
    
    Args:
        key: Rate limit key from check_login_rate_limit
    """
    auth_rate_limiter.record_failure(key)


def reset_login_limit(key: str) -> None:
    """Reset login rate limit.
    
    Args:
        key: Rate limit key from check_login_rate_limit
    """
    auth_rate_limiter.reset(key)


def check_refresh_rate_limit(token_identifier: str, client_ip: str | None = None) -> str:
    """Check if refresh rate limit is exceeded.
    
    Args:
        token_identifier: Token identifier
        client_ip: Client IP address
        
    Returns:
        Rate limit key for future operations
        
    Raises:
        RateLimitExceededError: If rate limit exceeded
    """
    key = _make_key("refresh", token_identifier, client_ip)
    _ensure_not_limited(auth_rate_limiter, key)
    return key


def record_refresh_failure(key: str) -> None:
    """Record a failed refresh attempt.
    
    Args:
        key: Rate limit key from check_refresh_rate_limit
    """
    auth_rate_limiter.record_failure(key)


def reset_refresh_limit(key: str) -> None:
    """Reset refresh rate limit.
    
    Args:
        key: Rate limit key from check_refresh_rate_limit
    """
    auth_rate_limiter.reset(key)
