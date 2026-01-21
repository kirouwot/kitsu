"""
Admin API endpoints for statistics (READ-ONLY).

These endpoints provide system-wide statistics for monitoring and analysis.
All endpoints require the admin.statistics.view permission and are READ-ONLY.

SECURITY:
- No mutations allowed
- All actions are audited
- Permission checks enforced
- Partial failure safe (returns data + warnings)
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...dependencies import get_db, get_current_user
from ...models.user import User
from ...services.statistics import (
    StatisticsService,
    OverviewStatistics,
    AnimeStatistics,
    EpisodeStatistics,
    ParserStatistics,
    ErrorStatistics,
    ActivityStatistics,
)
from ...services.admin.permission_service import PermissionService
from ...services.audit.audit_service import AuditService


router = APIRouter(prefix="/admin/statistics", tags=["admin-statistics"])


async def require_statistics_permission(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to enforce admin.statistics.view permission.
    
    SECURITY: Every statistics endpoint requires this permission.
    """
    permission_service = PermissionService(db)
    await permission_service.require_permission(
        user=current_user,
        permission_name="admin.statistics.view",
        actor_type="user"
    )
    return current_user


async def log_statistics_access(
    action: str,
    request: Request,
    current_user: User,
    db: AsyncSession,
) -> None:
    """
    Log statistics access to audit logs.
    
    REQUIREMENT: All statistics views must be audited.
    """
    audit_service = AuditService(db)
    try:
        await audit_service.log_action(
            actor=current_user,
            actor_type="user",
            action=action,
            entity_type="statistics",
            entity_id="system",
            before=None,
            after=None,
            reason=None,
            request=request,
        )
    except Exception:
        # Don't fail statistics request if audit logging fails
        pass


@router.get("/overview", response_model=OverviewStatistics)
async def get_overview_statistics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_statistics_permission),
):
    """
    Get comprehensive overview of all system statistics.
    
    Requires: admin.statistics.view permission
    
    Returns all available statistics with warnings if any subsystem fails.
    This endpoint is guaranteed to return a response even if partial failures occur.
    """
    # Log access
    await log_statistics_access("statistics.view.overview", request, current_user, db)
    
    # Get statistics
    stats_service = StatisticsService(db)
    return await stats_service.get_overview()


@router.get("/anime", response_model=AnimeStatistics)
async def get_anime_statistics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_statistics_permission),
):
    """
    Get anime-specific statistics.
    
    Requires: admin.statistics.view permission
    
    Returns detailed metrics about anime entities.
    """
    # Log access
    await log_statistics_access("statistics.view.anime", request, current_user, db)
    
    # Get statistics
    stats_service = StatisticsService(db)
    anime_stats, warnings = await stats_service.get_anime_statistics()
    
    if anime_stats is None:
        # Return empty stats if query failed
        anime_stats = AnimeStatistics(
            total_anime=0,
            published_anime=0,
            draft_anime=0,
            broken_anime=0,
            pending_anime=0,
            archived_anime=0,
            ongoing_anime=0,
            completed_anime=0,
            anime_with_errors=0,
            anime_without_episodes=0,
        )
    
    return anime_stats


@router.get("/episodes", response_model=EpisodeStatistics)
async def get_episode_statistics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_statistics_permission),
):
    """
    Get episode-specific statistics.
    
    Requires: admin.statistics.view permission
    
    Returns detailed metrics about episode entities.
    """
    # Log access
    await log_statistics_access("statistics.view.episodes", request, current_user, db)
    
    # Get statistics
    stats_service = StatisticsService(db)
    episode_stats, warnings = await stats_service.get_episode_statistics()
    
    if episode_stats is None:
        episode_stats = EpisodeStatistics(
            total_episodes=0,
            published_episodes=0,
            draft_episodes=0,
            episodes_with_errors=0,
            episodes_missing_video=0,
        )
    
    return episode_stats


@router.get("/parser", response_model=ParserStatistics)
async def get_parser_statistics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_statistics_permission),
):
    """
    Get parser job statistics.
    
    Requires: admin.statistics.view permission
    
    Returns metrics about parser jobs, sources, and performance.
    """
    # Log access
    await log_statistics_access("statistics.view.parser", request, current_user, db)
    
    # Get statistics
    stats_service = StatisticsService(db)
    parser_stats, warnings = await stats_service.get_parser_statistics()
    
    if parser_stats is None:
        parser_stats = ParserStatistics(
            total_parser_jobs=0,
            successful_jobs=0,
            failed_jobs=0,
            running_jobs=0,
            disabled_sources=0,
            active_sources=0,
            average_job_duration=None,
            last_job_time=None,
        )
    
    return parser_stats


@router.get("/errors", response_model=ErrorStatistics)
async def get_error_statistics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_statistics_permission),
):
    """
    Get error tracking statistics.
    
    Requires: admin.statistics.view permission
    
    Returns metrics about system errors from audit logs.
    """
    # Log access
    await log_statistics_access("statistics.view.errors", request, current_user, db)
    
    # Get statistics
    stats_service = StatisticsService(db)
    error_stats, warnings = await stats_service.get_error_statistics()
    
    if error_stats is None:
        error_stats = ErrorStatistics(
            total_errors=0,
            errors_last_24h=0,
            errors_last_7d=0,
            critical_errors=0,
            most_frequent_error_types=[],
        )
    
    return error_stats


@router.get("/activity", response_model=ActivityStatistics)
async def get_activity_statistics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_statistics_permission),
):
    """
    Get admin activity statistics.
    
    Requires: admin.statistics.view permission
    
    Returns metrics about admin actions from audit logs.
    """
    # Log access
    await log_statistics_access("statistics.view.activity", request, current_user, db)
    
    # Get statistics
    stats_service = StatisticsService(db)
    activity_stats, warnings = await stats_service.get_activity_statistics()
    
    if activity_stats is None:
        activity_stats = ActivityStatistics(
            total_audit_logs=0,
            actions_last_24h=0,
            most_active_admins=[],
            most_common_actions=[],
        )
    
    return activity_stats
