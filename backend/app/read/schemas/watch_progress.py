"""
READ SCHEMA: Watch Progress DTO
CQRS-lite: Read-only projection for watch progress
"""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class WatchProgressDTO:
    """
    Immutable DTO for watch progress display.
    Contains only current watch state, no domain logic.
    """

    anime_id: uuid.UUID
    episode: int
    position_seconds: int | None
    progress_percent: float | None
