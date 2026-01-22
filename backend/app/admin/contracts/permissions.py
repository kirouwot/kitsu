"""
Admin Permission Contracts - Permission enumeration for admin operations.

Defines all available admin permissions as an enum.
NO logic, NO helper functions - ONLY permission identifiers.
"""
from __future__ import annotations

from enum import Enum


class AdminPermission(str, Enum):
    """
    Admin-specific permissions for system administration.

    Format: "admin.<domain>.<action>"
    """

    # Parser administration
    PARSER_LOGS = "admin.parser.logs"
    PARSER_SETTINGS = "admin.parser.settings"
    PARSER_EMERGENCY = "admin.parser.emergency"

    # User management
    USERS_VIEW = "admin.users.view"
    USERS_MANAGE = "admin.users.manage"

    # Role management
    ROLES_VIEW = "admin.roles.view"
    ROLES_MANAGE = "admin.roles.manage"

    # Audit logs
    AUDIT_VIEW = "admin.audit.view"

    # System monitoring
    SYSTEM_VIEW = "admin.system.view"
    SYSTEM_MANAGE = "admin.system.manage"
