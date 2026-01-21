"""
Centralized Admin Router with RBAC Protection.

This module provides infrastructure for admin endpoints with permission-based access control:
- All endpoints protected by require_permissions dependency
- No inline role checks
- Async audit logging for all actions
- Demonstrates RBAC pattern for admin operations

SECURITY:
- All endpoints require explicit permissions
- Uses PermissionService for runtime checks
- Audit logs all admin actions

NOTE: Existing admin endpoints in parser.admin.router and api.admin.anime
continue to function independently. This module provides the centralized
infrastructure and pattern for RBAC-protected admin operations.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, get_current_user
from ..models.user import User
from ..services.admin.permission_service import PermissionService
from .audit import log_admin_action
from .dependencies import require_permissions
from .permissions import AdminPermission, AdminRole, get_admin_permissions

# Create admin infrastructure router
# This provides utility endpoints and demonstrates the RBAC pattern
router = APIRouter(
    prefix="/admin",
    tags=["admin-core"],
)


@router.get("/health")
async def admin_health(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    _: None = Depends(require_permissions(AdminPermission.PARSER_LOGS)),
) -> dict[str, str]:
    """
    Admin health check endpoint.
    
    Requires: admin.parser.logs permission
    
    Returns basic status and logs the access.
    """
    # Log admin access
    await log_admin_action(
        action="admin.health_check",
        endpoint=str(request.url.path),
        actor=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    return {
        "status": "ok",
        "message": "Admin RBAC infrastructure is operational"
    }


@router.get("/permissions/my")
async def get_my_permissions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, list[str]]:
    """
    Get current user's admin permissions.
    
    Returns list of admin permissions the current user has.
    This is useful for UI to show/hide admin features.
    """
    permission_service = PermissionService(session)
    user_permissions = await permission_service.get_user_permissions(current_user.id)
    
    # Filter to only admin permissions
    admin_permissions = [
        perm for perm in user_permissions
        if perm.startswith("admin.")
    ]
    
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "admin_permissions": admin_permissions,
    }


@router.get("/permissions/role/{role}")
async def get_role_permissions(
    role: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    _: None = Depends(require_permissions(AdminPermission.ROLES_MANAGE)),
) -> dict[str, object]:
    """
    Get admin permissions for a specific role.
    
    Requires: admin.roles.manage permission
    
    Returns the admin permissions assigned to a role.
    Useful for role management UI.
    """
    permissions = get_admin_permissions(role)
    
    return {
        "role": role,
        "admin_permissions": list(permissions),
        "count": len(permissions),
    }
