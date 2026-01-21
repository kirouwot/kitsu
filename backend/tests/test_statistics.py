"""
Tests for Statistics Service (STATISTICS-01).

This test suite verifies:
1. Statistics don't modify data (READ-ONLY)
2. No access without permission (RBAC)
3. Empty DB returns correct zeros
4. Filled DB returns correct values
5. Partial errors return partial data + warnings
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.models.base import Base
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.parser.tables import parser_jobs, parser_sources
from app.services.statistics import StatisticsService
from app.services.statistics.schemas import (
    AnimeStatistics,
    EpisodeStatistics,
    ParserStatistics,
    ErrorStatistics,
    ActivityStatistics,
    OverviewStatistics,
)
from app.auth import rbac_contract


class AsyncSessionAdapter:
    """Adapter to make synchronous session work with async code."""
    
    def __init__(self, session: Session, engine: sa.Engine) -> None:
        self._session = session
        self._engine = engine

    def get_bind(self) -> sa.Engine:
        return self._engine

    async def execute(self, *args, **kwargs):
        return self._session.execute(*args, **kwargs)

    async def commit(self) -> None:
        self._session.commit()

    async def rollback(self) -> None:
        self._session.rollback()

    @asynccontextmanager
    async def begin(self):
        with self._session.begin():
            yield self


@pytest.fixture()
def db_session():
    """Create a test database session with minimal tables."""
    engine = sa.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=sa.pool.StaticPool,
    )
    # Only create tables that work with SQLite (no ARRAY types)
    Base.metadata.create_all(engine, tables=[
        AuditLog.__table__,
        User.__table__,
        Role.__table__,
        Permission.__table__,
        UserRole.__table__,
        RolePermission.__table__,
        parser_jobs,
        parser_sources,
    ])
    session = Session(engine)
    adapter = AsyncSessionAdapter(session, engine)
    yield adapter, session
    session.close()


class TestRBACContract:
    """Test RBAC contract for statistics permission."""
    
    def test_statistics_permission_exists(self):
        """RBAC: admin.statistics.view permission must exist in contract."""
        assert "admin.statistics.view" in rbac_contract.ADMIN_PERMISSIONS
        assert "admin.statistics.view" in rbac_contract.ALLOWED_PERMISSIONS
    
    def test_super_admin_has_statistics_permission(self):
        """RBAC: super_admin role has statistics permission."""
        super_admin_perms = rbac_contract.ROLE_PERMISSION_MAPPINGS["super_admin"]
        assert "admin.statistics.view" in super_admin_perms
    
    def test_admin_has_statistics_permission(self):
        """RBAC: admin role has statistics permission."""
        admin_perms = rbac_contract.ROLE_PERMISSION_MAPPINGS["admin"]
        assert "admin.statistics.view" in admin_perms
    
    def test_regular_user_no_statistics_permission(self):
        """RBAC: regular user doesn't have statistics permission."""
        user_perms = rbac_contract.ROLE_PERMISSION_MAPPINGS["user"]
        assert "admin.statistics.view" not in user_perms
    
    def test_system_roles_no_statistics_permission(self):
        """RBAC: system roles cannot have admin.statistics.view permission."""
        parser_perms = rbac_contract.ROLE_PERMISSION_MAPPINGS["parser_bot"]
        worker_perms = rbac_contract.ROLE_PERMISSION_MAPPINGS["worker_bot"]
        assert "admin.statistics.view" not in parser_perms
        assert "admin.statistics.view" not in worker_perms


