"""Pydantic schemas for statistics responses."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class AnimeStatistics(BaseModel):
    """Statistics for anime entities."""
    
    total_anime: int = Field(..., description="Total number of anime")
    published_anime: int = Field(..., description="Anime in published state")
    draft_anime: int = Field(..., description="Anime in draft state")
    broken_anime: int = Field(..., description="Anime in broken state")
    pending_anime: int = Field(..., description="Anime in pending state")
    archived_anime: int = Field(..., description="Anime in archived state")
    ongoing_anime: int = Field(..., description="Anime with status=ongoing")
    completed_anime: int = Field(..., description="Anime with status=completed")
    anime_with_errors: int = Field(..., description="Anime flagged with errors")
    anime_without_episodes: int = Field(..., description="Anime with no episodes")


class EpisodeStatistics(BaseModel):
    """Statistics for episode entities."""
    
    total_episodes: int = Field(..., description="Total number of episodes")
    published_episodes: int = Field(..., description="Episodes published (not deleted)")
    draft_episodes: int = Field(..., description="Episodes in draft (not linked to releases)")
    episodes_with_errors: int = Field(..., description="Episodes flagged with errors")
    episodes_missing_video: int = Field(..., description="Episodes without iframe_url")


class ParserStatistics(BaseModel):
    """Statistics for parser jobs."""
    
    total_parser_jobs: int = Field(..., description="Total parser jobs")
    successful_jobs: int = Field(..., description="Jobs with status=success")
    failed_jobs: int = Field(..., description="Jobs with status=failed")
    running_jobs: int = Field(..., description="Jobs with status=running")
    disabled_sources: int = Field(..., description="Parser sources with enabled=false")
    active_sources: int = Field(..., description="Parser sources with enabled=true")
    average_job_duration: float | None = Field(None, description="Average job duration in seconds")
    last_job_time: datetime | None = Field(None, description="Last job start time")


class ErrorStatistics(BaseModel):
    """Statistics for error tracking."""
    
    total_errors: int = Field(..., description="Total error count in audit logs")
    errors_last_24h: int = Field(..., description="Errors in last 24 hours")
    errors_last_7d: int = Field(..., description="Errors in last 7 days")
    critical_errors: int = Field(..., description="Critical/emergency level errors")
    most_frequent_error_types: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Most common error types with counts"
    )


class ActivityStatistics(BaseModel):
    """Statistics for admin activity."""
    
    total_audit_logs: int = Field(..., description="Total audit log entries")
    actions_last_24h: int = Field(..., description="Actions in last 24 hours")
    most_active_admins: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Most active administrators"
    )
    most_common_actions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Most common admin actions"
    )


class OverviewStatistics(BaseModel):
    """Overall system statistics overview."""
    
    anime: AnimeStatistics
    episodes: EpisodeStatistics
    parser: ParserStatistics
    errors: ErrorStatistics
    activity: ActivityStatistics
    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings about partial data or errors"
    )
