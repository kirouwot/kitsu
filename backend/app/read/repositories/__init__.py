"""
READ REPOSITORIES: SELECT-only data access for CQRS-lite read layer
"""

from .anime_feed_read_repo import AnimeFeedReadRepository
from .user_library_read_repo import UserLibraryReadRepository
from .watch_progress_read_repo import WatchProgressReadRepository

__all__ = [
    "AnimeFeedReadRepository",
    "UserLibraryReadRepository",
    "WatchProgressReadRepository",
]
