"""Declarative mapping of protected endpoints to required permissions.

Each key is a (METHOD, PATH) tuple, and the value is a tuple of permissions
that satisfy the endpoint's RBAC enforcement.

SECURITY: All permissions must be explicit (no wildcards like "admin:*").
Per SECURITY-01 contract, only allowed permissions from rbac_contract.py are valid.

NOTE: This matrix is now DEPRECATED for admin endpoints.
Admin endpoints use PermissionService directly via dependency injection.
This matrix is kept only for non-admin endpoints that still use middleware.
"""
from ..auth.rbac_contract import ALLOWED_PERMISSIONS

Permission = str

# SECURITY: Wildcard permissions removed per SECURITY-01
# Old entries with "admin:*" replaced with explicit permissions
# Admin endpoints now use PermissionService directly, not this matrix
ENFORCEMENT_MATRIX: dict[tuple[str, str], tuple[Permission, ...]] = {
    # Parser admin endpoints removed - they now use PermissionService directly
    # These entries are kept only for legacy non-admin routes
}
