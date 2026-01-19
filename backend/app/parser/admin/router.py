from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.helpers import require_permission
from ...dependencies import get_db
from ..config import ParserSettings
from ..services.autoupdate_service import ParserEpisodeAutoupdateService
from ..services.publish_service import ParserPublishService, PublishNotFoundError
from ..services.sync_service import ParserSyncService, get_parser_settings
from ..sources.kodik_episode import KodikEpisodeSource
from ..sources.shikimori_catalog import ShikimoriCatalogSource
from ..sources.shikimori_schedule import ShikimoriScheduleSource
from ..tables import (
    anime_episodes_external,
    anime_external,
    parser_job_logs,
    parser_jobs,
    parser_settings,
    parser_sources,
)
from .schemas import (
    AnimeExternalRead,
    ParserDashboardRead,
    ParserMatchRequest,
    ParserPublishAnimeRead,
    ParserPublishEpisodeRead,
    ParserPublishEpisodeRequest,
    ParserPublishPreviewRead,
    ParserRunRequest,
    ParserSettingsRead,
    ParserSettingsUpdate,
    ParserSourceRead,
    ParserUnmatchRequest,
)

router = APIRouter(
    prefix="/admin/parser",
    tags=["parser-admin"],
    dependencies=[Depends(require_permission("admin:*"))],
)


class _EmptyCatalogSource:
    def fetch_catalog(self):
        return []


class _EmptyScheduleSource:
    def fetch_schedule(self):
        return []


class _EmptyEpisodeSource:
    def fetch_episodes(self):
        return []


def _settings_row(settings: ParserSettings) -> dict[str, Any]:
    return {
        "mode": settings.mode,
        "stage_only": True,
        "publish_enabled": False,
        "enable_autoupdate": settings.enable_autoupdate,
        "update_interval_minutes": settings.update_interval_minutes,
        "dry_run": settings.dry_run_default,
        "allowed_translation_types": list(settings.allowed_translation_types),
        "allowed_translations": list(settings.allowed_translations),
        "allowed_qualities": list(settings.allowed_qualities),
        "preferred_translation_priority": list(settings.preferred_translation_priority),
        "preferred_quality_priority": list(settings.preferred_quality_priority),
        "blacklist_titles": list(settings.blacklist_titles),
        "blacklist_external_ids": list(settings.blacklist_external_ids),
    }


def _settings_response(settings: ParserSettings) -> ParserSettingsRead:
    return ParserSettingsRead(
        mode=settings.mode,
        stage_only=True,
        autopublish_enabled=False,
        enable_autoupdate=settings.enable_autoupdate,
        update_interval_minutes=settings.update_interval_minutes,
        dry_run_default=settings.dry_run_default,
        allowed_translation_types=list(settings.allowed_translation_types),
        allowed_translations=list(settings.allowed_translations),
        allowed_qualities=list(settings.allowed_qualities),
        preferred_translation_priority=list(settings.preferred_translation_priority),
        preferred_quality_priority=list(settings.preferred_quality_priority),
        blacklist_titles=list(settings.blacklist_titles),
        blacklist_external_ids=list(settings.blacklist_external_ids),
    )


async def _get_settings_id(session: AsyncSession) -> int | None:
    result = await session.execute(select(parser_settings.c.id).limit(1))
    return result.scalar_one_or_none()


@router.get("/dashboard", response_model=ParserDashboardRead)
async def get_dashboard(
    session: AsyncSession = Depends(get_db),
) -> ParserDashboardRead:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    sources_result = await session.execute(
        select(parser_sources.c.id, parser_sources.c.code, parser_sources.c.enabled)
    )
    sources = [
        ParserSourceRead.model_validate(
            {"id": row.id, "code": row.code, "enabled": row.enabled}
        )
        for row in sources_result
    ]
    anime_count = await session.scalar(
        select(func.count()).select_from(anime_external)
    )
    unmapped_count = await session.scalar(
        select(func.count())
        .select_from(anime_external)
        .where(anime_external.c.anime_id.is_(None))
    )
    episodes_count = await session.scalar(
        select(func.count()).select_from(anime_episodes_external)
    )
    jobs_count = await session.scalar(
        select(func.count())
        .select_from(parser_jobs)
        .where(parser_jobs.c.started_at >= cutoff)
    )
    errors_count = await session.scalar(
        select(func.count())
        .select_from(parser_job_logs)
        .where(parser_job_logs.c.level == "error")
        .where(parser_job_logs.c.created_at >= cutoff)
    )
    return ParserDashboardRead(
        sources=sources,
        anime_external_count=int(anime_count or 0),
        unmapped_anime_count=int(unmapped_count or 0),
        episodes_external_count=int(episodes_count or 0),
        jobs_last_24h=int(jobs_count or 0),
        errors_count=int(errors_count or 0),
    )


