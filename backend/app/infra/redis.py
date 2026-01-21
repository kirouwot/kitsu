import asyncio
import redis.asyncio as redis

from app.config import settings

_redis_client: redis.Redis | None = None
_redis_client_loop: asyncio.AbstractEventLoop | None = None


async def get_redis() -> redis.Redis:
    """Get or create async Redis client for the current event loop."""
    global _redis_client, _redis_client_loop
    
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        # No event loop, this shouldn't happen in async context
        raise
    
    # If the client doesn't exist or was created for a different event loop, create a new one
    if _redis_client is None or _redis_client_loop is not current_loop:
        # Close old client if it exists
        if _redis_client is not None:
            try:
                await _redis_client.aclose()
            except Exception:
                pass
        
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        _redis_client_loop = current_loop
    
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client, _redis_client_loop
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None
        _redis_client_loop = None
