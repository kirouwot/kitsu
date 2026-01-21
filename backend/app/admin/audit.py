"""
Async Audit Logger for Admin Actions.

This module provides non-blocking audit logging for admin operations:
- Admin actions (settings changes, parser control)
- Job execution (parser runs, emergency stops)
- Critical changes (role assignments, permission changes)

ARCHITECTURE:
- Async, non-blocking logging
- Structured log output
- No database writes (stdout/structured log for now)
- Does NOT block request flow

FUTURE: Can be extended to write to audit_logs table
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from ..models.user import User

logger = logging.getLogger("kitsu.audit")


class AdminAuditLogger:
    """
    Async audit logger for admin actions.
    
    Logs admin actions to structured logs (stdout) without blocking requests.
    All logging is async and failures don't block the request flow.
    """
    
    def __init__(self):
        """Initialize the audit logger."""
        self._logger = logger
    
    async def log_admin_action(
        self,
        action: str,
        endpoint: str,
        actor: User | None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Log an admin action asynchronously.
        
        Args:
            action: The action performed (e.g., 'parser.settings.update')
            endpoint: The endpoint path (e.g., '/admin/parser/settings')
            actor: The user who performed the action
            details: Additional details about the action
            ip_address: Client IP address
            user_agent: Client user agent
        """
        try:
            await self._log_async(
                level="INFO",
                event_type="admin_action",
                action=action,
                endpoint=endpoint,
                actor_id=str(actor.id) if actor else None,
                actor_email=actor.email if actor else None,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as e:
            # Never let audit logging failure break the request
            self._logger.error("Audit logging failed: %s", e, exc_info=True)
    
    async def log_parser_job(
        self,
        job_type: str,
        actor: User | None,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Log a parser job execution.
        
        Args:
            job_type: Type of parser job (e.g., 'sync', 'autoupdate', 'emergency_stop')
            actor: The user who initiated the job
            status: Job status (e.g., 'started', 'completed', 'failed')
            details: Additional job details
        """
        try:
            await self._log_async(
                level="INFO",
                event_type="parser_job",
                job_type=job_type,
                status=status,
                actor_id=str(actor.id) if actor else None,
                details=details or {},
            )
        except Exception as e:
            self._logger.error("Audit logging failed: %s", e, exc_info=True)
    
    async def log_critical_change(
        self,
        change_type: str,
        entity_type: str,
        entity_id: str | UUID,
        actor: User | None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        reason: str | None = None,
    ) -> None:
        """
        Log a critical change (e.g., role assignment, permission grant).
        
        Args:
            change_type: Type of change (e.g., 'role.assign', 'permission.grant')
            entity_type: Type of entity changed (e.g., 'user', 'role')
            entity_id: ID of the entity
            actor: The user who made the change
            before: State before the change
            after: State after the change
            reason: Reason for the change
        """
        try:
            await self._log_async(
                level="WARNING",  # Critical changes get WARNING level
                event_type="critical_change",
                change_type=change_type,
                entity_type=entity_type,
                entity_id=str(entity_id),
                actor_id=str(actor.id) if actor else None,
                before=before or {},
                after=after or {},
                reason=reason,
            )
        except Exception as e:
            self._logger.error("Audit logging failed: %s", e, exc_info=True)
    
    async def _log_async(
        self,
        level: str,
        event_type: str,
        **kwargs: Any
    ) -> None:
        """
        Internal async logging method.
        
        Args:
            level: Log level (INFO, WARNING, ERROR)
            event_type: Type of event
            **kwargs: Additional fields to log
        """
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._write_log,
            level,
            event_type,
            kwargs
        )
    
    def _write_log(
        self,
        level: str,
        event_type: str,
        data: dict[str, Any]
    ) -> None:
        """
        Write structured log entry.
        
        Args:
            level: Log level
            event_type: Event type
            data: Log data
        """
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **data
        }
        
        # Convert to JSON for structured logging
        log_message = json.dumps(log_entry, default=str)
        
        # Write to logger
        log_level = getattr(logging, level.upper(), logging.INFO)
        self._logger.log(log_level, "AUDIT: %s", log_message)


# Global audit logger instance
audit_logger = AdminAuditLogger()


# Convenience functions for common audit operations
async def log_admin_action(
    action: str,
    endpoint: str,
    actor: User | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Log an admin action. See AdminAuditLogger.log_admin_action for details."""
    await audit_logger.log_admin_action(
        action=action,
        endpoint=endpoint,
        actor=actor,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_parser_job(
    job_type: str,
    actor: User | None = None,
    status: str = "started",
    details: dict[str, Any] | None = None,
) -> None:
    """Log a parser job. See AdminAuditLogger.log_parser_job for details."""
    await audit_logger.log_parser_job(
        job_type=job_type,
        actor=actor,
        status=status,
        details=details,
    )


async def log_critical_change(
    change_type: str,
    entity_type: str,
    entity_id: str | UUID,
    actor: User | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
) -> None:
    """Log a critical change. See AdminAuditLogger.log_critical_change for details."""
    await audit_logger.log_critical_change(
        change_type=change_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        before=before,
        after=after,
        reason=reason,
    )
