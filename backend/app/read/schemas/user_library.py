"""
READ SCHEMA: User Library DTO
CQRS-lite: Read-only projection for user's anime library
"""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class UserLibraryDTO:
    """
    Immutable DTO for user's anime library.
    Contains anime info + user's watch progress.
    """

    anime_id: uuid.UUID
    title: str
    last_episode: int
    progress_percent: float | None
