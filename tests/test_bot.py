from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


class TestSetupDatabase:
    async def test_calls_init_and_migrate(self) -> None:
        with (
            patch("bot.init_collections", AsyncMock()) as mock_init,
            patch("bot.run_migrations", AsyncMock()) as mock_migrate,
        ):
            from bot import setup_database

            await setup_database()
            mock_init.assert_awaited_once()
            mock_migrate.assert_awaited_once()

    async def test_raises_on_init_error(self) -> None:
        with (
            patch("bot.init_collections", AsyncMock(side_effect=ConnectionError("fail"))),
            patch("bot.run_migrations", AsyncMock()),
        ):
            from bot import setup_database

            with pytest.raises(ConnectionError):
                await setup_database()


class TestBackupCommand:
    @pytest.mark.usefixtures("patch_get_collection")
    async def test_private_chat_rejects(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one = AsyncMock(return_value={"telegram_id": 12345, "role": "admin"})
        mock_update.effective_chat.type = "private"

        from bot import backup_command

        await backup_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once_with("Usa este comando en un grupo")

    @pytest.mark.usefixtures("patch_get_collection")
    async def test_non_admin_rejects(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_update.effective_chat.type = "group"

        from bot import backup_command

        await backup_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_with("No autorizado. Solo administradores.")

    @pytest.mark.usefixtures("patch_get_collection")
    async def test_admin_calls_export(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one = AsyncMock(return_value={"telegram_id": 12345, "role": "admin"})
        mock_update.effective_chat.type = "group"

        with patch("handlers.export.exportar_excel_miembros", AsyncMock()) as mock_export:
            from bot import backup_command

            await backup_command(mock_update, mock_context)
            mock_export.assert_awaited_once()

    @pytest.mark.usefixtures("patch_get_collection")
    async def test_non_admin_db_rejects(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_update.effective_chat.type = "group"

        from bot import backup_command

        await backup_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_with("No autorizado. Solo administradores.")


class TestCancelCommand:
    @pytest.mark.usefixtures("patch_get_collection")
    async def test_clears_all_states(self, mock_update, mock_context):
        user_id = mock_update.effective_user.id
        mock_context.user_data = {"some_key": "value"}

        from handlers.admins import _set_state as set_admin_state
        from handlers.members import _set_state as set_member_state
        from handlers.payments import _set_state as set_payment_state

        set_member_state(user_id, "test")
        set_payment_state(user_id, {"step": "test"})
        set_admin_state(user_id, "test")

        from bot import cancel_command

        await cancel_command(mock_update, mock_context)

        assert mock_context.user_data == {}
        from handlers.admins import admin_state as ads
        from handlers.members import user_state as ms
        from handlers.payments import payment_state as ps

        assert user_id not in ms
        assert user_id not in ps
        assert user_id not in ads

    @pytest.mark.usefixtures("patch_get_collection")
    async def test_replies_cancel_message(self, mock_update, mock_context):
        from bot import cancel_command

        await cancel_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once()


class TestRunDashboard:
    def test_starts_dashboard(self):
        with patch("dashboard.start_dashboard") as mock_start:
            from bot import run_dashboard

            run_dashboard()
            mock_start.assert_called_once()

    def test_handles_import_error(self):
        with patch("dashboard.start_dashboard", side_effect=ImportError("no fastapi")):
            from bot import run_dashboard

            run_dashboard()

    def test_handles_os_error(self):
        with patch("dashboard.start_dashboard", side_effect=OSError("port in use")):
            from bot import run_dashboard

            run_dashboard()
