"""
RBAC Core - Centralized Permission and Role Definitions.

This module defines the RBAC model for admin operations:
- Role definitions (SUPERADMIN, ADMIN, MODERATOR)
- Permission definitions (READ, WRITE, EXECUTE)
- Role-to-Permission mappings

SECURITY:
- Uses existing rbac_contract for validation
- No wildcard permissions
- Explicit permission enumeration only
"""
from __future__ import annotations

from enum import Enum
from typing import Final

from ..auth import rbac_contract


class AdminPermission(str, Enum):
    """
    Admin-specific permissions for parser and system administration.
    
    These map to permissions defined in rbac_contract.ADMIN_PERMISSIONS.
    """
    # Parser administration
    PARSER_SETTINGS = "admin.parser.settings"
    PARSER_EMERGENCY = "admin.parser.emergency"
    PARSER_LOGS = "admin.parser.logs"
    
    # Role and user management
    ROLES_MANAGE = "admin.roles.manage"
    USERS_MANAGE = "admin.users.manage"
    USERS_VIEW = "admin.users.view"


class AdminRole(str, Enum):
    """
    Admin role definitions.
    
    These map to user roles defined in rbac_contract.USER_ROLES.
    """
    SUPERADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"


# Role-to-Permission mappings for admin operations
# This defines what each admin role can do
ADMIN_ROLE_PERMISSIONS: Final[dict[str, frozenset[str]]] = {
    AdminRole.SUPERADMIN: frozenset({
        # Full admin access
        AdminPermission.PARSER_SETTINGS,
        AdminPermission.PARSER_EMERGENCY,
        AdminPermission.PARSER_LOGS,
        AdminPermission.ROLES_MANAGE,
        AdminPermission.USERS_MANAGE,
        AdminPermission.USERS_VIEW,
    }),
    
    AdminRole.ADMIN: frozenset({
        # Admin access without emergency and role management
        AdminPermission.PARSER_SETTINGS,
        AdminPermission.PARSER_LOGS,
        AdminPermission.USERS_VIEW,
    }),
    
    AdminRole.MODERATOR: frozenset({
        # Read-only access
        AdminPermission.PARSER_LOGS,
        AdminPermission.USERS_VIEW,
    }),
}


def get_admin_permissions(role: str) -> frozenset[str]:
    """
    Get admin permissions for a given role.
    
    Args:
        role: The role name (e.g., 'super_admin', 'admin', 'moderator')
        
    Returns:
        frozenset[str]: Set of permission names for the role
    """
    # Validate role against contract
    if role not in rbac_contract.USER_ROLES:
        return frozenset()
    
    return ADMIN_ROLE_PERMISSIONS.get(role, frozenset())


def validate_admin_permission(permission: str) -> bool:
    """
    Validate that a permission is a valid admin permission.
    
    Args:
        permission: The permission to validate
        
    Returns:
        bool: True if valid admin permission
    """
    try:
        rbac_contract.validate_permission(permission)
        return permission in rbac_contract.ADMIN_PERMISSIONS
    except ValueError:
        return False
