"""Declarative mapping of protected endpoints to required permissions.

Each key is a (METHOD, PATH) tuple, and the value is a tuple of permissions
that satisfy the endpoint's RBAC enforcement.
"""
from .helpers import require_permission
from .rbac import Permission

ENFORCEMENT_MATRIX: dict[tuple[str, str], tuple[Permission, ...]] = {
    ("POST", "/favorites"): ("write:content",),
    ("DELETE", "/favorites/{anime_id}"): ("write:content",),
    ("POST", "/watch/progress"): ("write:content",),
    ("POST", "/admin/parser/publish/anime/{external_id}"): ("admin:*",),
    ("POST", "/admin/parser/publish/episode"): ("admin:*",),
    ("GET", "/admin/parser/preview/{external_id}"): ("admin:*",),
}


def permission_for(method: str, path: str) -> Permission:
    permissions = ENFORCEMENT_MATRIX[(method, path)]
    return permissions[0]


def require_enforced_permission(method: str, path: str):
    return require_permission(permission_for(method, path))
