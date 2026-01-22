"""
Test admin data contracts to ensure they are read-only, have no logic, and use Python 3.12 syntax.
"""
import ast
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest


def _find_contracts_root() -> Path:
    """Find the admin contracts directory."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "app" / "admin" / "contracts"
        if candidate.is_dir():
            return candidate
    raise AssertionError("Unable to locate app/admin/contracts")


CONTRACTS_ROOT = _find_contracts_root()


def _iter_contract_files() -> list[Path]:
    """Get all Python files in contracts directory."""
    return [path for path in CONTRACTS_ROOT.rglob("*.py") if path.is_file()]


def test_contracts_no_logic() -> None:
    """Verify contracts have no validators, computed fields, or methods with logic."""
    violations: list[str] = []
    
    for filepath in _iter_contract_files():
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
        
        for node in ast.walk(tree):
            # Check for validators
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    decorator_name = ""
                    if isinstance(decorator, ast.Name):
                        decorator_name = decorator.id
                    elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                        decorator_name = decorator.func.id
                    
                    if "validator" in decorator_name.lower():
                        violations.append(
                            f"{filepath.name}: Found validator {node.name}"
                        )
                    if "computed" in decorator_name.lower():
                        violations.append(
                            f"{filepath.name}: Found computed field {node.name}"
                        )
            
            # Check for methods in classes (excluding __init__ and Config/ConfigDict)
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        # Allow __init__, model_config, Config class
                        if item.name not in ("__init__", "model_config", "Config"):
                            violations.append(
                                f"{filepath.name}:{node.name}: Found method {item.name}"
                            )
    
    assert not violations, (
        "Contracts contain logic (validators/computed fields/methods):\n"
        + "\n".join(sorted(violations))
    )


def test_contracts_use_union_syntax() -> None:
    """Verify contracts use Python 3.12 union syntax (|) instead of Optional/Union."""
    violations: list[str] = []
    
    for filepath in _iter_contract_files():
        content = filepath.read_text(encoding="utf-8")
        
        # Check for Optional or Union imports from typing
        if "from typing import" in content:
            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                if "from typing import" in line:
                    if "Optional" in line or "Union" in line:
                        violations.append(
                            f"{filepath.name}:{line_num}: Uses Optional/Union instead of | syntax"
                        )
    
    # Note: This is a heuristic check, not exhaustive
    assert not violations, (
        "Contracts use old-style Optional/Union instead of | syntax:\n"
        + "\n".join(sorted(violations))
    )


def test_contracts_import_successfully() -> None:
    """Verify all contracts can be imported without errors."""
    from app.admin.contracts import (
        AdminAuditActor,
        AdminAuditLogRead,
        AdminAuditTarget,
        AdminPermission,
        AdminRoleAssignment,
        AdminRoleList,
        AdminRoleRead,
        AdminUserList,
        AdminUserRead,
        AdminUserShort,
        ParserJobStatusRead,
        ParserJobSummary,
        ParserStatusRead,
        SystemComponentStatus,
        SystemHealthRead,
    )
    
    # Just verify they exist
    assert AdminUserRead is not None
    assert AdminUserShort is not None
    assert AdminUserList is not None
    assert AdminRoleRead is not None
    assert AdminRoleList is not None
    assert AdminRoleAssignment is not None
    assert AdminPermission is not None
    assert AdminAuditLogRead is not None
    assert AdminAuditActor is not None
    assert AdminAuditTarget is not None
    assert ParserStatusRead is not None
    assert ParserJobStatusRead is not None
    assert ParserJobSummary is not None
    assert SystemHealthRead is not None
    assert SystemComponentStatus is not None


def test_contracts_can_be_instantiated() -> None:
    """Verify contract models can be instantiated with valid data."""
    from app.admin.contracts import (
        AdminAuditActor,
        AdminAuditLogRead,
        AdminAuditTarget,
        AdminPermission,
        AdminRoleAssignment,
        AdminRoleRead,
        AdminUserRead,
        AdminUserShort,
        ParserJobStatusRead,
        ParserStatusRead,
        SystemComponentStatus,
        SystemHealthRead,
    )
    
    # Test user models
    user_short = AdminUserShort(
        id=uuid4(),
        email="test@example.com",
        is_active=True
    )
    assert user_short.email == "test@example.com"
    
    # Test role models
    role_read = AdminRoleRead(
        id=uuid4(),
        name="admin",
        display_name="Administrator",
        permissions=["admin.users.view"],
        is_system=True,
        is_active=True,
        created_at=datetime.now(UTC)
    )
    assert role_read.name == "admin"
    
    # Test permission enum
    perm = AdminPermission.PARSER_LOGS
    assert perm.value == "admin.parser.logs"
    
    # Test audit models
    actor = AdminAuditActor(
        actor_id=uuid4(),
        actor_type="user",
        actor_email="actor@example.com"
    )
    assert actor.actor_type == "user"
    
    target = AdminAuditTarget(
        entity_type="user",
        entity_id="123",
        entity_name="Test User"
    )
    assert target.entity_type == "user"
    
    audit_log = AdminAuditLogRead(
        id=uuid4(),
        action="create",
        actor=actor,
        target=target,
        payload={"key": "value"},
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0",
        created_at=datetime.now(UTC)
    )
    assert audit_log.action == "create"
    
    # Test parser models
    job_status = ParserJobStatusRead(
        job_name="daily_update",
        state="running",
        last_run_at=datetime.now(UTC),
        next_run_at=None,
        last_duration_ms=1500,
        error=None
    )
    assert job_status.job_name == "daily_update"
    
    parser_status = ParserStatusRead(
        is_enabled=True,
        is_healthy=True,
        jobs=[job_status],
        last_check_at=datetime.now(UTC)
    )
    assert parser_status.is_enabled is True
    
    # Test system models
    component = SystemComponentStatus(
        name="database",
        status="healthy",
        response_time_ms=50,
        error=None,
        details={"version": "14"}
    )
    assert component.name == "database"
    
    health = SystemHealthRead(
        status="healthy",
        components=[component],
        checked_at=datetime.now(UTC)
    )
    assert health.status == "healthy"


def test_contracts_not_used_elsewhere() -> None:
    """Verify contracts are not imported or used anywhere else in the codebase."""
    app_root = CONTRACTS_ROOT.parent.parent.parent
    violations: list[str] = []
    
    # Check all Python files except those in contracts directory
    for filepath in app_root.rglob("*.py"):
        if CONTRACTS_ROOT in filepath.parents or filepath.parent == CONTRACTS_ROOT:
            continue
        
        if filepath.name.startswith("test_"):
            # Skip test files as they may import for testing
            continue
        
        content = filepath.read_text(encoding="utf-8")
        if "admin.contracts" in content or "from app.admin.contracts" in content:
            violations.append(
                f"{filepath.relative_to(app_root)}: References admin.contracts"
            )
    
    assert not violations, (
        "Contracts are used elsewhere (they should be isolated):\n"
        + "\n".join(sorted(violations))
    )
