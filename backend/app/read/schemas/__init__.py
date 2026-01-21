"""
READ SCHEMAS: Immutable DTOs for CQRS-lite read layer
"""

from .anime_feed import AnimeFeedDTO
from .user_library import UserLibraryDTO
from .watch_progress import WatchProgressDTO

__all__ = [
    "AnimeFeedDTO",
    "UserLibraryDTO",
    "WatchProgressDTO",
]
