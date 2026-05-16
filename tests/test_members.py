from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from handlers.members import (
    agregar_miembro_start,
    agregar_varios_start,
    buscar_miembro_start,
    eliminar_miembro_start,
    eliminar_varios_start,
    lista_miembros,
    menu_members,
    procesar_miembro,
    user_state,
)
from keyboards import menu_miembros
from services import reset_services


@pytest.fixture(autouse=True)
def _reset_services():
    reset_services()
    yield


@pytest.fixture(autouse=True)
def _patch_factory_get_collection(mock_collection):
    with patch("services.factory.get_collection", AsyncMock(return_value=mock_collection)):
        yield


@pytest.fixture(autouse=True)
def _clean_user_state():
    user_state.clear()
    yield
    user_state.clear()


@pytest.mark.usefixtures("patch_get_collection")
class TestMenuMembers:
    async def test_menu_members_replies_with_keyboard(self, mock_update, mock_context):
        await menu_members(mock_update, mock_context)

        mock_update.message.reply_text.assert_awaited_once_with("Menu miembros", reply_markup=menu_miembros)


@pytest.mark.usefixtures("patch_get_collection")
class TestAgregarMiembroStart:
    async def test_sets_state_and_sends_prompt(self, mock_update, mock_context):
        await agregar_miembro_start(mock_update, mock_context)

        assert user_state[12345] == "agregar_miembro"
        mock_update.message.reply_text.assert_awaited_once()
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Nombre, Telefono, Fecha" in text


@pytest.mark.usefixtures("patch_get_collection")
class TestAgregarVariosStart:
    async def test_sets_state_and_sends_prompt(self, mock_update, mock_context):
        await agregar_varios_start(mock_update, mock_context)

        assert user_state[12345] == "agregar_varios"
        mock_update.message.reply_text.assert_awaited_once()
        text = mock_update.message.reply_text.await_args[0][0]
        assert "uno por linea" in text.lower()


@pytest.mark.usefixtures("patch_get_collection")
class TestBuscarMiembroStart:
    async def test_sets_state_and_sends_prompt(self, mock_update, mock_context):
        await buscar_miembro_start(mock_update, mock_context)

        assert user_state[12345] == "buscar_miembro"
        mock_update.message.reply_text.assert_awaited_once_with("Ingresa el nombre a buscar")


@pytest.mark.usefixtures("patch_get_collection")
class TestEliminarMiembroStart:
    async def test_sets_state_and_sends_prompt(self, mock_update, mock_context):
        await eliminar_miembro_start(mock_update, mock_context)

        assert user_state[12345] == "eliminar_miembro"
        mock_update.message.reply_text.assert_awaited_once_with("Ingresa el nombre completo del miembro a eliminar")


@pytest.mark.usefixtures("patch_get_collection")
class TestEliminarVariosStart:
    async def test_sets_state_and_sends_prompt(self, mock_update, mock_context):
        await eliminar_varios_start(mock_update, mock_context)

        assert user_state[12345] == "eliminar_varios"
        mock_update.message.reply_text.assert_awaited_once()
        text = mock_update.message.reply_text.await_args[0][0]
        assert "nombres uno por linea" in text.lower()


