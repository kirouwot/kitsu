from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Awaitable, Mapping
from typing import Any

import httpx


def run_sync(coro: Awaitable[Any]) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    return _run_in_thread(coro)


def _run_in_thread(coro: Awaitable[Any]) -> Any:
    result: Any = None
    error: BaseException | None = None

    def runner() -> None:
        nonlocal result, error
        try:
            result = asyncio.run(coro)
        except BaseException as exc:  # pragma: no cover - defensive
            error = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()
    if error:
        raise error
    return result


class RateLimitedRequester:
    def __init__(
        self,
        *,
        base_url: str,
        rate_limit_seconds: float = 1.0,
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._rate_limit_seconds = rate_limit_seconds
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._headers = dict(headers or {})
        self._last_request_at: float | None = None

    async def get_json(
        self, path: str, *, params: Mapping[str, str] | None = None
    ) -> Any:
        url = self._build_url(path)
        last_error: httpx.RequestError | None = None
        for attempt in range(self._max_retries + 1):
            await self._respect_rate_limit()
            self._last_request_at = time.monotonic()
            try:
                async with httpx.AsyncClient(
                    timeout=self._timeout_seconds, headers=self._headers
                ) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
            except httpx.RequestError as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    break
                await asyncio.sleep(0.5 * (attempt + 1))

        if last_error:
            raise last_error
        raise RuntimeError(
            "Unexpected state: request failed without capturing an error"
        )


    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self._base_url}/{path.lstrip('/')}"

    async def _respect_rate_limit(self) -> None:
        if not self._rate_limit_seconds or self._last_request_at is None:
            return
        elapsed = time.monotonic() - self._last_request_at
        remaining = self._rate_limit_seconds - elapsed
        if remaining > 0:
            await asyncio.sleep(remaining)
