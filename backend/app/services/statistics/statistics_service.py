"""
Statistics Service - READ-ONLY system metrics using SQL aggregates.

ARCHITECTURE PRINCIPLES:
- SQL aggregates only (COUNT, GROUP BY, LIMIT)
- No data loaded into Python memory
- No side effects or mutations
- Errors return partial data + warnings
- Single source of truth: existing database
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import func, select, text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from ...models.anime import Anime
from ...models.episode import Episode
from ...models.release import Release
from ...models.audit_log import AuditLog
from ...parser.tables import parser_jobs, parser_sources
from .schemas import (
    AnimeStatistics,
    EpisodeStatistics,
    ParserStatistics,
    ErrorStatistics,
    ActivityStatistics,
    OverviewStatistics,
)


class StatisticsService:
    """
    Service for computing READ-ONLY statistics from the database.
    
    SECURITY: This service only reads data. It never modifies anything.
    All queries use SQL aggregates to avoid loading data into memory.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_anime_statistics(self) -> tuple[AnimeStatistics | None, list[str]]:
        """
        Get anime statistics using SQL aggregates.
        
        Returns:
            tuple: (AnimeStatistics or None, list of warnings)
        """
        warnings = []
        
        try:
            # Total anime (not soft-deleted)
            total_result = await self.session.execute(
                select(func.count(Anime.id)).where(Anime.is_deleted == False)
            )
            total_anime = total_result.scalar() or 0
            
            # Count by state
            state_result = await self.session.execute(
                select(
                    Anime.state,
                    func.count(Anime.id)
                )
                .where(Anime.is_deleted == False)
                .group_by(Anime.state)
            )
            state_counts = {state: count for state, count in state_result.fetchall()}
            
            # Count by status (ongoing/completed)
            status_result = await self.session.execute(
                select(
                    Anime.status,
                    func.count(Anime.id)
                )
                .where(and_(
                    Anime.is_deleted == False,
                    Anime.status.isnot(None)
                ))
                .group_by(Anime.status)
            )
            status_counts = {status: count for status, count in status_result.fetchall()}
            
            # Anime without episodes (no releases)
            anime_without_episodes_result = await self.session.execute(
                select(func.count(Anime.id))
                .select_from(Anime)
                .outerjoin(Release, Release.anime_id == Anime.id)
                .where(and_(
                    Anime.is_deleted == False,
                    Release.id.is_(None)
                ))
            )
            anime_without_episodes = anime_without_episodes_result.scalar() or 0
            
            # Anime with errors (locked with error reason or state=broken)
            anime_with_errors_result = await self.session.execute(
                select(func.count(Anime.id))
                .where(and_(
                    Anime.is_deleted == False,
                    or_(
                        Anime.state == "broken",
                        and_(
                            Anime.is_locked == True,
                            Anime.locked_reason.isnot(None)
                        )
                    )
                ))
            )
            anime_with_errors = anime_with_errors_result.scalar() or 0
            
            return AnimeStatistics(
                total_anime=total_anime,
                published_anime=state_counts.get("published", 0),
                draft_anime=state_counts.get("draft", 0),
                broken_anime=state_counts.get("broken", 0),
                pending_anime=state_counts.get("pending", 0),
                archived_anime=state_counts.get("archived", 0),
                ongoing_anime=status_counts.get("ongoing", 0),
                completed_anime=status_counts.get("completed", 0),
                anime_with_errors=anime_with_errors,
                anime_without_episodes=anime_without_episodes,
            ), warnings
            
        except Exception as e:
            warnings.append(f"Failed to compute anime statistics: {str(e)}")
            return None, warnings
    
    async def get_episode_statistics(self) -> tuple[EpisodeStatistics | None, list[str]]:
        """
        Get episode statistics using SQL aggregates.
        
        Returns:
            tuple: (EpisodeStatistics or None, list of warnings)
        """
        warnings = []
        
        try:
            # Total episodes (not soft-deleted)
            total_result = await self.session.execute(
                select(func.count(Episode.id)).where(Episode.is_deleted == False)
            )
            total_episodes = total_result.scalar() or 0
            
            # Published episodes (not deleted)
            published_result = await self.session.execute(
                select(func.count(Episode.id))
                .where(Episode.is_deleted == False)
            )
            published_episodes = published_result.scalar() or 0
            
            # Episodes missing video (no iframe_url)
            missing_video_result = await self.session.execute(
                select(func.count(Episode.id))
                .where(and_(
                    Episode.is_deleted == False,
                    or_(
                        Episode.iframe_url.is_(None),
                        Episode.iframe_url == ""
                    )
                ))
            )
            episodes_missing_video = missing_video_result.scalar() or 0
            
            # Episodes with errors (locked with reason)
            episodes_with_errors_result = await self.session.execute(
                select(func.count(Episode.id))
                .where(and_(
                    Episode.is_deleted == False,
                    Episode.is_locked == True,
                    Episode.locked_reason.isnot(None)
                ))
            )
            episodes_with_errors = episodes_with_errors_result.scalar() or 0
            
            # Draft episodes (for simplicity, count episodes without release or with manual source)
            draft_result = await self.session.execute(
                select(func.count(Episode.id))
                .where(and_(
                    Episode.is_deleted == False,
                    Episode.source == "manual"
                ))
            )
            draft_episodes = draft_result.scalar() or 0
            
            return EpisodeStatistics(
                total_episodes=total_episodes,
                published_episodes=published_episodes,
                draft_episodes=draft_episodes,
                episodes_with_errors=episodes_with_errors,
                episodes_missing_video=episodes_missing_video,
            ), warnings
            
        except Exception as e:
            warnings.append(f"Failed to compute episode statistics: {str(e)}")
            return None, warnings
    
    async def get_parser_statistics(self) -> tuple[ParserStatistics | None, list[str]]:
        """
        Get parser job statistics using SQL aggregates.
        
        Returns:
            tuple: (ParserStatistics or None, list of warnings)
        """
        warnings = []
        
        try:
            # Total parser jobs
            total_jobs_result = await self.session.execute(
                select(func.count()).select_from(parser_jobs)
            )
            total_parser_jobs = total_jobs_result.scalar() or 0
            
            # Count by status
            status_result = await self.session.execute(
                select(
                    parser_jobs.c.status,
                    func.count()
                )
                .group_by(parser_jobs.c.status)
            )
            status_counts = {status: count for status, count in status_result.fetchall()}
            
            # Source counts
            disabled_sources_result = await self.session.execute(
                select(func.count())
                .select_from(parser_sources)
                .where(parser_sources.c.enabled == False)
            )
            disabled_sources = disabled_sources_result.scalar() or 0
            
            active_sources_result = await self.session.execute(
                select(func.count())
                .select_from(parser_sources)
                .where(parser_sources.c.enabled == True)
            )
            active_sources = active_sources_result.scalar() or 0
            
            # Average job duration (for finished jobs)
            avg_duration_result = await self.session.execute(
                select(
                    func.avg(
                        func.extract('epoch', parser_jobs.c.finished_at - parser_jobs.c.started_at)
                    )
                )
                .where(parser_jobs.c.finished_at.isnot(None))
            )
            average_job_duration = avg_duration_result.scalar()
            
            # Last job time
            last_job_result = await self.session.execute(
                select(func.max(parser_jobs.c.started_at))
            )
            last_job_time = last_job_result.scalar()
            
            return ParserStatistics(
                total_parser_jobs=total_parser_jobs,
                successful_jobs=status_counts.get("success", 0) + status_counts.get("completed", 0),
                failed_jobs=status_counts.get("failed", 0) + status_counts.get("error", 0),
                running_jobs=status_counts.get("running", 0) + status_counts.get("in_progress", 0),
                disabled_sources=disabled_sources,
                active_sources=active_sources,
                average_job_duration=average_job_duration,
                last_job_time=last_job_time,
            ), warnings
            
        except Exception as e:
            warnings.append(f"Failed to compute parser statistics: {str(e)}")
            return None, warnings
    
    async def get_error_statistics(self) -> tuple[ErrorStatistics | None, list[str]]:
        """
        Get error statistics from audit logs using SQL aggregates.
        
        Returns:
            tuple: (ErrorStatistics or None, list of warnings)
        """
        warnings = []
        
        try:
            now = datetime.now(timezone.utc)
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            # Count error actions (actions containing 'error', 'failed', 'denied')
            error_patterns = ["error", "failed", "denied", "permission_denied"]
            
            # Total errors
            total_errors_result = await self.session.execute(
                select(func.count(AuditLog.id))
                .where(
                    or_(*[AuditLog.action.ilike(f"%{pattern}%") for pattern in error_patterns])
                )
            )
            total_errors = total_errors_result.scalar() or 0
            
            # Errors in last 24h
            errors_24h_result = await self.session.execute(
                select(func.count(AuditLog.id))
                .where(and_(
                    AuditLog.created_at >= last_24h,
                    or_(*[AuditLog.action.ilike(f"%{pattern}%") for pattern in error_patterns])
                ))
            )
            errors_last_24h = errors_24h_result.scalar() or 0
            
            # Errors in last 7d
            errors_7d_result = await self.session.execute(
                select(func.count(AuditLog.id))
                .where(and_(
                    AuditLog.created_at >= last_7d,
                    or_(*[AuditLog.action.ilike(f"%{pattern}%") for pattern in error_patterns])
                ))
            )
            errors_last_7d = errors_7d_result.scalar() or 0
            
            # Critical errors (assuming actions with 'critical' or 'emergency')
            critical_result = await self.session.execute(
                select(func.count(AuditLog.id))
                .where(
                    or_(
                        AuditLog.action.ilike("%critical%"),
                        AuditLog.action.ilike("%emergency%")
                    )
                )
            )
            critical_errors = critical_result.scalar() or 0
            
            # Most frequent error types
            error_types_result = await self.session.execute(
                select(
                    AuditLog.action,
                    func.count(AuditLog.id).label("count")
                )
                .where(
                    or_(*[AuditLog.action.ilike(f"%{pattern}%") for pattern in error_patterns])
                )
                .group_by(AuditLog.action)
                .order_by(func.count(AuditLog.id).desc())
                .limit(10)
            )
            most_frequent_error_types = [
                {"action": action, "count": count}
                for action, count in error_types_result.fetchall()
            ]
            
            return ErrorStatistics(
                total_errors=total_errors,
                errors_last_24h=errors_last_24h,
                errors_last_7d=errors_last_7d,
                critical_errors=critical_errors,
                most_frequent_error_types=most_frequent_error_types,
            ), warnings
            
        except Exception as e:
            warnings.append(f"Failed to compute error statistics: {str(e)}")
            return None, warnings
    
    async def get_activity_statistics(self) -> tuple[ActivityStatistics | None, list[str]]:
        """
        Get admin activity statistics from audit logs using SQL aggregates.
        
        Returns:
            tuple: (ActivityStatistics or None, list of warnings)
        """
        warnings = []
        
        try:
            now = datetime.now(timezone.utc)
            last_24h = now - timedelta(hours=24)
            
            # Total audit logs
            total_logs_result = await self.session.execute(
                select(func.count(AuditLog.id))
            )
            total_audit_logs = total_logs_result.scalar() or 0
            
            # Actions in last 24h
            actions_24h_result = await self.session.execute(
                select(func.count(AuditLog.id))
                .where(AuditLog.created_at >= last_24h)
            )
            actions_last_24h = actions_24h_result.scalar() or 0
            
            # Most active admins (by actor_id, where actor_type='user')
            most_active_result = await self.session.execute(
                select(
                    AuditLog.actor_id,
                    func.count(AuditLog.id).label("count")
                )
                .where(and_(
                    AuditLog.actor_type == "user",
                    AuditLog.actor_id.isnot(None)
                ))
                .group_by(AuditLog.actor_id)
                .order_by(func.count(AuditLog.id).desc())
                .limit(10)
            )
            most_active_admins = [
                {"actor_id": str(actor_id), "action_count": count}
                for actor_id, count in most_active_result.fetchall()
            ]
            
            # Most common actions
            common_actions_result = await self.session.execute(
                select(
                    AuditLog.action,
                    func.count(AuditLog.id).label("count")
                )
                .group_by(AuditLog.action)
                .order_by(func.count(AuditLog.id).desc())
                .limit(10)
            )
            most_common_actions = [
                {"action": action, "count": count}
                for action, count in common_actions_result.fetchall()
            ]
            
            return ActivityStatistics(
                total_audit_logs=total_audit_logs,
                actions_last_24h=actions_last_24h,
                most_active_admins=most_active_admins,
                most_common_actions=most_common_actions,
            ), warnings
            
        except Exception as e:
            warnings.append(f"Failed to compute activity statistics: {str(e)}")
            return None, warnings
    
    async def get_overview(self) -> OverviewStatistics:
        """
        Get comprehensive overview of all statistics.
        
        GUARANTEE: This method always returns a response, even if some stats fail.
        Failed stats are replaced with defaults and warnings are included.
        
        Returns:
            OverviewStatistics with all available data and any warnings
        """
        all_warnings = []
        
        # Get all statistics (each returns tuple of (result, warnings))
        anime_stats, anime_warnings = await self.get_anime_statistics()
        all_warnings.extend(anime_warnings)
        
        episode_stats, episode_warnings = await self.get_episode_statistics()
        all_warnings.extend(episode_warnings)
        
        parser_stats, parser_warnings = await self.get_parser_statistics()
        all_warnings.extend(parser_warnings)
        
        error_stats, error_warnings = await self.get_error_statistics()
        all_warnings.extend(error_warnings)
        
        activity_stats, activity_warnings = await self.get_activity_statistics()
        all_warnings.extend(activity_warnings)
        
        # Use defaults if any failed
        if anime_stats is None:
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
        
        if episode_stats is None:
            episode_stats = EpisodeStatistics(
                total_episodes=0,
                published_episodes=0,
                draft_episodes=0,
                episodes_with_errors=0,
                episodes_missing_video=0,
            )
        
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
        
        if error_stats is None:
            error_stats = ErrorStatistics(
                total_errors=0,
                errors_last_24h=0,
                errors_last_7d=0,
                critical_errors=0,
                most_frequent_error_types=[],
            )
        
        if activity_stats is None:
            activity_stats = ActivityStatistics(
                total_audit_logs=0,
                actions_last_24h=0,
                most_active_admins=[],
                most_common_actions=[],
            )
        
        return OverviewStatistics(
            anime=anime_stats,
            episodes=episode_stats,
            parser=parser_stats,
            errors=error_stats,
            activity=activity_stats,
            warnings=all_warnings,
        )
