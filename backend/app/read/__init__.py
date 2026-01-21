"""
READ LAYER: CQRS-lite implementation for Kitsu

This module provides a separate read path for fast, safe, and scalable read operations.

ARCHITECTURE:
- READ ≠ WRITE
- READ: Fast, safe, no domain logic, SELECT-only
- WRITE: Single source of truth, domain logic, state changes

CONSTRAINTS:
- NO writes (add/update/delete/commit/flush)
- NO domain logic
- NO use_case imports
- NO invariant validation
- ONLY SELECT queries
- Returns ONLY DTOs (projections)

USAGE:
- API routers READ through read-layer repositories
- use_cases DO NOT import read layer
- background jobs DO NOT import read layer
"""

from .repositories import (
    AnimeFeedReadRepository,
    UserLibraryReadRepository,
    WatchProgressReadRepository,
)
from .schemas import AnimeFeedDTO, UserLibraryDTO, WatchProgressDTO

__all__ = [
    # Repositories
    "AnimeFeedReadRepository",
    "UserLibraryReadRepository",
    "WatchProgressReadRepository",
    # DTOs
    "AnimeFeedDTO",
    "UserLibraryDTO",
    "WatchProgressDTO",
]
