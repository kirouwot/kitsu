"""
READ REPOSITORY: User Library
CQRS-lite: SELECT-only operations for user's anime library

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

from ...models.anime import Anime
from ...models.watch_progress import WatchProgress
from ..schemas.user_library import UserLibraryDTO


class UserLibraryReadRepository:
    """
    Read-only repository for user's anime library operations.
    Fast, safe, scalable read path without domain logic.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize with database session.
        Session is used ONLY for SELECT queries.
        """
        self._session = session

    async def get_user_library(self, user_id: uuid.UUID) -> list[UserLibraryDTO]:
        """
        Get user's anime library with watch progress.
        
        Uses join: Anime <- WatchProgress (filtered by user_id)
        Ordered by last watched time descending.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of UserLibraryDTO with anime info and user's progress
        """
        stmt = (
            select(
                Anime.id,
                Anime.title,
                WatchProgress.episode,
                WatchProgress.progress_percent,
            )
            .join(WatchProgress, WatchProgress.anime_id == Anime.id)
            .where(WatchProgress.user_id == user_id)
            .order_by(WatchProgress.last_watched_at.desc())
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        return [
            UserLibraryDTO(
                anime_id=row.id,
                title=row.title,
                last_episode=row.episode,
                progress_percent=row.progress_percent,
            )
            for row in rows
        ]
