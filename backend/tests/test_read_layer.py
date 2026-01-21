"""
Tests for CQRS-lite read layer

Validates:
- DTOs are immutable (frozen dataclasses)
- Repositories use ONLY SELECT queries
- No write operations (commit/flush/add/delete)
- No domain logic
- No use_case imports
"""

import uuid
from datetime import datetime, timezone
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.read import (
    AnimeFeedDTO,
    AnimeFeedReadRepository,
    UserLibraryDTO,
    UserLibraryReadRepository,
    WatchProgressDTO,
    WatchProgressReadRepository,
)


class TestDTOImmutability:
    """Test that all DTOs are immutable (frozen=True)"""

    def test_anime_feed_dto_is_frozen(self) -> None:
        dto = AnimeFeedDTO(
            anime_id=uuid.uuid4(),
            title="Test Anime",
            poster_url="https://example.com/poster.jpg",
            episodes_count=12,
        )

        with pytest.raises(AttributeError):
            dto.title = "Modified Title"  # type: ignore

    def test_user_library_dto_is_frozen(self) -> None:
        dto = UserLibraryDTO(
            anime_id=uuid.uuid4(),
            title="Test Anime",
            last_episode=5,
            progress_percent=50.0,
        )

        with pytest.raises(AttributeError):
            dto.last_episode = 10  # type: ignore

    def test_watch_progress_dto_is_frozen(self) -> None:
        dto = WatchProgressDTO(
            anime_id=uuid.uuid4(),
            episode=3,
            position_seconds=120,
            progress_percent=75.0,
        )

        with pytest.raises(AttributeError):
            dto.episode = 5  # type: ignore


class MockAsyncSession:
    """Mock async session that only allows SELECT operations"""

    def __init__(self) -> None:
        self.execute_calls: list[Any] = []
        self.commit_called = False
        self.flush_called = False
        self.add_called = False
        self.delete_called = False
        self.rollback_called = False

    async def execute(self, stmt: Any) -> Any:
        """Record SELECT queries"""
        self.execute_calls.append(stmt)
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        return mock_result

    async def commit(self) -> None:
        """Should never be called in read layer"""
        self.commit_called = True
        raise AssertionError("READ layer called commit() - VIOLATION!")

    async def flush(self) -> None:
        """Should never be called in read layer"""
        self.flush_called = True
        raise AssertionError("READ layer called flush() - VIOLATION!")

    def add(self, instance: Any) -> None:
        """Should never be called in read layer"""
        self.add_called = True
        raise AssertionError("READ layer called add() - VIOLATION!")

    async def delete(self, instance: Any) -> None:
        """Should never be called in read layer"""
        self.delete_called = True
        raise AssertionError("READ layer called delete() - VIOLATION!")

    async def rollback(self) -> None:
        """Should never be called in read layer"""
        self.rollback_called = True
        raise AssertionError("READ layer called rollback() - VIOLATION!")


class TestAnimeFeedReadRepository:
    """Test AnimeFeedReadRepository uses only SELECT"""

    @pytest.mark.anyio
    async def test_get_feed_uses_only_select(self) -> None:
        session = MockAsyncSession()
        repo = AnimeFeedReadRepository(session)

        result = await repo.get_feed(limit=10)

        # Should execute exactly one SELECT query
        assert len(session.execute_calls) == 1
        # Should never call write operations
        assert not session.commit_called
        assert not session.flush_called
        assert not session.add_called
        assert not session.delete_called
        # Result should be list of DTOs
        assert isinstance(result, list)

    @pytest.mark.anyio
    async def test_get_feed_returns_dtos(self) -> None:
        session = MockAsyncSession()

        # Mock result with test data
        class MockRow:
            def __init__(self) -> None:
                self.id = uuid.uuid4()
                self.title = "Test Anime"
                self.poster_url = "https://example.com/poster.jpg"
                self.episodes_count = 12

        mock_result = MagicMock()
        mock_result.all.return_value = [MockRow()]

        async def mock_execute(stmt: Any) -> Any:
            return mock_result

        session.execute = mock_execute  # type: ignore

        repo = AnimeFeedReadRepository(session)
        result = await repo.get_feed(limit=10)

        assert len(result) == 1
        assert isinstance(result[0], AnimeFeedDTO)
        assert result[0].title == "Test Anime"
        assert result[0].episodes_count == 12


