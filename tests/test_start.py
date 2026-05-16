from __future__ import annotations

from unittest.mock import AsyncMock

from telegram.error import TelegramError

from handlers.start import getgroupid, start, verificar_admin_grupo
from keyboards import menu_principal


class TestVerificarAdminGrupo:
    async def test_private_chat_returns_true(self, mock_update, mock_context):
        mock_update.effective_chat.type = "private"
        result = await verificar_admin_grupo(mock_update, mock_context)
        assert result is True

    async def test_group_admin_returns_true(self, mock_update, mock_context):
        mock_update.effective_chat.type = "group"
        mock_member = AsyncMock()
        mock_member.status = "administrator"
        mock_context.bot.get_chat_member = AsyncMock(return_value=mock_member)
        result = await verificar_admin_grupo(mock_update, mock_context)
        assert result is True

    async def test_group_creator_returns_true(self, mock_update, mock_context):
        mock_update.effective_chat.type = "group"
        mock_member = AsyncMock()
        mock_member.status = "creator"
        mock_context.bot.get_chat_member = AsyncMock(return_value=mock_member)
        result = await verificar_admin_grupo(mock_update, mock_context)
        assert result is True

    async def test_group_non_admin_returns_false(self, mock_update, mock_context):
        mock_update.effective_chat.type = "group"
        mock_member = AsyncMock()
        mock_member.status = "member"
        mock_context.bot.get_chat_member = AsyncMock(return_value=mock_member)
        result = await verificar_admin_grupo(mock_update, mock_context)
        assert result is False

    async def test_group_telegram_error_returns_false(self, mock_update, mock_context):
        mock_update.effective_chat.type = "group"
        mock_context.bot.get_chat_member = AsyncMock(side_effect=TelegramError("API error"))
        result = await verificar_admin_grupo(mock_update, mock_context)
        assert result is False

    async def test_restricted_user_returns_false(self, mock_update, mock_context):
        mock_update.effective_chat.type = "group"
        mock_member = AsyncMock()
        mock_member.status = "restricted"
        mock_context.bot.get_chat_member = AsyncMock(return_value=mock_member)
        result = await verificar_admin_grupo(mock_update, mock_context)
        assert result is False

    async def test_left_user_returns_false(self, mock_update, mock_context):
        mock_update.effective_chat.type = "group"
        mock_member = AsyncMock()
        mock_member.status = "left"
        mock_context.bot.get_chat_member = AsyncMock(return_value=mock_member)
        result = await verificar_admin_grupo(mock_update, mock_context)
        assert result is False


class TestStart:
    async def test_start_private_chat_sends_welcome(self, mock_update, mock_context):
        mock_update.effective_chat.type = "private"
        await start(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once_with("Sistema del gimnasio", reply_markup=menu_principal)

    async def test_start_group_admin_sends_welcome(self, mock_update, mock_context):
        mock_update.effective_chat.type = "group"
        mock_member = AsyncMock()
        mock_member.status = "administrator"
        mock_context.bot.get_chat_member = AsyncMock(return_value=mock_member)
        await start(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once_with("Sistema del gimnasio", reply_markup=menu_principal)

    async def test_start_group_non_admin_rejected(self, mock_update, mock_context):
        mock_update.effective_chat.type = "group"
        mock_member = AsyncMock()
        mock_member.status = "member"
        mock_context.bot.get_chat_member = AsyncMock(return_value=mock_member)
        await start(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once_with("No tienes acceso. Debes ser admin del grupo.")

    async def test_start_group_telegram_error_rejected(self, mock_update, mock_context):
        mock_update.effective_chat.type = "group"
        mock_context.bot.get_chat_member = AsyncMock(side_effect=TelegramError("API error"))
        await start(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once_with("No tienes acceso. Debes ser admin del grupo.")

    async def test_start_supergroup_admin_sends_welcome(self, mock_update, mock_context):
        mock_update.effective_chat.type = "supergroup"
        mock_member = AsyncMock()
        mock_member.status = "administrator"
        mock_context.bot.get_chat_member = AsyncMock(return_value=mock_member)
        await start(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once_with("Sistema del gimnasio", reply_markup=menu_principal)

    async def test_getgroupid_works_in_any_chat_type(self, mock_update, mock_context):
        mock_update.effective_chat.id = -100987654321
        mock_update.effective_chat.type = "supergroup"
        await getgroupid(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once_with("Group ID: -100987654321")
