import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.models.base import Base
from app.parser.repositories.anime_external_binding_repo import (
    AnimeExternalBindingRepository,
)
from app.parser.tables import anime_external, anime_external_binding, parser_sources
from tests.parser_helpers import AsyncSessionAdapter


@pytest.fixture()
def db_session():
    engine = sa.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=sa.pool.StaticPool,
    )
    Base.metadata.create_all(
        engine, tables=[parser_sources, anime_external, anime_external_binding]
    )
    session = Session(engine)
    adapter = AsyncSessionAdapter(session, engine)
    yield adapter, session
    session.close()


@pytest.mark.anyio
async def test_binding_repo_is_idempotent(db_session) -> None:
    adapter, session = db_session
    session.execute(
        sa.insert(parser_sources).values(
            id=1,
            code="shikimori",
            enabled=True,
            rate_limit_per_min=60,
            max_concurrency=2,
        )
    )
    session.execute(
        sa.insert(anime_external).values(
            id=1,
            source_id=1,
            external_id="ext-1",
            title_raw="Test",
        )
    )
    session.commit()

    repo = AnimeExternalBindingRepository(adapter)
    anime_id = str(uuid.uuid4())
    binding = await repo.ensure_binding(1, anime_id, bound_by="admin")
    assert binding["anime_external_id"] == 1
    assert binding["anime_id"] == anime_id

    same = await repo.ensure_binding(1, anime_id, bound_by="admin")
    assert same["id"] == binding["id"]

    by_anime = await repo.get_by_anime_id(anime_id)
    assert by_anime["anime_external_id"] == 1

    count = session.execute(
        sa.select(sa.func.count()).select_from(anime_external_binding)
    ).scalar_one()
    assert count == 1
