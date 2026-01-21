from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import AsyncContextManager, Callable

from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.infra.redis import DistributedLock, get_async_redis_client

from ..services.autoupdate_service import (
    ParserEpisodeAutoupdateService,
    resolve_update_interval_minutes,
)
from ..services.sync_service import get_parser_settings


DEFAULT_INTERVAL_MINUTES = 60
SCHEDULER_LOCK_KEY = "parser_autoupdate_scheduler"
SCHEDULER_LOCK_TTL = 90  # seconds


logger = logging.getLogger("kitsu.parser.autoupdate")


class ParserAutoupdateScheduler:
    """
    Scheduler for parser auto-update that runs EXACTLY ONCE across all workers.
    Uses Redis distributed lock to ensure single-instance execution.
    """

    def __init__(
        self,
        *,
        session_factory: Callable[
            [], AsyncContextManager[AsyncSession]
        ] = AsyncSessionLocal,
        service_factory: Callable[..., ParserEpisodeAutoupdateService] = (
            ParserEpisodeAutoupdateService
        ),
        redis_client: AsyncRedis | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._service_factory = service_factory
        self._redis = redis_client
        self._task: asyncio.Task[None] | None = None
        self._lock: DistributedLock | None = None
        self._lock_extend_task: asyncio.Task[None] | None = None

    async def _ensure_redis(self) -> AsyncRedis:
        """Lazy initialize Redis client."""
        if self._redis is None:
            try:
                self._redis = get_async_redis_client()
                await self._redis.ping()
            except (RedisError, ValueError) as exc:
                logger.error("Redis unavailable for scheduler: %s", exc)
                raise
        return self._redis

    async def start(self) -> None:
        """
        Start scheduler if lock can be acquired.
        Only ONE instance across all workers will start.
        """
        if self._task and not self._task.done():
            return

        try:
            # Try to acquire distributed lock
            redis = await self._ensure_redis()
            self._lock = DistributedLock(
                redis, SCHEDULER_LOCK_KEY, ttl_seconds=SCHEDULER_LOCK_TTL
            )

            if await self._lock.acquire():
                logger.info(
                    "Scheduler lock acquired - starting ParserAutoupdateScheduler"
                )
                self._task = asyncio.create_task(self._loop())
                # Start lock extension task
                self._lock_extend_task = asyncio.create_task(self._extend_lock_loop())
            else:
                logger.info(
                    "Scheduler lock NOT acquired - another worker is running the scheduler"
                )

        except (RedisError, ValueError) as exc:
            logger.warning(
                "Failed to acquire scheduler lock (Redis unavailable): %s. Scheduler will NOT start.",
                exc,
            )

    async def stop(self) -> None:
        """Stop scheduler and release lock."""
        # Stop lock extension
        if self._lock_extend_task:
            self._lock_extend_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._lock_extend_task
            self._lock_extend_task = None

        # Stop main task
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

        # Release lock
        if self._lock:
            await self._lock.release()
            logger.info("Scheduler lock released")
            self._lock = None

    async def run_once(self, *, force: bool = False) -> dict[str, object]:
        """Run autoupdate once (for manual triggers or testing)."""
        async with self._session_factory() as session:
            settings = await get_parser_settings(session)
            interval = resolve_update_interval_minutes(settings)
            if not settings.enable_autoupdate and not force:
                return {"status": "disabled", "interval_minutes": interval}
            service = self._service_factory(session=session, settings=settings)
            summary = await service.run(force=True)
            summary["interval_minutes"] = interval
            return summary

    async def _extend_lock_loop(self) -> None:
        """Periodically extend lock to prevent expiration."""
        if not self._lock:
            return

        try:
            while True:
                # Extend lock every TTL/2 seconds
                await asyncio.sleep(SCHEDULER_LOCK_TTL / 2)
                if not await self._lock.extend():
                    logger.error("Failed to extend scheduler lock - stopping scheduler")
                    # Stop main task if lock extension fails
                    if self._task and not self._task.done():
                        self._task.cancel()
                    break
        except asyncio.CancelledError:
            return

    async def _loop(self) -> None:
        """Main scheduler loop."""
        while True:
            result = await self.run_once()
            interval = int(result.get("interval_minutes") or DEFAULT_INTERVAL_MINUTES)
            await asyncio.sleep(interval * 60)


parser_autoupdate_scheduler = ParserAutoupdateScheduler()
