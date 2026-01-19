import uuid
from datetime import datetime, timezone
from typing import Any, TypeVar, cast

import pytest

from app.crud import favorite as favorite_crud
from app.crud.favorite import FavoriteRepository
from app.models.anime import Anime

T = TypeVar("T")


class DummySession:
    def __init__(self, get_result: T | None = None) -> None:
        self.get_result = get_result
        self.get_args = None
        self.committed = False
        self.rolled_back = False

    async def get(self, model: type[T], key: Any) -> T | None:
        self.get_args = (model, key)
        return cast(T | None, self.get_result)

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


@pytest.mark.anyio
async def test_favorite_repository_anime_exists() -> None:
    session = DummySession(get_result=object())
    repo = FavoriteRepository(session)
    anime_id = uuid.uuid4()

    assert await repo.anime_exists(anime_id) is True
    assert session.get_args == (Anime, anime_id)


@pytest.mark.anyio
async def test_favorite_repository_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    session = DummySession()
    get_sentinel = object()
    list_sentinel = [object()]
    add_sentinel = object()

    async def fake_get(
        session_arg: DummySession, user_id: uuid.UUID, anime_id: uuid.UUID
    ) -> object:
        assert session_arg is session
        assert user_id == uuid.UUID(int=1)
        assert anime_id == uuid.UUID(int=2)
        return get_sentinel

    async def fake_list(
        session_arg: DummySession, user_id: uuid.UUID, limit: int, offset: int
    ) -> list[object]:
        assert session_arg is session
        assert user_id == uuid.UUID(int=3)
        assert limit == 5
        assert offset == 10
        return list_sentinel

    async def fake_add(
        session_arg: DummySession,
        user_id: uuid.UUID,
        anime_id: uuid.UUID,
        favorite_id: uuid.UUID | None = None,
        created_at: datetime | None = None,
    ) -> object:
        assert session_arg is session
        assert user_id == uuid.UUID(int=4)
        assert anime_id == uuid.UUID(int=5)
        assert favorite_id == uuid.UUID(int=6)
        assert created_at == datetime(2024, 1, 1, tzinfo=timezone.utc)
        return add_sentinel

    async def fake_remove(
        session_arg: DummySession, user_id: uuid.UUID, anime_id: uuid.UUID
    ) -> bool:
        assert session_arg is session
        assert user_id == uuid.UUID(int=7)
        assert anime_id == uuid.UUID(int=8)
        return True

    monkeypatch.setattr(favorite_crud, "get_favorite", fake_get)
    monkeypatch.setattr(favorite_crud, "list_favorites", fake_list)
    monkeypatch.setattr(favorite_crud, "add_favorite", fake_add)
    monkeypatch.setattr(favorite_crud, "remove_favorite", fake_remove)

    repo = FavoriteRepository(session)

    assert await repo.get(uuid.UUID(int=1), uuid.UUID(int=2)) is get_sentinel
    assert await repo.list(uuid.UUID(int=3), limit=5, offset=10) is list_sentinel
    assert (
        await repo.add(
            uuid.UUID(int=4),
            uuid.UUID(int=5),
            favorite_id=uuid.UUID(int=6),
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        is add_sentinel
    )
    assert await repo.remove(uuid.UUID(int=7), uuid.UUID(int=8)) is True

    await repo.commit()
    await repo.rollback()

    assert session.committed is True
    assert session.rolled_back is True
