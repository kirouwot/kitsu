"""
Admin module for centralized RBAC and admin endpoint protection.

This module provides:
- Centralized RBAC permissions
- Permission-based dependencies
- Async audit logging
- Admin routers with permission enforcement
"""
from .router import router

__all__ = ["router"]
