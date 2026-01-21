"""Redis client for distributed coordination.

This module provides async Redis operations for:
- Distributed locks
- Rate limiting counters
- Job coordination

No global state is stored in memory - all coordination uses Redis.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from redis.asyncio import Redis as AsyncRedis, from_url as async_from_url
from redis import Redis as SyncRedis, from_url as sync_from_url
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client for distributed coordination.
    
    This client provides methods for distributed locking and coordination
    across multiple worker instances without storing any state in memory.
    """
    
    def __init__(self, redis_url: str) -> None:
        """Initialize Redis client.
        
        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
        """
        self._redis_url = redis_url
        self._redis: AsyncRedis | None = None
    
    async def connect(self) -> None:
        """Establish Redis connection."""
        if self._redis is None:
            self._redis = async_from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("Redis connection established")
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
            logger.info("Redis connection closed")
    
    async def _ensure_connected(self) -> AsyncRedis:
        """Ensure Redis is connected and return the client."""
        if self._redis is None:
            await self.connect()
        assert self._redis is not None
        return self._redis
    
    @asynccontextmanager
    async def acquire_lock(
        self,
        key: str,
        ttl_seconds: int = 60,
        retry_interval: float = 1.0,
    ) -> AsyncGenerator[bool, None]:
        """Acquire a distributed lock using Redis SET NX EX.
        
        This implements a simple distributed lock that automatically expires.
        Only one worker can hold the lock at a time.
        
        Args:
            key: Lock key
            ttl_seconds: Lock TTL (auto-release on crash)
            retry_interval: How long to wait before retrying (not used for non-blocking)
        
        Yields:
            True if lock was acquired, False otherwise
        """
        redis = await self._ensure_connected()
        lock_key = f"lock:{key}"
        
        try:
            # Try to acquire lock (non-blocking)
            # SET key value NX EX ttl
            acquired = await redis.set(lock_key, "1", nx=True, ex=ttl_seconds)
            yield bool(acquired)
        finally:
            # Release lock if we acquired it
            if acquired:
                try:
                    await redis.delete(lock_key)
                except RedisError:
                    # Lock will auto-expire anyway
                    pass
    
    async def try_acquire_lock(self, key: str, ttl_seconds: int = 60) -> bool:
        """Try to acquire a lock without blocking.
        
        Args:
            key: Lock key
            ttl_seconds: Lock TTL (auto-release on crash)
            
        Returns:
            True if lock was acquired, False otherwise
        """
        redis = await self._ensure_connected()
        lock_key = f"lock:{key}"
        acquired = await redis.set(lock_key, "1", nx=True, ex=ttl_seconds)
        return bool(acquired)
    
    async def release_lock(self, key: str) -> None:
        """Release a lock.
        
        Args:
            key: Lock key
        """
        redis = await self._ensure_connected()
        lock_key = f"lock:{key}"
        await redis.delete(lock_key)
    
    async def extend_lock(self, key: str, ttl_seconds: int = 60) -> bool:
        """Extend the TTL of an existing lock.
        
        Args:
            key: Lock key
            ttl_seconds: New TTL
            
        Returns:
            True if lock exists and was extended, False otherwise
        """
        redis = await self._ensure_connected()
        lock_key = f"lock:{key}"
        result = await redis.expire(lock_key, ttl_seconds)
        return bool(result)
    
    async def increment_counter(
        self,
        key: str,
        ttl_seconds: int | None = None,
    ) -> int:
        """Increment a counter and optionally set TTL.
        
        Used for rate limiting - increments counter and sets expiry.
        
        Args:
            key: Counter key
            ttl_seconds: TTL for the counter (set only on first increment)
            
        Returns:
            New counter value
        """
        redis = await self._ensure_connected()
        
        # Use pipeline for atomic operations
        async with redis.pipeline(transaction=True) as pipe:
            # Increment counter
            pipe.incr(key)
            
            # Set TTL only if this is the first increment
            # (EXPIRE returns 0 if key doesn't exist after INCR, but we just created it)
            if ttl_seconds is not None:
                # Use NX flag to only set expiry if not already set
                # This is a pipeline, so we need to check existence first
                pipe.expire(key, ttl_seconds, nx=True)
            
            results = await pipe.execute()
            return int(results[0])
    
    async def get_counter(self, key: str) -> int:
        """Get current counter value.
        
        Args:
            key: Counter key
            
        Returns:
            Counter value (0 if not exists)
        """
        redis = await self._ensure_connected()
        value = await redis.get(key)
        return int(value) if value else 0
    
    async def delete_counter(self, key: str) -> None:
        """Delete a counter.
        
        Args:
            key: Counter key
        """
        redis = await self._ensure_connected()
        await redis.delete(key)
    
    async def set_value(
        self,
        key: str,
        value: str,
        ttl_seconds: int | None = None,
    ) -> None:
        """Set a string value with optional TTL.
        
        Args:
            key: Key
            value: Value
            ttl_seconds: Optional TTL
        """
        redis = await self._ensure_connected()
        if ttl_seconds:
            await redis.setex(key, ttl_seconds, value)
        else:
            await redis.set(key, value)
    
    async def get_value(self, key: str) -> str | None:
        """Get a string value.
        
        Args:
            key: Key
            
        Returns:
            Value or None if not exists
        """
        redis = await self._ensure_connected()
        return await redis.get(key)
    
    async def delete_value(self, key: str) -> None:
        """Delete a value.
        
        Args:
            key: Key
        """
        redis = await self._ensure_connected()
        await redis.delete(key)
    
    async def check_job_running(self, job_id: str, ttl_seconds: int = 300) -> bool:
        """Check if a job is already running and mark it if not.
        
        This is used for job deduplication across workers.
        
        Args:
            job_id: Unique job identifier
            ttl_seconds: How long the job is expected to run (max)
            
        Returns:
            True if job is now running (caller should proceed),
            False if job was already running (caller should skip)
        """
        redis = await self._ensure_connected()
        job_key = f"job:running:{job_id}"
        
        # Try to set the job marker with NX (only if not exists)
        acquired = await redis.set(job_key, "1", nx=True, ex=ttl_seconds)
        return bool(acquired)
    
    async def mark_job_complete(self, job_id: str) -> None:
        """Mark a job as complete (remove running marker).
        
        Args:
            job_id: Unique job identifier
        """
        redis = await self._ensure_connected()
        job_key = f"job:running:{job_id}"
        await redis.delete(job_key)