class TestStatisticsServiceReadOnly:
    """Test that statistics service is READ-ONLY and doesn't modify data."""
    
    @pytest.mark.anyio
    async def test_parser_statistics_no_side_effects(self, db_session):
        """Statistics: get_parser_statistics doesn't modify database."""
        adapter, session = db_session
        
        # Create parser source
        session.execute(
            sa.insert(parser_sources).values(
                code="test_source",
                enabled=True,
            )
        )
        session.commit()
        
        # Get count before
        count_before = session.execute(
            sa.select(sa.func.count()).select_from(parser_sources)
        ).scalar()
        
        # Call statistics
        stats_service = StatisticsService(adapter)
        result, warnings = await stats_service.get_parser_statistics()
        
        # Verify no changes
        count_after = session.execute(
            sa.select(sa.func.count()).select_from(parser_sources)
        ).scalar()
        
        assert count_before == count_after
        assert result is not None
    
    @pytest.mark.anyio
    async def test_audit_statistics_no_side_effects(self, db_session):
        """Statistics: audit statistics don't modify database."""
        adapter, session = db_session
        
        # Create audit log
        user_id = uuid.uuid4()
        log = AuditLog(
            actor_id=user_id,
            actor_type="user",
            action="test.action",
            entity_type="test",
            entity_id=str(uuid.uuid4()),
        )
        session.add(log)
        session.commit()
        
        # Get count before
        count_before = session.query(AuditLog).count()
        
        # Call statistics
        stats_service = StatisticsService(adapter)
        error_result, _ = await stats_service.get_error_statistics()
        activity_result, _ = await stats_service.get_activity_statistics()
        
        # Verify no changes
        count_after = session.query(AuditLog).count()
        assert count_before == count_after
        assert error_result is not None
        assert activity_result is not None
    
    @pytest.mark.anyio
    async def test_get_overview_no_side_effects(self, db_session):
        """Statistics: get_overview doesn't modify database."""
        adapter, session = db_session
        
        # Create some data
        log = AuditLog(
            actor_id=uuid.uuid4(),
            actor_type="user",
            action="test.action",
            entity_type="test",
            entity_id=str(uuid.uuid4()),
        )
        session.add(log)
        session.commit()
        
        # Get counts before
        audit_count_before = session.query(AuditLog).count()
        
        # Call statistics
        stats_service = StatisticsService(adapter)
        result = await stats_service.get_overview()
        
        # Verify no changes
        audit_count_after = session.query(AuditLog).count()
        assert audit_count_before == audit_count_after
        assert isinstance(result, OverviewStatistics)


class TestStatisticsServiceEmptyDatabase:
    """Test statistics with empty database."""
    
    @pytest.mark.anyio
    async def test_parser_statistics_empty_db(self, db_session):
        """Statistics: empty DB returns zeros for parser."""
        adapter, session = db_session
        stats_service = StatisticsService(adapter)
        
        result, warnings = await stats_service.get_parser_statistics()
        
        assert result is not None
        assert result.total_parser_jobs == 0
        assert result.successful_jobs == 0
        assert result.failed_jobs == 0
        assert result.running_jobs == 0
        assert result.disabled_sources == 0
        assert result.active_sources == 0
    
    @pytest.mark.anyio
    async def test_error_statistics_empty_db(self, db_session):
        """Statistics: empty DB returns zeros for errors."""
        adapter, session = db_session
        stats_service = StatisticsService(adapter)
        
        result, warnings = await stats_service.get_error_statistics()
        
        assert result is not None
        assert result.total_errors == 0
        assert result.errors_last_24h == 0
        assert result.errors_last_7d == 0
        assert result.critical_errors == 0
        assert len(result.most_frequent_error_types) == 0
    
    @pytest.mark.anyio
    async def test_activity_statistics_empty_db(self, db_session):
        """Statistics: empty DB returns zeros for activity."""
        adapter, session = db_session
        stats_service = StatisticsService(adapter)
        
        result, warnings = await stats_service.get_activity_statistics()
        
        assert result is not None
        assert result.total_audit_logs == 0
        assert result.actions_last_24h == 0
        assert len(result.most_active_admins) == 0
        assert len(result.most_common_actions) == 0


