import time
from unittest.mock import AsyncMock, patch

import pytest

from handlers import admins

FAKE_USER_ID = 12345
FAKE_TARGET_ID = 99999


@pytest.fixture(autouse=True)
def _patch_admin_service():
    mock_svc = AsyncMock()
    with patch("handlers.admins.get_admin_service", return_value=mock_svc):
        yield mock_svc


@pytest.fixture(autouse=True)
def _clear_admin_state():
    admins.admin_state.clear()
    yield


class TestMenuAdmins:
    async def test_unauthorized_non_super_admin(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_svc.is_super_admin.return_value = False
        await admins.menu_admins(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Solo Super Admin puede acceder")

    async def test_authorized_super_admin(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_svc.is_super_admin.return_value = True
        await admins.menu_admins(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        args = mock_update.message.reply_text.call_args[0][0]
        assert "Menu Admin" in args

    async def test_no_admin_found(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_svc.is_super_admin.return_value = False
        await admins.menu_admins(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Solo Super Admin puede acceder")


class TestAgregarAdminStart:
    async def test_unauthorized_returns_denied(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_svc.is_super_admin.return_value = False
        await admins.agregar_admin_start(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Solo Super Admin puede acceder")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_authorized_sets_state(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_svc.is_super_admin.return_value = True
        await admins.agregar_admin_start(mock_update, mock_context)
        assert admins.admin_state.get(FAKE_USER_ID) == "agregar_admin"
        mock_update.message.reply_text.assert_called_once()
        assert "ID" in mock_update.message.reply_text.call_args[0][0]


class TestListaAdmins:
    async def test_unauthorized_returns_denied(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_svc.is_super_admin.return_value = False
        await admins.lista_admins(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Solo Super Admin puede acceder")

    async def test_empty_list(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_svc.is_super_admin.return_value = True
        mock_svc.list_all_admins.return_value = []
        await admins.lista_admins(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("No hay admins registrados")

    async def test_with_admins(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_svc.is_super_admin.return_value = True

        from services.admin_service import AdminInfo

        mock_svc.list_all_admins.return_value = [
            AdminInfo(telegram_id=1, name="Alice", role="super_admin"),
            AdminInfo(telegram_id=2, name="Bob", role="admin"),
            AdminInfo(telegram_id=3, name="Charlie", role="viewer"),
        ]
        await admins.lista_admins(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Alice" in text
        assert "Bob" in text
        assert "Charlie" in text
        assert "super_admin" in text
        assert "admin" in text
        assert "viewer" in text


class TestQuitarAdminStart:
    async def test_unauthorized_returns_denied(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_svc.is_super_admin.return_value = False
        await admins.quitar_admin_start(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Solo Super Admin puede acceder")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_authorized_sets_state(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_svc.is_super_admin.return_value = True
        await admins.quitar_admin_start(mock_update, mock_context)
        assert admins.admin_state.get(FAKE_USER_ID) == "quitar_admin"
        mock_update.message.reply_text.assert_called_once()
        assert "ID" in mock_update.message.reply_text.call_args[0][0]


class TestCambiarRolStart:
    async def test_unauthorized_returns_denied(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_svc.is_super_admin.return_value = False
        await admins.cambiar_rol_start(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Solo Super Admin puede acceder")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_authorized_sets_state(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_svc.is_super_admin.return_value = True
        await admins.cambiar_rol_start(mock_update, mock_context)
        assert admins.admin_state.get(FAKE_USER_ID) == "cambiar_rol_id"
        mock_update.message.reply_text.assert_called_once()
        assert "ID" in mock_update.message.reply_text.call_args[0][0]


class TestProcesarAdmin:
    async def test_no_state_returns_early(self, mock_update, mock_context, _patch_admin_service):
        mock_update.message.text = "123"
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_not_called()

    async def test_agregar_invalid_id(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_update.message.text = "not_a_number"
        admins.admin_state[FAKE_USER_ID] = "agregar_admin"
        mock_svc.validate_telegram_id.return_value = None
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("ID invalido. Debe ser un numero.")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_agregar_duplicate_admin(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_update.message.text = str(FAKE_TARGET_ID)
        admins.admin_state[FAKE_USER_ID] = "agregar_admin"
        mock_svc.validate_telegram_id.return_value = FAKE_TARGET_ID
        mock_svc.is_admin.return_value = True
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Este usuario ya es admin")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_agregar_admin_asks_for_name(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_update.message.text = str(FAKE_TARGET_ID)
        admins.admin_state[FAKE_USER_ID] = "agregar_admin"
        mock_svc.validate_telegram_id.return_value = FAKE_TARGET_ID
        mock_svc.is_admin.return_value = False
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Ingresa el nombre del nuevo admin:")
        assert admins.admin_state.get(FAKE_USER_ID) == {
            "step": "agregar_nombre",
            "telegram_id": FAKE_TARGET_ID,
            "_ts": pytest.approx(time.time(), abs=2),
        }

    async def test_agregar_nombre_success(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        new_name = "Nuevo Admin"
        mock_update.message.text = new_name
        admins.admin_state[FAKE_USER_ID] = {
            "step": "agregar_nombre",
            "telegram_id": FAKE_TARGET_ID,
            "_ts": time.time(),
        }
        await admins.procesar_admin(mock_update, mock_context)
        mock_svc.add_admin.assert_called_once_with(FAKE_TARGET_ID, new_name, role="admin")
        mock_update.message.reply_text.assert_called_once()
        assert FAKE_USER_ID not in admins.admin_state

    async def test_quitar_admin_success(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_update.message.text = str(FAKE_TARGET_ID)
        admins.admin_state[FAKE_USER_ID] = "quitar_admin"
        mock_svc.validate_telegram_id.return_value = FAKE_TARGET_ID
        mock_svc.remove_admin.return_value = True
        await admins.procesar_admin(mock_update, mock_context)
        mock_svc.remove_admin.assert_called_once_with(FAKE_TARGET_ID)
        mock_update.message.reply_text.assert_called_once_with("Admin eliminado")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_quitar_admin_not_found(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_update.message.text = str(FAKE_TARGET_ID)
        admins.admin_state[FAKE_USER_ID] = "quitar_admin"
        mock_svc.validate_telegram_id.return_value = FAKE_TARGET_ID
        mock_svc.remove_admin.return_value = False
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Admin no encontrado")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_cambiar_rol_invalid_id(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_update.message.text = "invalid"
        admins.admin_state[FAKE_USER_ID] = "cambiar_rol_id"
        mock_svc.validate_telegram_id.return_value = None
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("ID invalido")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_cambiar_rol_not_found(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_update.message.text = str(FAKE_TARGET_ID)
        admins.admin_state[FAKE_USER_ID] = "cambiar_rol_id"
        mock_svc.validate_telegram_id.return_value = FAKE_TARGET_ID
        mock_svc.get_admin_display_info.return_value = None
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Admin no encontrado")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_cambiar_rol_asks_for_role(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_update.message.text = str(FAKE_TARGET_ID)
        admins.admin_state[FAKE_USER_ID] = "cambiar_rol_id"

        from services.admin_service import AdminInfo

        mock_svc.validate_telegram_id.return_value = FAKE_TARGET_ID
        mock_svc.get_admin_display_info.return_value = AdminInfo(
            telegram_id=FAKE_TARGET_ID, name="Target", role="viewer"
        )
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Target" in text
        assert "viewer" in text
        assert "admin" in text
        assert "1." in text
        assert "2." in text
        state = admins.admin_state.get(FAKE_USER_ID)
        assert isinstance(state, dict)
        assert state["step"] == "cambiar_rol_rol"
        assert state["telegram_id"] == FAKE_TARGET_ID

    async def test_cambiar_rol_applies_new_role(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_update.message.text = "1"
        admins.admin_state[FAKE_USER_ID] = {
            "step": "cambiar_rol_rol",
            "telegram_id": FAKE_TARGET_ID,
            "name": "Target",
            "_ts": time.time(),
        }
        mock_svc.change_role.return_value = True
        await admins.procesar_admin(mock_update, mock_context)
        mock_svc.change_role.assert_called_once_with(FAKE_TARGET_ID, "admin")
        mock_update.message.reply_text.assert_called_once()
        assert "Rol actualizado" in mock_update.message.reply_text.call_args[0][0]
        assert FAKE_USER_ID not in admins.admin_state

    async def test_cambiar_rol_applies_viewer_role(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_update.message.text = "2"
        admins.admin_state[FAKE_USER_ID] = {
            "step": "cambiar_rol_rol",
            "telegram_id": FAKE_TARGET_ID,
            "name": "Target",
            "_ts": time.time(),
        }
        mock_svc.change_role.return_value = True
        await admins.procesar_admin(mock_update, mock_context)
        mock_svc.change_role.assert_called_once_with(FAKE_TARGET_ID, "viewer")

    async def test_cambiar_rol_invalid_option(self, mock_update, mock_context, _patch_admin_service):
        mock_update.message.text = "3"
        admins.admin_state[FAKE_USER_ID] = {
            "step": "cambiar_rol_rol",
            "telegram_id": FAKE_TARGET_ID,
            "name": "Target",
            "_ts": time.time(),
        }
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Selecciona 1 o 2")
        assert FAKE_USER_ID in admins.admin_state

    async def test_quitar_admin_invalid_id(self, mock_update, mock_context, _patch_admin_service):
        mock_svc = _patch_admin_service
        mock_update.message.text = "not_a_number"
        admins.admin_state[FAKE_USER_ID] = "quitar_admin"
        mock_svc.validate_telegram_id.return_value = None
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("ID invalido")
        assert FAKE_USER_ID not in admins.admin_state
