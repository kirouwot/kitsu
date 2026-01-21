import os
from redis import Redis, RedisError


def get_redis_client() -> Redis:
    """Create a synchronous Redis client from environment variable."""
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise ValueError("REDIS_URL environment variable must be set")
    return Redis.from_url(redis_url, decode_responses=True)