class TestStatisticsServiceWithData:
    """Test statistics with populated database."""
    
    @pytest.mark.anyio
    async def test_parser_statistics_counts_jobs(self, db_session):
        """Statistics: correctly counts parser jobs by status."""
        adapter, session = db_session
        
        # Create parser source
        session.execute(
            sa.insert(parser_sources).values(
                code="test_source",
                enabled=True,
            )
        )
        session.commit()
        
        source_id = session.execute(
            sa.select(parser_sources.c.id)
        ).scalar()
        
        # Create jobs with different statuses
        now = datetime.now(timezone.utc)
        session.execute(
            sa.insert(parser_jobs).values([
                {
                    "source_id": source_id,
                    "job_type": "sync",
                    "status": "success",
                    "started_at": now - timedelta(hours=2),
                    "finished_at": now - timedelta(hours=1),
                },
                {
                    "source_id": source_id,
                    "job_type": "sync",
                    "status": "failed",
                    "started_at": now - timedelta(hours=1),
                    "finished_at": now,
                },
                {
                    "source_id": source_id,
                    "job_type": "sync",
                    "status": "running",
                    "started_at": now,
                    "finished_at": None,
                },
            ])
        )
        session.commit()
        
        stats_service = StatisticsService(adapter)
        result, warnings = await stats_service.get_parser_statistics()
        
        assert result is not None
        assert result.total_parser_jobs == 3
        assert result.successful_jobs >= 1
        assert result.failed_jobs >= 1
        assert result.running_jobs >= 1
        assert result.active_sources == 1
    
    @pytest.mark.anyio
    async def test_error_statistics_counts_errors(self, db_session):
        """Statistics: correctly counts errors from audit logs."""
        adapter, session = db_session
        
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        
        # Create error audit logs
        error1 = AuditLog(
            actor_id=user_id,
            actor_type="user",
            action="anime.edit.failed",
            entity_type="anime",
            entity_id=str(uuid.uuid4()),
            created_at=now - timedelta(hours=1),
        )
        error2 = AuditLog(
            actor_id=user_id,
            actor_type="user",
            action="permission_denied",
            entity_type="anime",
            entity_id=str(uuid.uuid4()),
            created_at=now - timedelta(days=2),
        )
        error3 = AuditLog(
            actor_id=user_id,
            actor_type="user",
            action="critical.failure",
            entity_type="system",
            entity_id="system",
            created_at=now - timedelta(hours=12),
        )
        
        session.add_all([error1, error2, error3])
        session.commit()
        
        stats_service = StatisticsService(adapter)
        result, warnings = await stats_service.get_error_statistics()
        
        assert result is not None
        assert result.total_errors >= 2  # At least failed and denied
        assert result.errors_last_24h >= 1
        assert result.critical_errors >= 1
    
    @pytest.mark.anyio
    async def test_activity_statistics_counts_actions(self, db_session):
        """Statistics: correctly counts admin activity."""
        adapter, session = db_session
        
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        
        # Create audit logs
        log1 = AuditLog(
            actor_id=user_id,
            actor_type="user",
            action="anime.edit",
            entity_type="anime",
            entity_id=str(uuid.uuid4()),
            created_at=now - timedelta(hours=1),
        )
        log2 = AuditLog(
            actor_id=user_id,
            actor_type="user",
            action="anime.edit",
            entity_type="anime",
            entity_id=str(uuid.uuid4()),
            created_at=now - timedelta(hours=2),
        )
        
        session.add_all([log1, log2])
        session.commit()
        
        stats_service = StatisticsService(adapter)
        result, warnings = await stats_service.get_activity_statistics()
        
        assert result is not None
        assert result.total_audit_logs == 2
        assert result.actions_last_24h == 2
        assert len(result.most_active_admins) >= 1
        assert len(result.most_common_actions) >= 1


class TestStatisticsServicePartialFailure:
    """Test that partial failures return data + warnings."""
    
    @pytest.mark.anyio
    async def test_overview_returns_partial_data_on_error(self, db_session):
        """Statistics: overview returns partial data if some queries fail."""
        adapter, session = db_session
        
        # Create some valid data
        log = AuditLog(
            actor_id=uuid.uuid4(),
            actor_type="user",
            action="test.action",
            entity_type="test",
            entity_id=str(uuid.uuid4()),
        )
        session.add(log)
        session.commit()
        
        stats_service = StatisticsService(adapter)
        result = await stats_service.get_overview()
        
        # Should always return a valid response
        assert isinstance(result, OverviewStatistics)
        assert isinstance(result.anime, AnimeStatistics)
        assert isinstance(result.episodes, EpisodeStatistics)
        assert isinstance(result.parser, ParserStatistics)
        assert isinstance(result.errors, ErrorStatistics)
        assert isinstance(result.activity, ActivityStatistics)
        
        # Should have valid data
        assert result.anime.total_anime >= 0
        assert result.activity.total_audit_logs >= 0

