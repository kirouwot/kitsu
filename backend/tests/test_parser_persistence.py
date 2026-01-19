from __future__ import annotations

from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base
from app.parser.domain.entities import (
    AnimeExternal,
    EpisodeExternal,
    ScheduleItem,
    TranslationExternal,
)
from app.parser.services.sync_service import ParserSyncService
from app.parser.tables import (
    anime_episodes_external,
    anime_external,
    anime_schedule,
    anime_translations,
    parser_job_logs,
    parser_jobs,
    parser_settings,
    parser_sources,
)


class AsyncSessionAdapter:
    def __init__(self, session: Session, engine: sa.Engine) -> None:
        self._session = session
        self._engine = engine

    def get_bind(self) -> sa.Engine:
        return self._engine

    async def execute(self, *args, **kwargs):
        return self._session.execute(*args, **kwargs)

    async def commit(self) -> None:
        self._session.commit()

    async def rollback(self) -> None:
        self._session.rollback()


class StaticCatalogSource:
    def __init__(self, items: list[AnimeExternal]) -> None:
        self._items = items

    def fetch_catalog(self):
        return list(self._items)


class StaticScheduleSource:
    def __init__(self, items: list[ScheduleItem]) -> None:
        self._items = items

    def fetch_schedule(self):
        return list(self._items)


class StaticEpisodeSource:
    def __init__(self, items: list[EpisodeExternal]) -> None:
        self._items = items

    def fetch_episodes(self):
        return list(self._items)


class ErrorScheduleSource:
    def fetch_schedule(self):
        raise RuntimeError("schedule boom")


@pytest.fixture()
def db_session():
    engine = sa.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=sa.pool.StaticPool,
    )
    parser_tables = [
        parser_sources,
        parser_settings,
        parser_jobs,
        parser_job_logs,
        anime_external,
        anime_schedule,
        anime_episodes_external,
        anime_translations,
    ]
    Base.metadata.create_all(engine, tables=parser_tables)
    main_meta = sa.MetaData()
    anime_table = sa.Table(
        "anime", main_meta, sa.Column("id", sa.Integer(), primary_key=True)
    )
    episodes_table = sa.Table(
        "episodes", main_meta, sa.Column("id", sa.Integer(), primary_key=True)
    )
    main_meta.create_all(engine)
    session = Session(engine)
    adapter = AsyncSessionAdapter(session, engine)
    yield adapter, anime_table, episodes_table
    session.close()


async def _count_rows(session: AsyncSessionAdapter, table: sa.Table) -> int:
    result = await session.execute(select(sa.func.count()).select_from(table))
    return int(result.scalar_one())


@pytest.mark.anyio
async def test_persistence_is_idempotent_and_isolated(db_session) -> None:
    session, anime_table, episodes_table = db_session
    catalog = [AnimeExternal(source_id="1", title="Staging Anime")]
    schedule = [
        ScheduleItem(
            anime_source_id="1",
            episode_number=1,
            airs_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
    ]
    episodes = [
        EpisodeExternal(
            anime_source_id="1",
            number=1,
            stream_url="https://kodik.test/embed/1",
            translations=[TranslationExternal(code="tr1", name="Voice", type="voice")],
            qualities=["720p"],
        )
    ]
    service = ParserSyncService(
        StaticCatalogSource(catalog),
        StaticEpisodeSource(episodes),
        StaticScheduleSource(schedule),
        session=session,
    )

    summary = service.sync_all()

    assert summary["catalog"]["persisted"] == 1
    assert await _count_rows(session, anime_external) == 1
    assert await _count_rows(session, anime_schedule) == 1
    assert await _count_rows(session, anime_episodes_external) == 1
    assert await _count_rows(session, anime_translations) == 1
    assert await _count_rows(session, anime_table) == 0
    assert await _count_rows(session, episodes_table) == 0

    service.sync_all()

    assert await _count_rows(session, anime_external) == 1
    assert await _count_rows(session, anime_schedule) == 1
    assert await _count_rows(session, anime_episodes_external) == 1
    assert await _count_rows(session, anime_translations) == 1


@pytest.mark.anyio
async def test_sync_logs_failures(db_session) -> None:
    session, _anime_table, _episodes_table = db_session
    service = ParserSyncService(
        StaticCatalogSource([]),
        StaticEpisodeSource([]),
        ErrorScheduleSource(),
        session=session,
    )

    summary = service.sync_all()

    assert summary["errors"]
    result = await session.execute(
        select(parser_job_logs.c.level, parser_job_logs.c.message)
    )
    logs = result.all()
    assert any(log.level == "error" and "schedule boom" in log.message for log in logs)
