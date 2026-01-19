import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

import pytest

from app.background.runner import JobRunner
from app.errors import ConflictError, NotFoundError
from app.schemas.favorite import FavoriteRead
from app.use_cases.favorites.add_favorite import add_favorite
from app.use_cases.favorites.get_favorites import get_favorites
from app.use_cases.favorites.remove_favorite import remove_favorite


@dataclass
class FakeFavorite:
    id: uuid.UUID
    user_id: uuid.UUID
    anime_id: uuid.UUID
    created_at: datetime


class FakeFavoriteRepository:
    def __init__(self, store: list[FakeFavorite], *, anime_exists: bool = True) -> None:
        self._store = store
        self._anime_exists = anime_exists
        self.committed = False
        self.rolled_back = False

    async def anime_exists(self, anime_id: uuid.UUID) -> bool:
        return self._anime_exists

    async def get(self, user_id: uuid.UUID, anime_id: uuid.UUID) -> FakeFavorite | None:
        return next(
            (
                favorite
                for favorite in self._store
                if favorite.user_id == user_id and favorite.anime_id == anime_id
            ),
            None,
        )

    async def list(
        self, user_id: uuid.UUID, limit: int, offset: int
    ) -> list[FakeFavorite]:
        favorites = [favorite for favorite in self._store if favorite.user_id == user_id]
        favorites.sort(key=lambda fav: fav.created_at, reverse=True)
        return favorites[offset : offset + limit]

    async def add(
        self,
        user_id: uuid.UUID,
        anime_id: uuid.UUID,
        *,
        favorite_id: uuid.UUID | None = None,
        created_at: datetime | None = None,
    ) -> FakeFavorite:
        favorite = FakeFavorite(
            id=favorite_id or uuid.uuid4(),
            user_id=user_id,
            anime_id=anime_id,
            created_at=created_at or datetime.now(timezone.utc),
        )
        self._store.append(favorite)
        return favorite

    async def remove(self, user_id: uuid.UUID, anime_id: uuid.UUID) -> bool:
        favorite = await self.get(user_id, anime_id)
        if favorite is None:
            return False
        self._store.remove(favorite)
        return True

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


def build_repo_factory(repo: FakeFavoriteRepository):
    @asynccontextmanager
    async def factory():
        yield repo

    return factory


@pytest.mark.anyio
async def test_add_favorite_enqueues_and_persists(monkeypatch: pytest.MonkeyPatch) -> None:
    store: list[FakeFavorite] = []
    user_id = uuid.uuid4()
    anime_id = uuid.uuid4()
    repo = FakeFavoriteRepository(store)
    background_repo = FakeFavoriteRepository(store)
    runner = JobRunner()

    monkeypatch.setattr("app.use_cases.favorites.add_favorite.default_job_runner", runner)
    monkeypatch.setattr("app.background.default_job_runner", runner)

    result = await add_favorite(
        repo,
        user_id,
        anime_id,
        favorite_repo_factory=build_repo_factory(background_repo),
    )

    await asyncio.wait_for(runner.drain(), timeout=1)
    await runner.stop()

    assert isinstance(result, FavoriteRead)
    assert background_repo.committed is True
    assert any(favorite.id == result.id for favorite in store)


@pytest.mark.anyio
async def test_add_favorite_missing_anime_raises() -> None:
    repo = FakeFavoriteRepository([], anime_exists=False)

    with pytest.raises(NotFoundError):
        await add_favorite(repo, uuid.uuid4(), uuid.uuid4())


@pytest.mark.anyio
async def test_add_favorite_duplicate_raises() -> None:
    user_id = uuid.uuid4()
    anime_id = uuid.uuid4()
    store = [
        FakeFavorite(
            id=uuid.uuid4(),
            user_id=user_id,
            anime_id=anime_id,
            created_at=datetime.now(timezone.utc),
        )
    ]
    repo = FakeFavoriteRepository(store)

    with pytest.raises(ConflictError):
        await add_favorite(repo, user_id, anime_id)


@pytest.mark.anyio
async def test_remove_favorite_enqueues_and_persists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid.uuid4()
    anime_id = uuid.uuid4()
    favorite = FakeFavorite(
        id=uuid.uuid4(),
        user_id=user_id,
        anime_id=anime_id,
        created_at=datetime.now(timezone.utc),
    )
    store = [favorite]
    repo = FakeFavoriteRepository(store)
    background_repo = FakeFavoriteRepository(store)
    runner = JobRunner()

    monkeypatch.setattr("app.use_cases.favorites.remove_favorite.default_job_runner", runner)
    monkeypatch.setattr("app.background.default_job_runner", runner)

    await remove_favorite(
        repo,
        user_id,
        anime_id,
        favorite_repo_factory=build_repo_factory(background_repo),
    )

    await asyncio.wait_for(runner.drain(), timeout=1)
    await runner.stop()

    assert background_repo.committed is True
    assert store == []


@pytest.mark.anyio
async def test_get_favorites_returns_sorted() -> None:
    user_id = uuid.uuid4()
    older = FakeFavorite(
        id=uuid.uuid4(),
        user_id=user_id,
        anime_id=uuid.uuid4(),
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    newer = FakeFavorite(
        id=uuid.uuid4(),
        user_id=user_id,
        anime_id=uuid.uuid4(),
        created_at=datetime(2024, 5, 1, tzinfo=timezone.utc),
    )
    repo = FakeFavoriteRepository([older, newer])

    favorites = await get_favorites(repo, user_id=user_id, limit=10, offset=0)

    assert favorites == [newer, older]
