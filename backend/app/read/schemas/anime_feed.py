"""
READ SCHEMA: Anime Feed DTO
CQRS-lite: Read-only projection for anime feed display
"""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class AnimeFeedDTO:
    """
    Immutable DTO for anime feed display.
    Contains only essential fields for fast read operations.
    """

    anime_id: uuid.UUID
    title: str
    poster_url: str | None
    episodes_count: int