@pytest.mark.usefixtures("patch_get_collection")
class TestListaMiembros:
    async def test_empty_list_returns_no_members_message(self, mock_update, mock_context, mock_collection):
        mock_collection.find.return_value.to_list = AsyncMock(return_value=[])

        await lista_miembros(mock_update, mock_context)

        mock_update.message.reply_text.assert_awaited_once_with("No hay miembros registrados")

    async def test_with_members_and_last_payment(self, mock_update, mock_context, mock_collection):
        member_id = ObjectId()
        mock_collection.find.return_value.to_list = AsyncMock(
            return_value=[
                {"_id": member_id, "name": "Cesar Palacio", "phone": "3101234567", "active": True},
            ]
        )
        mock_collection.find_one = AsyncMock(
            return_value={
                "member_id": str(member_id),
                "payment_date": "2026-03-20",
                "due_date": "2026-04-20",
                "amount": 500,
                "plan": "Mensual",
            }
        )

        await lista_miembros(mock_update, mock_context)

        text = mock_update.message.reply_text.await_args[0][0]
        assert "MIEMBROS REGISTRADOS" in text
        assert "Cesar Palacio" in text
        assert "3101234567" in text
        assert "Vence: 2026-04-20" in text

    async def test_with_members_no_payments(self, mock_update, mock_context, mock_collection):
        mock_collection.find.return_value.to_list = AsyncMock(
            return_value=[
                {"_id": ObjectId(), "name": "Maria Lopez", "phone": "3158765432", "active": True},
            ]
        )
        mock_collection.find_one = AsyncMock(return_value=None)

        await lista_miembros(mock_update, mock_context)

        text = mock_update.message.reply_text.await_args[0][0]
        assert "Sin pagos registrados" in text

    async def test_with_phone_and_without_phone(self, mock_update, mock_context, mock_collection):
        mock_collection.find.return_value.to_list = AsyncMock(
            return_value=[
                {"_id": ObjectId(), "name": "Con Telefono", "phone": "3101111111", "active": True},
                {"_id": ObjectId(), "name": "Sin Telefono", "phone": None, "active": True},
            ]
        )
        mock_collection.find_one = AsyncMock(return_value=None)

        await lista_miembros(mock_update, mock_context)

        text = mock_update.message.reply_text.await_args[0][0]
        assert "3101111111" in text
        assert "Sin pagos registrados" in text


