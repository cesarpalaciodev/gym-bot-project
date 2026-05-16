import time
from unittest.mock import AsyncMock, patch

import pytest

from handlers import admins

FAKE_USER_ID = 12345
FAKE_SUPER_ADMIN = {"telegram_id": FAKE_USER_ID, "role": "super_admin", "name": "Super"}
FAKE_ADMIN = {"telegram_id": FAKE_USER_ID, "role": "admin", "name": "Admin"}
FAKE_TARGET_ID = 99999


@pytest.fixture(autouse=True)
def _patch_admins_collection(mock_collection):
    with patch("handlers.admins.get_collection", return_value=mock_collection):
        yield


@pytest.fixture(autouse=True)
def _clear_admin_state():
    admins.admin_state.clear()
    yield


class TestMenuAdmins:
    async def test_unauthorized_non_super_admin(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one.return_value = FAKE_ADMIN
        await admins.menu_admins(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Solo Super Admin puede acceder")

    async def test_authorized_super_admin(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one.return_value = FAKE_SUPER_ADMIN
        await admins.menu_admins(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        args = mock_update.message.reply_text.call_args[0][0]
        assert "Menu Admin" in args

    async def test_no_admin_found(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one.return_value = None
        await admins.menu_admins(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Solo Super Admin puede acceder")


class TestAgregarAdminStart:
    async def test_unauthorized_returns_denied(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one.return_value = FAKE_ADMIN
        await admins.agregar_admin_start(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Solo Super Admin puede acceder")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_authorized_sets_state(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one.return_value = FAKE_SUPER_ADMIN
        await admins.agregar_admin_start(mock_update, mock_context)
        assert admins.admin_state.get(FAKE_USER_ID) == "agregar_admin"
        mock_update.message.reply_text.assert_called_once()
        assert "ID" in mock_update.message.reply_text.call_args[0][0]


class TestListaAdmins:
    async def test_unauthorized_returns_denied(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one.return_value = FAKE_ADMIN
        await admins.lista_admins(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Solo Super Admin puede acceder")

    async def test_empty_list(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one.return_value = FAKE_SUPER_ADMIN
        mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
        await admins.lista_admins(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("No hay admins registrados")

    async def test_with_admins(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one.return_value = FAKE_SUPER_ADMIN
        admins_data = [
            {"telegram_id": 1, "name": "Alice", "role": "super_admin"},
            {"telegram_id": 2, "name": "Bob", "role": "admin"},
            {"telegram_id": 3, "name": "Charlie", "role": "viewer"},
        ]
        mock_collection.find.return_value.to_list = AsyncMock(return_value=admins_data)
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
    async def test_unauthorized_returns_denied(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one.return_value = FAKE_ADMIN
        await admins.quitar_admin_start(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Solo Super Admin puede acceder")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_authorized_sets_state(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one.return_value = FAKE_SUPER_ADMIN
        await admins.quitar_admin_start(mock_update, mock_context)
        assert admins.admin_state.get(FAKE_USER_ID) == "quitar_admin"
        mock_update.message.reply_text.assert_called_once()
        assert "ID" in mock_update.message.reply_text.call_args[0][0]


class TestCambiarRolStart:
    async def test_unauthorized_returns_denied(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one.return_value = FAKE_ADMIN
        await admins.cambiar_rol_start(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Solo Super Admin puede acceder")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_authorized_sets_state(self, mock_update, mock_context, mock_collection):
        mock_collection.find_one.return_value = FAKE_SUPER_ADMIN
        await admins.cambiar_rol_start(mock_update, mock_context)
        assert admins.admin_state.get(FAKE_USER_ID) == "cambiar_rol_id"
        mock_update.message.reply_text.assert_called_once()
        assert "ID" in mock_update.message.reply_text.call_args[0][0]


class TestProcesarAdmin:
    async def test_no_state_returns_early(self, mock_update, mock_context, mock_collection):
        mock_update.message.text = "123"
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_not_called()

    async def test_agregar_invalid_id(self, mock_update, mock_context, mock_collection):
        mock_update.message.text = "not_a_number"
        admins.admin_state[FAKE_USER_ID] = "agregar_admin"
        mock_collection.find_one.return_value = FAKE_SUPER_ADMIN
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("ID invalido. Debe ser un numero.")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_agregar_duplicate_admin(self, mock_update, mock_context, mock_collection):
        mock_update.message.text = str(FAKE_TARGET_ID)
        admins.admin_state[FAKE_USER_ID] = "agregar_admin"
        mock_collection.find_one.return_value = {"telegram_id": FAKE_TARGET_ID, "role": "admin"}
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Este usuario ya es admin")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_agregar_admin_asks_for_name(self, mock_update, mock_context, mock_collection):
        mock_update.message.text = str(FAKE_TARGET_ID)
        admins.admin_state[FAKE_USER_ID] = "agregar_admin"
        mock_collection.find_one.return_value = None
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Ingresa el nombre del nuevo admin:")
        assert admins.admin_state.get(FAKE_USER_ID) == {
            "step": "agregar_nombre",
            "telegram_id": FAKE_TARGET_ID,
            "_ts": pytest.approx(time.time(), abs=2),
        }

    async def test_agregar_nombre_success(self, mock_update, mock_context, mock_collection):
        new_name = "Nuevo Admin"
        mock_update.message.text = new_name
        admins.admin_state[FAKE_USER_ID] = {
            "step": "agregar_nombre",
            "telegram_id": FAKE_TARGET_ID,
            "_ts": time.time(),
        }
        await admins.procesar_admin(mock_update, mock_context)
        mock_collection.insert_one.assert_called_once()
        mock_update.message.reply_text.assert_called_once()
        assert FAKE_USER_ID not in admins.admin_state

    async def test_quitar_admin_success(self, mock_update, mock_context, mock_collection):
        mock_update.message.text = str(FAKE_TARGET_ID)
        admins.admin_state[FAKE_USER_ID] = "quitar_admin"
        mock_collection.delete_one.return_value.deleted_count = 1
        await admins.procesar_admin(mock_update, mock_context)
        mock_collection.delete_one.assert_called_once_with({"telegram_id": FAKE_TARGET_ID})
        mock_update.message.reply_text.assert_called_once_with("\u2705 Admin eliminado")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_quitar_admin_not_found(self, mock_update, mock_context, mock_collection):
        mock_update.message.text = str(FAKE_TARGET_ID)
        admins.admin_state[FAKE_USER_ID] = "quitar_admin"
        mock_collection.delete_one.return_value.deleted_count = 0
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Admin no encontrado")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_cambiar_rol_invalid_id(self, mock_update, mock_context, mock_collection):
        mock_update.message.text = "invalid"
        admins.admin_state[FAKE_USER_ID] = "cambiar_rol_id"
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("ID invalido")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_cambiar_rol_not_found(self, mock_update, mock_context, mock_collection):
        mock_update.message.text = str(FAKE_TARGET_ID)
        admins.admin_state[FAKE_USER_ID] = "cambiar_rol_id"
        mock_collection.find_one.return_value = None
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Admin no encontrado")
        assert FAKE_USER_ID not in admins.admin_state

    async def test_cambiar_rol_asks_for_role(self, mock_update, mock_context, mock_collection):
        mock_update.message.text = str(FAKE_TARGET_ID)
        admins.admin_state[FAKE_USER_ID] = "cambiar_rol_id"
        target_admin = {"telegram_id": FAKE_TARGET_ID, "name": "Target", "role": "viewer"}
        mock_collection.find_one.return_value = target_admin
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

    async def test_cambiar_rol_applies_new_role(self, mock_update, mock_context, mock_collection):
        mock_update.message.text = "1"
        admins.admin_state[FAKE_USER_ID] = {
            "step": "cambiar_rol_rol",
            "telegram_id": FAKE_TARGET_ID,
            "name": "Target",
            "_ts": time.time(),
        }
        await admins.procesar_admin(mock_update, mock_context)
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args[0]
        assert call_args[0] == {"telegram_id": FAKE_TARGET_ID}
        assert call_args[1]["$set"]["role"] == "admin"
        mock_update.message.reply_text.assert_called_once()
        assert "Rol actualizado" in mock_update.message.reply_text.call_args[0][0]
        assert FAKE_USER_ID not in admins.admin_state

    async def test_cambiar_rol_applies_viewer_role(self, mock_update, mock_context, mock_collection):
        mock_update.message.text = "2"
        admins.admin_state[FAKE_USER_ID] = {
            "step": "cambiar_rol_rol",
            "telegram_id": FAKE_TARGET_ID,
            "name": "Target",
            "_ts": time.time(),
        }
        await admins.procesar_admin(mock_update, mock_context)
        call_args = mock_collection.update_one.call_args[0]
        assert call_args[1]["$set"]["role"] == "viewer"

    async def test_cambiar_rol_invalid_option(self, mock_update, mock_context, mock_collection):
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

    async def test_quitar_admin_invalid_id(self, mock_update, mock_context, mock_collection):
        mock_update.message.text = "not_a_number"
        admins.admin_state[FAKE_USER_ID] = "quitar_admin"
        await admins.procesar_admin(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("ID invalido")
        assert FAKE_USER_ID not in admins.admin_state