class SyncRedisClient:
    """Synchronous Redis client for use in sync contexts (e.g., rate limiting).
    
    This client provides synchronous Redis operations for cases where
    async operations are not practical.
    """
    
    def __init__(self, redis_url: str) -> None:
        """Initialize sync Redis client.
        
        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
        """
        self._redis_url = redis_url
        self._redis: SyncRedis | None = None
    
    def connect(self) -> None:
        """Establish Redis connection."""
        if self._redis is None:
            self._redis = sync_from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("Sync Redis connection established")
    
    def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            self._redis.close()
            self._redis = None
            logger.info("Sync Redis connection closed")
    
    def _ensure_connected(self) -> SyncRedis:
        """Ensure Redis is connected and return the client."""
        if self._redis is None:
            self.connect()
        assert self._redis is not None
        return self._redis
    
    def increment_counter(
        self,
        key: str,
        ttl_seconds: int | None = None,
    ) -> int:
        """Increment a counter and optionally set TTL.
        
        Args:
            key: Counter key
            ttl_seconds: TTL for the counter (set only on first increment)
            
        Returns:
            New counter value
        """
        redis = self._ensure_connected()
        
        # Use pipeline for atomic operations
        with redis.pipeline(transaction=True) as pipe:
            # Increment counter
            pipe.incr(key)
            
            # Set TTL only if not already set
            if ttl_seconds is not None:
                pipe.expire(key, ttl_seconds, nx=True)
            
            results = pipe.execute()
            return int(results[0])
    
    def get_counter(self, key: str) -> int:
        """Get current counter value.
        
        Args:
            key: Counter key
            
        Returns:
            Counter value (0 if not exists)
        """
        redis = self._ensure_connected()
        value = redis.get(key)
        return int(value) if value else 0
    
    def delete_counter(self, key: str) -> None:
        """Delete a counter.
        
        Args:
            key: Counter key
        """
        redis = self._ensure_connected()
        redis.delete(key)


# Global instances (created at startup, not at import)
_redis_client: RedisClient | None = None
_sync_redis_client: SyncRedisClient | None = None


async def init_redis(redis_url: str) -> RedisClient:
    """Initialize global Redis clients.
    
    Should be called once at application startup.
    
    Args:
        redis_url: Redis connection URL
        
    Returns:
        Redis client instance
    """
    global _redis_client, _sync_redis_client
    _redis_client = RedisClient(redis_url)
    await _redis_client.connect()
    
    _sync_redis_client = SyncRedisClient(redis_url)
    _sync_redis_client.connect()
    
    return _redis_client


async def close_redis() -> None:
    """Close global Redis clients.
    
    Should be called at application shutdown.
    """
    global _redis_client, _sync_redis_client
    if _redis_client is not None:
        await _redis_client.disconnect()
        _redis_client = None
    if _sync_redis_client is not None:
        _sync_redis_client.disconnect()
        _sync_redis_client = None


def get_redis() -> RedisClient:
    """Get the global async Redis client.
    
    Returns:
        Redis client instance
        
    Raises:
        RuntimeError: If Redis client not initialized
    """
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis() first.")
    return _redis_client


def get_sync_redis() -> SyncRedisClient:
    """Get the global sync Redis client.
    
    Returns:
        Sync Redis client instance
        
    Raises:
        RuntimeError: If Redis client not initialized
    """
    if _sync_redis_client is None:
        raise RuntimeError("Sync Redis client not initialized. Call init_redis() first.")
    return _sync_redis_client
