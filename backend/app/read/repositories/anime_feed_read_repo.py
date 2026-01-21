"""
READ REPOSITORY: Anime Feed
CQRS-lite: SELECT-only operations for anime feed display

CONSTRAINTS:
- NO writes (add/update/delete/commit/flush)
- NO domain logic
- NO use_case imports
- ONLY SELECT queries
- Returns ONLY DTOs
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.anime import Anime
from ...models.episode import Episode
from ...models.release import Release
from ..schemas.anime_feed import AnimeFeedDTO


class AnimeFeedReadRepository:
    """
    Read-only repository for anime feed operations.
    Fast, safe, scalable read path without domain logic.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize with database session.
        Session is used ONLY for SELECT queries.
        """
        self._session = session

    async def get_feed(self, limit: int) -> list[AnimeFeedDTO]:
        """
        Get anime feed with episode counts.
        
        Uses joins: Anime -> Release -> Episode
        Ordered by creation time descending (newest first).
        
        Args:
            limit: Maximum number of anime to return
            
        Returns:
            List of AnimeFeedDTO with anime info and episode counts
        """
        # Join Anime -> Release -> Episode and count episodes per anime
        stmt = (
            select(
                Anime.id,
                Anime.title,
                Anime.poster_url,
                func.count(Episode.id).label("episodes_count"),
            )
            .join(Release, Release.anime_id == Anime.id, isouter=True)
            .join(Episode, Episode.release_id == Release.id, isouter=True)
            .group_by(Anime.id)
            .order_by(Anime.created_at.desc())
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        return [
            AnimeFeedDTO(
                anime_id=row.id,
                title=row.title,
                poster_url=row.poster_url,
                episodes_count=row.episodes_count or 0,
            )
            for row in rows
        ]
