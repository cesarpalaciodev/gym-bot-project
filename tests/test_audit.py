from __future__ import annotations

from unittest.mock import AsyncMock, patch

from utils.audit import log_action


class TestLogAction:
    async def test_inserts_audit_record(self) -> None:
        mock_col = AsyncMock()
        mock_col.insert_one = AsyncMock()

        with patch("utils.audit.get_collection", return_value=mock_col):
            await log_action(
                telegram_id=12345,
                username="testuser",
                action="agregar_miembro",
                detail="Nombre: Juan",
                member_name="Juan",
            )

        mock_col.insert_one.assert_awaited_once()
        call_args = mock_col.insert_one.await_args[0][0]
        assert call_args["telegram_id"] == 12345
        assert call_args["username"] == "testuser"
        assert call_args["action"] == "agregar_miembro"
        assert call_args["detail"] == "Nombre: Juan"
        assert call_args["member_name"] == "Juan"
        assert "created_at" in call_args

    async def test_handles_none_fields(self) -> None:
        mock_col = AsyncMock()
        mock_col.insert_one = AsyncMock()

        with patch("utils.audit.get_collection", return_value=mock_col):
            await log_action(
                telegram_id=None,
                username=None,
                action="test",
                detail=None,
                member_name=None,
            )

        mock_col.insert_one.assert_awaited_once()
        call_args = mock_col.insert_one.await_args[0][0]
        assert call_args["telegram_id"] is None
        assert call_args["username"] is None
        assert call_args["detail"] is None
        assert call_args["member_name"] is None

    async def test_logs_error_on_failure(self) -> None:
        mock_col = AsyncMock()
        mock_col.insert_one = AsyncMock(side_effect=Exception("DB error"))

        with (
            patch("utils.audit.get_collection", return_value=mock_col),
            patch("utils.audit.logger") as mock_logger,
        ):
            await log_action(telegram_id=1, username="u", action="test")

        mock_logger.error.assert_called_once()

    async def test_handles_no_extra_fields(self) -> None:
        mock_col = AsyncMock()
        mock_col.insert_one = AsyncMock()

        with patch("utils.audit.get_collection", return_value=mock_col):
            await log_action(telegram_id=1, username="u", action="test")

        call_args = mock_col.insert_one.await_args[0][0]
        assert call_args["detail"] is None
        assert call_args["member_name"] is None
