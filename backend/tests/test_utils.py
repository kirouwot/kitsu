"""Test utilities and helpers."""


class MockAsyncRedis:
    """Mock async Redis client for testing."""

    def __init__(self):
        self._data: dict[str, str] = {}

    async def ping(self):
        return True

    async def get(self, key: str) -> str | None:
        return self._data.get(key)

    async def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> bool:
        if nx and key in self._data:
            return False
        self._data[key] = value
        return True

    async def delete(self, key: str) -> int:
        if key in self._data:
            del self._data[key]
            return 1
        return 0

    async def expire(self, key: str, seconds: int) -> bool:
        return key in self._data
