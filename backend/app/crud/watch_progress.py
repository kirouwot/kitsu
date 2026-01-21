import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.ports.watch_progress import (
    WatchProgressData,
    WatchProgressRepository as WatchProgressRepositoryPort,
)
from ..models.anime import Anime
from ..models.watch_progress import WatchProgress


async def get_watch_progress(
    session: AsyncSession, user_id: uuid.UUID, anime_id: uuid.UUID
) -> WatchProgress | None:
    stmt = select(WatchProgress).where(
        WatchProgress.user_id == user_id, WatchProgress.anime_id == anime_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_watch_progress(
    session: AsyncSession,
    user_id: uuid.UUID,
    anime_id: uuid.UUID,
    episode: int,
    position_seconds: int | None,
    progress_percent: float | None,
    progress_id: uuid.UUID | None = None,
    created_at: datetime | None = None,
    last_watched_at: datetime | None = None,
) -> WatchProgress:
    progress = WatchProgress(
        id=progress_id or uuid.uuid4(),
        user_id=user_id,
        anime_id=anime_id,
        episode=episode,
        position_seconds=position_seconds,
        progress_percent=progress_percent,
    )
    if created_at is not None:
        progress.created_at = created_at
    if last_watched_at is not None:
        progress.last_watched_at = last_watched_at
    session.add(progress)
    await session.flush()
    return progress


async def update_watch_progress(
    session: AsyncSession,
    progress: WatchProgress,
    episode: int,
    position_seconds: int | None,
    progress_percent: float | None,
    last_watched_at: datetime | None = None,
) -> WatchProgress:
    progress.episode = episode
    progress.position_seconds = position_seconds
    progress.progress_percent = progress_percent
    if last_watched_at is not None:
        progress.last_watched_at = last_watched_at
    await session.flush()
    return progress


async def list_watch_progress(
    session: AsyncSession, user_id: uuid.UUID, limit: int
) -> list[WatchProgress]:
    stmt = (
        select(WatchProgress)
        .where(WatchProgress.user_id == user_id)
        .order_by(WatchProgress.last_watched_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


class WatchProgressRepository(WatchProgressRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def anime_exists(self, anime_id: uuid.UUID) -> bool:
        return await self._session.get(Anime, anime_id) is not None

    async def get(
        self, user_id: uuid.UUID, anime_id: uuid.UUID
    ) -> WatchProgressData | None:
        return await get_watch_progress(self._session, user_id, anime_id)

    async def list(self, user_id: uuid.UUID, limit: int) -> list[WatchProgressData]:
        return await list_watch_progress(self._session, user_id=user_id, limit=limit)

    async def add(
        self,
        user_id: uuid.UUID,
        anime_id: uuid.UUID,
        episode: int,
        position_seconds: int | None,
        progress_percent: float | None,
        *,
        progress_id: uuid.UUID | None = None,
        created_at: datetime | None = None,
        last_watched_at: datetime | None = None,
    ) -> WatchProgressData:
        try:
            progress = await create_watch_progress(
                self._session,
                user_id,
                anime_id,
                episode,
                position_seconds,
                progress_percent,
                progress_id=progress_id,
                created_at=created_at,
                last_watched_at=last_watched_at,
            )
            await self._session.commit()
            return progress
        except Exception:
            await self._session.rollback()
            raise

    async def update(
        self,
        progress: WatchProgressData,
        episode: int,
        position_seconds: int | None,
        progress_percent: float | None,
        *,
        last_watched_at: datetime | None = None,
    ) -> WatchProgressData:
        try:
            updated = await update_watch_progress(
                self._session,
                progress,
                episode,
                position_seconds,
                progress_percent,
                last_watched_at=last_watched_at,
            )
            await self._session.commit()
            return updated
        except Exception:
            await self._session.rollback()
            raise
