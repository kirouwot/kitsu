"""
Admin Dependencies - Permission-based dependency injection for admin endpoints.

This module provides dependency functions for FastAPI endpoints:
- require_permissions(*permissions): Enforce permission checks
- get_admin_user(): Get authenticated admin user

SECURITY:
- All permission checks use PermissionService
- No inline role checks in routers
- Raises 401 if not authenticated
- Raises 403 if insufficient permissions
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, get_current_user
from ..models.user import User
from ..services.admin.permission_service import PermissionService

logger = logging.getLogger("kitsu.admin")


def require_permissions(*permissions: str):
    """
    Dependency factory for enforcing admin permissions.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(
            _: None = Depends(require_permissions("admin.parser.settings"))
        ):
            ...
    
    Args:
        *permissions: One or more permission names required
        
    Returns:
        Async dependency function that raises HTTPException if permissions denied
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if insufficient permissions
    """
    async def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> None:
        """
        Check if current user has all required permissions.
        
        Args:
            current_user: Authenticated user from get_current_user dependency
            session: Database session
            
        Raises:
            HTTPException: 401 if not authenticated, 403 if insufficient permissions
        """
        # User is already authenticated via get_current_user
        # Now check permissions
        permission_service = PermissionService(session)
        
        for permission in permissions:
            # PermissionService.require_permission raises HTTPException(403) if denied
            await permission_service.require_permission(
                user=current_user,
                permission_name=permission,
                actor_type="user"
            )
        
        # All permissions granted - allow access
        logger.debug(
            "Permission check passed: user=%s permissions=%s",
            current_user.id,
            permissions
        )
    
    return dependency


async def get_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get authenticated user with admin verification.
    
    This is a convenience dependency that verifies the user is authenticated
    and has at least one admin permission. Use require_permissions for
    specific permission checks.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        session: Database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not an admin
    """
    # Check if user has any admin permission
    permission_service = PermissionService(session)
    
    # Get user permissions
    user_permissions = await permission_service.get_user_permissions(current_user.id)
    
    # Check if user has any admin.* permission
    has_admin_permission = any(
        perm.startswith("admin.") for perm in user_permissions
    )
    
    if not has_admin_permission:
        logger.warning(
            "Admin access denied: user=%s has no admin permissions",
            current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user