@pytest.mark.usefixtures("patch_get_collection")
class TestProcesarMiembro:
    async def test_no_state_returns_early(self, mock_update, mock_context):
        assert 12345 not in user_state

        await procesar_miembro(mock_update, mock_context)

        mock_update.message.reply_text.assert_not_called()

    async def test_agregar_valido(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "agregar_miembro"
        mock_update.message.text = "Cesar Palacio Garcia 3101234567 2026-03-20"
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        mock_collection.insert_one.assert_awaited()
        text = mock_update.message.reply_text.await_args[0][0]
        assert "agregado" in text.lower()

    async def test_agregar_formato_incorrecto_pocos_campos(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "agregar_miembro"
        mock_update.message.text = "SoloNombre"

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        mock_update.message.reply_text.assert_awaited_once_with("Formato incorrecto. Usa: Nombre Telefono YYYY-MM-DD")

    async def test_agregar_telefono_invalido_no_digits(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "agregar_miembro"
        mock_update.message.text = "Test User abcdefghij 2026-03-20"

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        mock_update.message.reply_text.assert_awaited_once_with(
            "Telefono invalido. Debe ser 10 digitos colombianos (ej: 3101234567)"
        )

    async def test_agregar_telefono_invalido_corta_longitud(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "agregar_miembro"
        mock_update.message.text = "Test User 310123456 2026-03-20"

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Telefono invalido" in text

    async def test_agregar_telefono_invalido_no_empieza_con_3(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "agregar_miembro"
        mock_update.message.text = "Test User 5101234567 2026-03-20"

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Telefono invalido" in text

    async def test_agregar_fecha_invalida(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "agregar_miembro"
        mock_update.message.text = "Test User 3101234567 2026-13-01"

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        mock_update.message.reply_text.assert_awaited_once_with("Fecha invalida. Formato: YYYY-MM-DD")

    async def test_agregar_miembro_ya_existe(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "agregar_miembro"
        mock_update.message.text = "Cesar Palacio 3101234567 2026-03-20"
        mock_collection.find_one = AsyncMock(return_value={"_id": ObjectId(), "name": "Cesar Palacio"})

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        text = mock_update.message.reply_text.await_args[0][0]
        assert "ya existe" in text.lower()

    async def test_agregar_varios_todos_validos(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "agregar_varios"
        mock_update.message.text = "User One 3101111111 2026-03-20\nUser Two 3102222222 2026-03-21"
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        assert mock_collection.insert_one.await_count == 4
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Agregados: 2" in text
        assert "Errores: 0" in text

    async def test_agregar_varios_con_errores_de_formato(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "agregar_varios"
        mock_update.message.text = "User One 3101111111 2026-03-20\nInvalidLine"
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Agregados: 1" in text
        assert "Errores: 1" in text

    async def test_agregar_varios_con_lineas_vacias(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "agregar_varios"
        mock_update.message.text = "User One 3101111111 2026-03-20\n\nUser Two 3102222222 2026-03-21"
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        assert mock_collection.insert_one.await_count == 4
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Agregados: 2" in text

    async def test_agregar_varios_telefono_invalido_skip(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "agregar_varios"
        mock_update.message.text = "User One 3101111111 2026-03-20\nUser Two 12345 2026-03-21"
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Agregados: 1" in text
        assert "Errores: 1" in text

    async def test_buscar_encontrado_con_pago(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "buscar_miembro"
        mock_update.message.text = "Cesar Palacio"
        member_id = ObjectId()
        mock_collection.find_one = AsyncMock(
            side_effect=[
                {"_id": member_id, "name": "Cesar Palacio", "phone": "3101234567", "active": True},
                {
                    "member_id": str(member_id),
                    "payment_date": "2026-03-01",
                    "due_date": "2026-04-01",
                    "plan": "Mensual",
                },
            ]
        )

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Cesar Palacio" in text
        assert "Ultimo pago: 2026-03-01" in text
        assert "Plan: Mensual" in text

    async def test_buscar_encontrado_sin_telefono(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "buscar_miembro"
        mock_update.message.text = "No Phone"
        member_id = ObjectId()
        mock_collection.find_one = AsyncMock(
            side_effect=[
                {"_id": member_id, "name": "No Phone", "phone": None, "active": True},
                None,
            ]
        )

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        text = mock_update.message.reply_text.await_args[0][0]
        assert "No Phone" in text

    async def test_buscar_no_encontrado(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "buscar_miembro"
        mock_update.message.text = "Nobody Knows"
        mock_collection.find_one = AsyncMock(return_value=None)

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        mock_update.message.reply_text.assert_awaited_once_with("Miembro no encontrado")

    async def test_eliminar_valido(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "eliminar_miembro"
        mock_update.message.text = "Cesar Palacio"
        member_id = ObjectId()
        mock_collection.find_one = AsyncMock(return_value={"_id": member_id, "name": "Cesar Palacio"})

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        mock_collection.delete_one.assert_awaited_once()
        mock_collection.delete_many.assert_awaited_once()
        text = mock_update.message.reply_text.await_args[0][0]
        assert "eliminado" in text.lower()

    async def test_eliminar_no_encontrado(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "eliminar_miembro"
        mock_update.message.text = "Nobody Knows"
        mock_collection.find_one = AsyncMock(return_value=None)

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        mock_update.message.reply_text.assert_awaited_once_with("Miembro 'Nobody Knows' no encontrado")

    async def test_eliminar_varios_todos_encontrados(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "eliminar_varios"
        mock_update.message.text = "User One\nUser Two"
        mock_collection.find_one = AsyncMock(return_value={"_id": ObjectId(), "name": "User"})

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        assert mock_collection.delete_one.await_count == 2
        assert mock_collection.delete_many.await_count == 2
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Eliminados: 2" in text

    async def test_eliminar_varios_con_no_encontrados(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "eliminar_varios"
        mock_update.message.text = "Existing\nGhost"
        mock_collection.find_one = AsyncMock(
            side_effect=[
                {"_id": ObjectId(), "name": "Existing"},
                None,
            ]
        )

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Eliminados: 1" in text
        assert "No encontrados: 1" in text

    async def test_eliminar_varios_con_lineas_vacias(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "eliminar_varios"
        mock_update.message.text = "User One\n\nUser Two"
        mock_collection.find_one = AsyncMock(return_value={"_id": ObjectId(), "name": "User"})

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        assert mock_collection.delete_one.await_count == 2

    async def test_exception_handling_clears_state_and_replies(self, mock_update, mock_context, mock_collection):
        user_state[12345] = "agregar_miembro"
        mock_update.message.text = "Test User 3101234567 2026-03-20"
        mock_collection.find_one = AsyncMock(side_effect=Exception("DB Error"))

        await procesar_miembro(mock_update, mock_context)

        assert 12345 not in user_state
        mock_update.message.reply_text.assert_awaited_with("Error al procesar. Intenta de nuevo.")