class TestUserLibraryReadRepository:
    """Test UserLibraryReadRepository uses only SELECT"""

    @pytest.mark.anyio
    async def test_get_user_library_uses_only_select(self) -> None:
        session = MockAsyncSession()
        repo = UserLibraryReadRepository(session)

        result = await repo.get_user_library(user_id=uuid.uuid4())

        # Should execute exactly one SELECT query
        assert len(session.execute_calls) == 1
        # Should never call write operations
        assert not session.commit_called
        assert not session.flush_called
        assert not session.add_called
        assert not session.delete_called
        # Result should be list of DTOs
        assert isinstance(result, list)

    @pytest.mark.anyio
    async def test_get_user_library_returns_dtos(self) -> None:
        session = MockAsyncSession()

        # Mock result with test data
        class MockRow:
            def __init__(self) -> None:
                self.id = uuid.uuid4()
                self.title = "Test Anime"
                self.episode = 5
                self.progress_percent = 50.0

        mock_result = MagicMock()
        mock_result.all.return_value = [MockRow()]

        async def mock_execute(stmt: Any) -> Any:
            return mock_result

        session.execute = mock_execute  # type: ignore

        repo = UserLibraryReadRepository(session)
        result = await repo.get_user_library(user_id=uuid.uuid4())

        assert len(result) == 1
        assert isinstance(result[0], UserLibraryDTO)
        assert result[0].title == "Test Anime"
        assert result[0].last_episode == 5
        assert result[0].progress_percent == 50.0


class TestWatchProgressReadRepository:
    """Test WatchProgressReadRepository uses only SELECT"""

    @pytest.mark.anyio
    async def test_get_uses_only_select(self) -> None:
        session = MockAsyncSession()
        repo = WatchProgressReadRepository(session)

        result = await repo.get(user_id=uuid.uuid4(), anime_id=uuid.uuid4())

        # Should execute exactly one SELECT query
        assert len(session.execute_calls) == 1
        # Should never call write operations
        assert not session.commit_called
        assert not session.flush_called
        assert not session.add_called
        assert not session.delete_called
        # Result should be None or DTO
        assert result is None or isinstance(result, WatchProgressDTO)

    @pytest.mark.anyio
    async def test_get_returns_dto_when_found(self) -> None:
        session = MockAsyncSession()

        # Mock progress object
        class MockProgress:
            def __init__(self) -> None:
                self.anime_id = uuid.uuid4()
                self.episode = 3
                self.position_seconds = 120
                self.progress_percent = 75.0

        mock_progress = MockProgress()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_progress

        async def mock_execute(stmt: Any) -> Any:
            return mock_result

        session.execute = mock_execute  # type: ignore

        repo = WatchProgressReadRepository(session)
        result = await repo.get(user_id=uuid.uuid4(), anime_id=uuid.uuid4())

        assert result is not None
        assert isinstance(result, WatchProgressDTO)
        assert result.episode == 3
        assert result.position_seconds == 120
        assert result.progress_percent == 75.0

    @pytest.mark.anyio
    async def test_get_returns_none_when_not_found(self) -> None:
        session = MockAsyncSession()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        async def mock_execute(stmt: Any) -> Any:
            return mock_result

        session.execute = mock_execute  # type: ignore

        repo = WatchProgressReadRepository(session)
        result = await repo.get(user_id=uuid.uuid4(), anime_id=uuid.uuid4())

        assert result is None


class TestReadLayerConstraints:
    """Test that read layer respects CQRS-lite constraints"""

    def test_no_use_case_imports(self) -> None:
        """Verify read layer does not import use_cases"""
        import app.read as read_module

        # Check module source for use_case imports
        module_file = read_module.__file__
        assert module_file is not None

        with open(module_file, "r") as f:
            content = f.read()
            # Should not import from use_cases
            assert "from ..use_cases" not in content
            assert "from ...use_cases" not in content
            assert "import use_cases" not in content

    def test_repositories_have_type_hints(self) -> None:
        """Verify all read repositories use type hints"""
        # Check that repositories have proper type annotations
        from inspect import signature, Parameter

        # AnimeFeedReadRepository
        sig = signature(AnimeFeedReadRepository.get_feed)
        assert sig.return_annotation != Parameter.empty

        # UserLibraryReadRepository
        sig = signature(UserLibraryReadRepository.get_user_library)
        assert sig.return_annotation != Parameter.empty

        # WatchProgressReadRepository
        sig = signature(WatchProgressReadRepository.get)
        assert sig.return_annotation != Parameter.empty
