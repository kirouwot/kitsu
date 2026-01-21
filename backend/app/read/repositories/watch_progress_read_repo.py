"""
READ REPOSITORY: Watch Progress
CQRS-lite: SELECT-only operations for watch progress retrieval

CONSTRAINTS:
- NO writes (add/update/delete/commit/flush)
- NO domain logic
- NO use_case imports
- ONLY SELECT queries
- Returns ONLY DTOs
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.watch_progress import WatchProgress
from ..schemas.watch_progress import WatchProgressDTO


class WatchProgressReadRepository:
    """
    Read-only repository for watch progress operations.
    Fast, safe, scalable read path without domain logic.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize with database session.
        Session is used ONLY for SELECT queries.
        """
        self._session = session

    async def get(
        self, user_id: uuid.UUID, anime_id: uuid.UUID
    ) -> WatchProgressDTO | None:
        """
        Get watch progress for specific user and anime.
        
        Simple SELECT query with no joins.
        
        Args:
            user_id: UUID of the user
            anime_id: UUID of the anime
            
        Returns:
            WatchProgressDTO if found, None otherwise
        """
        stmt = select(WatchProgress).where(
            WatchProgress.user_id == user_id,
            WatchProgress.anime_id == anime_id,
        )

        result = await self._session.execute(stmt)
        progress = result.scalar_one_or_none()

        if progress is None:
            return None

        return WatchProgressDTO(
            anime_id=progress.anime_id,
            episode=progress.episode,
            position_seconds=progress.position_seconds,
            progress_percent=progress.progress_percent,
        )
