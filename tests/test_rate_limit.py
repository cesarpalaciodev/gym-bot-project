from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.rate_limit import check_rate_limit, check_rate_limit_sync, close_rate_limiter


@pytest.fixture(autouse=True)
def _clear_store():
    from utils.rate_limit import _fallback_store

    _fallback_store.clear()
    yield
    _fallback_store.clear()


class TestCheckRateLimit:
    async def test_allows_first_request(self) -> None:
        assert await check_rate_limit(1) is True

    async def test_blocks_after_max(self) -> None:
        for _ in range(10):
            await check_rate_limit(1)
        assert await check_rate_limit(1) is False

    async def test_allows_after_window_expires(self) -> None:
        with patch("utils.rate_limit.time.time") as mock_time:
            mock_time.return_value = 100.0
            for _ in range(10):
                await check_rate_limit(1)
            assert await check_rate_limit(1) is False
            mock_time.return_value = 106.0
            assert await check_rate_limit(1) is True

    async def test_different_users_independent(self) -> None:
        for _ in range(10):
            await check_rate_limit(1)
        assert await check_rate_limit(2) is True

    async def test_redis_path(self) -> None:
        with (
            patch("utils.rate_limit._get_redis") as mock_redis,
            patch("utils.rate_limit.REDIS_URL", "redis://localhost"),
        ):
            mock_conn = AsyncMock()
            mock_conn.zremrangebyscore = AsyncMock()
            mock_conn.zcard = AsyncMock(return_value=5)
            mock_conn.zadd = AsyncMock()
            mock_conn.expire = AsyncMock()
            mock_redis.return_value = mock_conn
            assert await check_rate_limit(1, max_per_window=10) is True
            mock_conn.zcard.assert_awaited_once()

    async def test_redis_blocks_at_limit(self) -> None:
        with (
            patch("utils.rate_limit._get_redis") as mock_redis,
            patch("utils.rate_limit.REDIS_URL", "redis://localhost"),
        ):
            mock_conn = AsyncMock()
            mock_conn.zremrangebyscore = AsyncMock()
            mock_conn.zcard = AsyncMock(return_value=10)
            mock_conn.expire = AsyncMock()
            mock_redis.return_value = mock_conn
            assert await check_rate_limit(1, max_per_window=10) is False

    async def test_redis_error_falls_back(self) -> None:
        with (
            patch("utils.rate_limit._get_redis") as mock_redis,
            patch("utils.rate_limit.REDIS_URL", "redis://localhost"),
        ):
            mock_conn = AsyncMock()
            mock_conn.zremrangebyscore = AsyncMock(side_effect=Exception("Redis down"))
            mock_redis.return_value = mock_conn
            assert await check_rate_limit(1) is True

    async def test_no_redis_uses_fallback(self) -> None:
        with patch("utils.rate_limit.REDIS_URL", ""):
            assert await check_rate_limit(1) is True
            for _ in range(9):
                await check_rate_limit(1)
            assert await check_rate_limit(1) is False

    async def test_close_rate_limiter(self) -> None:
        with patch("utils.rate_limit._redis", AsyncMock()):
            await close_rate_limiter()
            from utils.rate_limit import _redis

            assert _redis is None


class TestCheckRateLimitSync:
    def test_allows_first_request(self) -> None:
        assert check_rate_limit_sync(1) is True

    def test_blocks_after_max(self) -> None:
        for _ in range(10):
            check_rate_limit_sync(1)
        assert check_rate_limit_sync(1) is False

    def test_allows_after_window(self) -> None:
        with patch("utils.rate_limit.time.time") as mock_time:
            mock_time.return_value = 100.0
            for _ in range(10):
                check_rate_limit_sync(1)
            assert check_rate_limit_sync(1) is False
            mock_time.return_value = 106.0
            assert check_rate_limit_sync(1) is True

    def test_different_users_independent_sync(self) -> None:
        for _ in range(10):
            check_rate_limit_sync(1)
        assert check_rate_limit_sync(2) is True
