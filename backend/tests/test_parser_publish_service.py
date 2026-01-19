from __future__ import annotations

from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.models.anime import Anime
from app.models.base import Base
from app.models.episode import Episode
from app.models.release import Release
from app.parser.services.publish_service import ParserPublishService
from app.parser.tables import (
    anime_episodes_external,
    anime_external,
    anime_external_binding,
    anime_translations,
    parser_settings,
    parser_sources,
)
from tests.parser_helpers import AsyncSessionAdapter


@pytest.fixture()
def db_session():
    engine = sa.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=sa.pool.StaticPool,
    )
    tables = [
        parser_sources,
        parser_settings,
        anime_external,
        anime_episodes_external,
        anime_translations,
        anime_external_binding,
        Anime.__table__,
        Release.__table__,
        Episode.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)
    session = Session(engine)
    adapter = AsyncSessionAdapter(session, engine)
    yield adapter, session
    session.close()


@pytest.mark.anyio
async def test_publish_service_copies_and_is_idempotent(db_session) -> None:
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
        sa.insert(parser_settings).values(
            mode="manual",
            stage_only=True,
            publish_enabled=False,
            dry_run=False,
            allowed_translation_types=["voice"],
            allowed_translations=["AniLibria"],
            allowed_qualities=["1080p"],
            preferred_translation_priority=["AniLibria"],
            preferred_quality_priority=["1080p"],
            blacklist_titles=[],
            blacklist_external_ids=[],
            updated_at=datetime.now(timezone.utc),
        )
    )
    session.execute(
        sa.insert(anime_external).values(
            id=1,
            source_id=1,
            external_id="ext-1",
            title_raw="Raw",
            title_ru="Тест",
            title_en="Test",
            title_original="テスト",
            description="Описание",
            poster_url="https://example.com/poster.jpg?token=1",
            year=2024,
            season="spring",
            status="ongoing",
            genres=["Action", "Drama"],
        )
    )
    session.execute(
        sa.insert(anime_episodes_external).values(
            id=1,
            anime_id=1,
            source_id=1,
            episode_number=1,
            iframe_url="https://kodik.test/embed/1",
            available_qualities=["720p", "1080p"],
            available_translations=["AniLibria", "Subs"],
        )
    )
    session.execute(
        sa.insert(anime_translations).values(
            anime_id=1,
            source_id=1,
            translation_code="AniLibria",
            translation_name="AniLibria",
            type="voice",
            enabled=True,
            priority=0,
        )
    )
    session.execute(
        sa.insert(anime_translations).values(
            anime_id=1,
            source_id=1,
            translation_code="Subs",
            translation_name="Subs",
            type="sub",
            enabled=True,
            priority=0,
        )
    )
    session.commit()

    service = ParserPublishService(adapter)
    publish_result = await service.publish_anime(1)
    await service.publish_episode(publish_result["anime_id"], 1)

    anime_row = session.execute(sa.select(Anime.__table__)).mappings().one()
    assert anime_row["title"] == "Тест"
    assert anime_row["title_ru"] == "Тест"
    assert anime_row["title_en"] == "Test"
    assert anime_row["title_original"] == "テスト"
    assert anime_row["description"] == "Описание"
    assert anime_row["poster_url"] == "https://example.com/poster.jpg"
    assert anime_row["year"] == 2024
    assert anime_row["season"] == "spring"
    assert anime_row["status"] == "ongoing"
    assert anime_row["genres"] == ["Action", "Drama"]

    episode_row = session.execute(sa.select(Episode.__table__)).mappings().one()
    assert episode_row["iframe_url"] == "https://kodik.test/embed/1"
    assert episode_row["available_translations"] == ["AniLibria"]
    assert episode_row["available_qualities"] == ["1080p"]

    staging_anime = session.execute(sa.select(anime_external)).mappings().one()
    assert staging_anime["poster_url"] == "https://example.com/poster.jpg?token=1"
    staging_episode = session.execute(
        sa.select(anime_episodes_external)
    ).mappings().one()
    assert staging_episode["available_translations"] == ["AniLibria", "Subs"]

    await service.publish_anime(1)
    await service.publish_episode(publish_result["anime_id"], 1)

    anime_count = session.execute(
        sa.select(sa.func.count()).select_from(Anime.__table__)
    ).scalar_one()
    episode_count = session.execute(
        sa.select(sa.func.count()).select_from(Episode.__table__)
    ).scalar_one()
    binding_count = session.execute(
        sa.select(sa.func.count()).select_from(anime_external_binding)
    ).scalar_one()
    assert anime_count == 1
    assert episode_count == 1
    assert binding_count == 1
