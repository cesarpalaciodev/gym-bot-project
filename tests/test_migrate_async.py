from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.migrate import apply_pending, get_current_version, get_pending, rollback, status


class _AsyncIterator:
    def __init__(self, items: list):
        self._items = items

    def __aiter__(self):
        return self._aiter()

    async def _aiter(self):
        for item in self._items:
            yield item


class TestGetCurrentVersion:
    async def test_returns_zero_when_no_migrations(self) -> None:
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=None)

        with patch("utils.migrate.get_collection", return_value=mock_col):
            assert await get_current_version() == 0

    async def test_returns_latest_version(self) -> None:
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value={"version": 3})

        with patch("utils.migrate.get_collection", return_value=mock_col):
            assert await get_current_version() == 3


class TestGetPending:
    async def test_no_pending_when_up_to_date(self) -> None:
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value={"version": 999})

        with patch("utils.migrate.get_collection", return_value=mock_col):
            pending = await get_pending()
            assert pending == []

    async def test_returns_pending_when_behind(self) -> None:
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value={"version": 0})

        with patch("utils.migrate.get_collection", return_value=mock_col):
            pending = await get_pending()
            versions = [m["version"] for m in pending]
            assert 1 in versions


class TestApplyPending:
    async def test_returns_empty_when_no_pending(self) -> None:
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value={"version": 999})

        with (
            patch("utils.migrate.get_collection", return_value=mock_col),
            patch("utils.migrate.get_database"),
        ):
            result = await apply_pending()
            assert result == []

    async def test_applies_pending_migrations(self) -> None:
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value={"version": 0})
        mock_col.insert_one = AsyncMock()
        mock_db = MagicMock()

        with (
            patch("utils.migrate.get_collection", return_value=mock_col),
            patch("utils.migrate.get_database", return_value=mock_db),
            patch("utils.migrate.importlib.import_module") as mock_import,
        ):
            mock_module = MagicMock()
            mock_module.up = AsyncMock()
            mock_import.return_value = mock_module

            result = await apply_pending()

            assert 1 in result
            mock_module.up.assert_awaited_once_with(mock_db)
            mock_col.insert_one.assert_awaited_once()

    async def test_reraises_on_error(self) -> None:
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value={"version": 0})

        with (
            patch("utils.migrate.get_collection", return_value=mock_col),
            patch("utils.migrate.get_database"),
            patch("utils.migrate.importlib.import_module") as mock_import,
        ):
            mock_module = MagicMock()
            mock_module.up = AsyncMock(side_effect=Exception("Migration failed"))
            mock_import.return_value = mock_module

            with pytest.raises(Exception, match="Migration failed"):
                await apply_pending()


class TestRollback:
    async def test_returns_empty_when_no_migrations(self) -> None:
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=None)

        with patch("utils.migrate.get_collection", return_value=mock_col):
            result = await rollback()
            assert result == []

    async def test_rolls_back_last_migration(self) -> None:
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value={"version": 1})
        mock_col.find = MagicMock()
        mock_col.find.return_value = _AsyncIterator([{"version": 1, "description": "test"}])
        mock_col.delete_one = AsyncMock()
        mock_db = MagicMock()

        with (
            patch("utils.migrate.get_collection", return_value=mock_col),
            patch("utils.migrate.get_database", return_value=mock_db),
            patch("utils.migrate.importlib.import_module") as mock_import,
        ):
            mock_module = MagicMock()
            mock_module.down = AsyncMock()
            mock_import.return_value = mock_module

            result = await rollback(1)

            assert 1 in result
            mock_module.down.assert_awaited_once_with(mock_db)
            mock_col.delete_one.assert_awaited_once_with({"version": 1})

    async def test_skips_missing_migration_script(self) -> None:
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value={"version": 99})
        mock_col.find = MagicMock()
        mock_col.find.return_value = _AsyncIterator([{"version": 99, "description": "missing"}])
        mock_col.delete_one = AsyncMock()

        with (
            patch("utils.migrate.get_collection", return_value=mock_col),
            patch("utils.migrate.get_database"),
        ):
            result = await rollback(1)
            assert result == []


class TestStatus:
    async def test_returns_list_with_applied_status(self) -> None:
        mock_col = AsyncMock()
        mock_col.find = MagicMock()
        mock_col.find.return_value = _AsyncIterator([{"version": 1, "applied_at": "2024-01-01"}])

        with patch("utils.migrate.get_collection", return_value=mock_col):
            result = await status()

        assert len(result) >= 1
        m001 = next(m for m in result if m["version"] == 1)
        assert m001["applied"] is True

    async def test_all_not_applied_when_no_records(self) -> None:
        mock_col = AsyncMock()
        mock_col.find = MagicMock()
        mock_col.find.return_value = _AsyncIterator([])

        with patch("utils.migrate.get_collection", return_value=mock_col):
            result = await status()

        assert len(result) >= 1
        for m in result:
            assert m["applied"] is False