@router.get("/anime_external", response_model=list[AnimeExternalRead])
async def list_anime_external(
    source: str | None = Query(default=None),
    matched: bool | None = Query(default=None),
    year: int | None = Query(default=None),
    status_text: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> list[AnimeExternalRead]:
    stmt = (
        select(
            anime_external.c.id,
            anime_external.c.anime_id,
            parser_sources.c.code.label("source"),
            anime_external.c.external_id,
            anime_external.c.title_raw,
            anime_external.c.year,
            anime_external.c.status,
            anime_external.c.matched_by,
        )
        .select_from(anime_external)
        .join(parser_sources, anime_external.c.source_id == parser_sources.c.id)
    )
    if source:
        stmt = stmt.where(parser_sources.c.code == source)
    if matched is True:
        stmt = stmt.where(anime_external.c.anime_id.is_not(None))
    if matched is False:
        stmt = stmt.where(anime_external.c.anime_id.is_(None))
    if year is not None:
        stmt = stmt.where(anime_external.c.year == year)
    if status_text:
        stmt = stmt.where(anime_external.c.status == status_text)
    if search:
        stmt = stmt.where(
            func.lower(anime_external.c.title_raw).like(f"%{search.lower()}%")
        )
    result = await session.execute(stmt.order_by(anime_external.c.id.desc()))
    return [AnimeExternalRead.model_validate(row) for row in result.mappings()]


@router.post("/match", status_code=status.HTTP_200_OK)
async def match_anime_external(
    payload: ParserMatchRequest,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    async with session.begin():
        result = await session.execute(
            select(anime_external.c.id).where(
                anime_external.c.id == payload.anime_external_id
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Anime external not found"
            )
        await session.execute(
            update(anime_external)
            .where(anime_external.c.id == payload.anime_external_id)
            .values(anime_id=str(payload.anime_id), matched_by="manual")
        )
    return {"status": "matched"}


@router.post("/unmatch", status_code=status.HTTP_200_OK)
async def unmatch_anime_external(
    payload: ParserUnmatchRequest,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    async with session.begin():
        result = await session.execute(
            select(anime_external.c.id).where(
                anime_external.c.id == payload.anime_external_id
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Anime external not found"
            )
        await session.execute(
            update(anime_external)
            .where(anime_external.c.id == payload.anime_external_id)
            .values(anime_id=None, matched_by=None)
        )
    return {"status": "unmatched"}


@router.post("/publish/anime/{external_id}", response_model=ParserPublishAnimeRead)
async def publish_anime_external(
    external_id: int,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("admin:*")),
) -> ParserPublishAnimeRead:
    service = ParserPublishService(session)
    try:
        result = await service.publish_anime(external_id)
    except PublishNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return ParserPublishAnimeRead.model_validate(result)


@router.post("/publish/episode", response_model=ParserPublishEpisodeRead)
async def publish_episode_external(
    payload: ParserPublishEpisodeRequest,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("admin:*")),
) -> ParserPublishEpisodeRead:
    service = ParserPublishService(session)
    try:
        result = await service.publish_episode(payload.anime_id, payload.episode_number)
    except PublishNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return ParserPublishEpisodeRead.model_validate(result)


@router.get("/preview/{external_id}", response_model=ParserPublishPreviewRead)
async def preview_publish_diff(
    external_id: int,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("admin:*")),
) -> ParserPublishPreviewRead:
    service = ParserPublishService(session)
    try:
        result = await service.preview_diff(external_id)
    except PublishNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return ParserPublishPreviewRead.model_validate(result)


@router.post("/run")
async def run_parser_sync(
    payload: ParserRunRequest,
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    settings = await get_parser_settings(session)
    sources = set(payload.sources)
    catalog_source = (
        ShikimoriCatalogSource(settings)
        if "shikimori" in sources
        else _EmptyCatalogSource()
    )
    schedule_source = (
        ShikimoriScheduleSource(settings)
        if "shikimori" in sources
        else _EmptyScheduleSource()
    )
    episode_source = (
        KodikEpisodeSource(settings)
        if "kodik" in sources
        else _EmptyEpisodeSource()
    )
    service = ParserSyncService(
        catalog_source, episode_source, schedule_source, session=session
    )
    persist = payload.mode == "persist"
    return service.sync_all(persist=persist, publish=False)


@router.post("/run/autoupdate")
async def run_parser_autoupdate(
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    service = ParserEpisodeAutoupdateService(session=session)
    return await service.run(force=True)


@router.get("/settings", response_model=ParserSettingsRead)
async def get_settings(
    session: AsyncSession = Depends(get_db),
) -> ParserSettingsRead:
    settings = await get_parser_settings(session)
    return _settings_response(settings)


@router.post("/settings", response_model=ParserSettingsRead)
async def update_settings(
    payload: ParserSettingsUpdate,
    session: AsyncSession = Depends(get_db),
) -> ParserSettingsRead:
    async with session.begin():
        current = await get_parser_settings(session)
        updates = payload.model_dump(exclude_unset=True)
        updates["autopublish_enabled"] = False
        updates["stage_only"] = True
        settings = ParserSettings(**{**current.model_dump(), **updates})
        settings_id = await _get_settings_id(session)
        values = {**_settings_row(settings), "updated_at": datetime.now(timezone.utc)}
        if settings_id is None:
            await session.execute(insert(parser_settings).values(values))
        else:
            await session.execute(
                update(parser_settings)
                .where(parser_settings.c.id == settings_id)
                .values(values)
            )
    return _settings_response(settings)
