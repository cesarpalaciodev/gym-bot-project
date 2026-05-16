from unittest.mock import AsyncMock, MagicMock, patch

from utils.auth import ROLE_HIERARCHY, require_role


class TestRoleHierarchy:
    def test_super_admin_highest(self):
        assert ROLE_HIERARCHY["super_admin"] == 3

    def test_admin_middle(self):
        assert ROLE_HIERARCHY["admin"] == 2

    def test_viewer_lowest(self):
        assert ROLE_HIERARCHY["viewer"] == 1

    def test_unknown_role_is_zero(self):
        assert ROLE_HIERARCHY.get("fake_role", 0) == 0

    def test_all_expected_roles_present(self):
        for role in ["super_admin", "admin", "viewer"]:
            assert role in ROLE_HIERARCHY


class TestRequireRole:
    @patch("utils.auth.get_collection")
    async def test_no_admin_does_not_call_handler(self, mock_get_collection):
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=None)
        mock_get_collection.return_value = mock_col

        handler = MagicMock()
        handler.__name__ = "test_handler"

        update = MagicMock()
        update.effective_user.id = 999
        update.effective_user.username = "test"
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        decorator = require_role("admin")
        wrapped = decorator(handler)

        result = await wrapped(update, context)

        handler.assert_not_called()
        assert result is None
        update.message.reply_text.assert_awaited_once_with("No autorizado. Solo administradores.")

    @patch("utils.auth.get_collection")
    async def test_low_role_does_not_call_handler(self, mock_get_collection):
        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value={"telegram_id": 999, "role": "viewer"})
        mock_get_collection.return_value = mock_col

        handler = MagicMock()
        handler.__name__ = "test_handler"

        update = MagicMock()
        update.effective_user.id = 999
        update.effective_user.username = "test"
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        decorator = require_role("admin")
        wrapped = decorator(handler)

        result = await wrapped(update, context)

        handler.assert_not_called()
        assert result is None
        update.message.reply_text.assert_awaited_once_with("No tienes permisos suficientes.")
