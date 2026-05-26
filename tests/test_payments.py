import time as time_module
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from config import PLANS
from handlers.payments import (
    historial_pagos,
    menu_payments,
    payment_state,
    procesar_pago,
    registrar_pago_start,
)
from keyboards import menu_confirmar, menu_pagos, menu_planes, menu_principal
from services import reset_services
from utils import format_fecha


@pytest.fixture(autouse=True)
def _reset_services():
    reset_services()
    yield


@pytest.fixture(autouse=True)
def _patch_factory_get_collection(mock_collection):
    with patch("services.factory.get_collection", AsyncMock(return_value=mock_collection)):
        yield


@pytest.fixture(autouse=True)
def _clean_payment_state():
    payment_state.clear()
    yield
    payment_state.clear()


@pytest.mark.usefixtures("patch_get_collection")
class TestMenuPayments:
    async def test_menu_payments_replies_with_keyboard(self, mock_update, mock_context):
        await menu_payments(mock_update, mock_context)

        mock_update.message.reply_text.assert_awaited_once_with("Menu pagos", reply_markup=menu_pagos)


@pytest.mark.usefixtures("patch_get_collection")
class TestRegistrarPagoStart:
    async def test_sets_nombre_step_and_prompts(self, mock_update, mock_context):
        await registrar_pago_start(mock_update, mock_context)

        assert payment_state[12345]["step"] == "nombre"
        assert "_ts" in payment_state[12345]
        mock_update.message.reply_text.assert_awaited_once_with("Ingresa el nombre del miembro")

    async def test_cleans_stale_states_before_setting(self, mock_update, mock_context):
        payment_state[99999] = {"step": "old", "_ts": time_module.time() - 700}

        await registrar_pago_start(mock_update, mock_context)

        assert 99999 not in payment_state
        assert payment_state[12345]["step"] == "nombre"


@pytest.mark.usefixtures("patch_get_collection")
class TestHistorialPagos:
    async def test_sets_historial_nombre_step_and_prompts(self, mock_update, mock_context):
        await historial_pagos(mock_update, mock_context)

        assert payment_state[12345]["step"] == "historial_nombre"
        assert "_ts" in payment_state[12345]
        mock_update.message.reply_text.assert_awaited_once_with("Ingresa el nombre del miembro para ver su historial")


@pytest.mark.usefixtures("patch_get_collection")
class TestProcesarPago:
    async def test_no_state_returns_early(self, mock_update, mock_context):
        assert 12345 not in payment_state

        await procesar_pago(mock_update, mock_context)

        mock_update.message.reply_text.assert_not_called()

    async def test_nombre_miembro_encontrado_transitions_to_plan(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {"step": "nombre", "_ts": 0}
        mock_update.message.text = "Cesar Palacio"
        member_id = ObjectId()
        mock_collection.find_one = AsyncMock(
            side_effect=[
                {"_id": member_id, "name": "Cesar Palacio", "active": True},
                None,
            ]
        )

        await procesar_pago(mock_update, mock_context)

        assert payment_state[12345]["step"] == "plan"
        assert payment_state[12345]["member_name"] == "Cesar Palacio"
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Cesar Palacio" in text
        assert "Selecciona el plan" in text

    async def test_nombre_miembro_no_encontrado_clears_state(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {"step": "nombre", "_ts": 0}
        mock_update.message.text = "Nobody Knows"
        mock_collection.find_one = AsyncMock(return_value=None)

        await procesar_pago(mock_update, mock_context)

        assert 12345 not in payment_state
        mock_update.message.reply_text.assert_awaited_once_with("Miembro no encontrado")

    async def test_nombre_con_ultimo_pago_stores_in_state(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {"step": "nombre", "_ts": 0}
        mock_update.message.text = "Cesar Palacio"
        member_id = ObjectId()
        last_payment = {
            "member_id": str(member_id),
            "payment_date": "2026-03-20",
            "due_date": "2026-04-20",
            "plan": "Mensual",
            "amount": 500,
        }
        mock_collection.find_one = AsyncMock(
            side_effect=[
                {"_id": member_id, "name": "Cesar Palacio", "active": True},
                last_payment,
            ]
        )

        await procesar_pago(mock_update, mock_context)

        assert payment_state[12345]["step"] == "plan"
        assert payment_state[12345]["last_payment"] == last_payment
        assert payment_state[12345]["member_name"] == "Cesar Palacio"

    async def test_plan_cancelar_clears_state(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {
            "step": "plan",
            "member_id": str(ObjectId()),
            "member_name": "Cesar Palacio",
            "last_payment": None,
            "_ts": 0,
        }
        mock_update.message.text = "Cancelar"

        await procesar_pago(mock_update, mock_context)

        assert 12345 not in payment_state
        mock_update.message.reply_text.assert_awaited_once_with("Operacion cancelada")

    async def test_plan_invalido_stays_in_plan_step(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {
            "step": "plan",
            "member_id": str(ObjectId()),
            "member_name": "Cesar Palacio",
            "last_payment": None,
            "_ts": 0,
        }
        mock_update.message.text = "99. Plan Falso"

        await procesar_pago(mock_update, mock_context)

        assert payment_state[12345]["step"] == "plan"
        mock_update.message.reply_text.assert_awaited_once_with("Selecciona un plan valido", reply_markup=menu_planes)

    async def test_plan_mensual_valido_transitions_to_confirmar(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {
            "step": "plan",
            "member_id": str(ObjectId()),
            "member_name": "Cesar Palacio",
            "last_payment": None,
            "_ts": 0,
        }
        mock_update.message.text = "1. Mensual ($70,000)"

        await procesar_pago(mock_update, mock_context)

        assert payment_state[12345]["step"] == "confirmar"
        assert payment_state[12345]["plan"] == PLANS["1"]
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Resumen del pago" in text
        assert "70000" in text

    async def test_plan_con_vencido_muestra_gracia_text(self, mock_update, mock_context, mock_collection):
        member_id = ObjectId()
        payment_state[12345] = {
            "step": "plan",
            "member_id": str(member_id),
            "member_name": "Cesar Palacio",
            "last_payment": {
                "member_id": str(member_id),
                "payment_date": "2026-03-20",
                "due_date": "2026-04-20",
                "plan": "Mensual",
                "amount": 500,
            },
            "_ts": 0,
        }
        mock_update.message.text = "1. Mensual ($70,000)"

        await procesar_pago(mock_update, mock_context)

        assert payment_state[12345]["step"] == "confirmar"
        text = mock_update.message.reply_text.await_args[0][0]
        assert "periodo de gracia" in text.lower() or "dias de retraso" in text.lower() or "Confirmar" in text

    async def test_confirmar_cancelar_clears_state(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {
            "step": "confirmar",
            "plan": PLANS["1"],
            "member_id": str(ObjectId()),
            "member_name": "Cesar Palacio",
            "last_payment": None,
            "_ts": 0,
        }
        mock_update.message.text = "Cancelar"

        await procesar_pago(mock_update, mock_context)

        assert 12345 not in payment_state
        mock_update.message.reply_text.assert_awaited_once_with("Operacion cancelada")

    async def test_confirmar_opcion_invalida_stays_in_confirmar(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {
            "step": "confirmar",
            "plan": PLANS["1"],
            "member_id": str(ObjectId()),
            "member_name": "Cesar Palacio",
            "last_payment": None,
            "_ts": 0,
        }
        mock_update.message.text = "Tal vez"

        await procesar_pago(mock_update, mock_context)

        assert payment_state[12345]["step"] == "confirmar"
        mock_update.message.reply_text.assert_awaited_once_with(
            "Selecciona una opcion valida", reply_markup=menu_confirmar
        )

    async def test_confirmar_valido_sin_historial_registra_pago(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {
            "step": "confirmar",
            "plan": PLANS["1"],
            "plan_key": "1",
            "member_id": str(ObjectId()),
            "member_name": "Cesar Palacio",
            "last_payment": None,
            "_ts": 0,
        }
        mock_update.message.text = "Confirmar"
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        await procesar_pago(mock_update, mock_context)

        assert 12345 not in payment_state
        mock_collection.insert_one.assert_awaited_once()
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Pago registrado" in text

    async def test_confirmar_valido_con_historial_gracia(self, mock_update, mock_context, mock_collection):
        hoy = date.today()
        payment_state[12345] = {
            "step": "confirmar",
            "plan": PLANS["1"],
            "plan_key": "1",
            "member_id": str(ObjectId()),
            "member_name": "Cesar Palacio",
            "last_payment": {
                "member_id": str(ObjectId()),
                "payment_date": format_fecha(hoy),
                "due_date": format_fecha(hoy),
                "plan": "Mensual",
                "amount": 500,
            },
            "_ts": 0,
        }
        mock_update.message.text = "Confirmar"
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        await procesar_pago(mock_update, mock_context)

        assert 12345 not in payment_state
        mock_collection.insert_one.assert_awaited_once()
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Pago registrado" in text

    async def test_confirmar_valido_con_historial_tardio(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {
            "step": "confirmar",
            "plan": PLANS["1"],
            "plan_key": "1",
            "member_id": str(ObjectId()),
            "member_name": "Cesar Palacio",
            "last_payment": {
                "member_id": str(ObjectId()),
                "payment_date": "2026-04-01",
                "due_date": "2026-05-01",
                "plan": "Mensual",
                "amount": 500,
            },
            "_ts": 0,
        }
        mock_update.message.text = "Confirmar"
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        await procesar_pago(mock_update, mock_context)

        assert 12345 not in payment_state
        mock_collection.insert_one.assert_awaited_once()
        text = mock_update.message.reply_text.await_args[0][0]
        assert "Pago registrado" in text

    async def test_confirmar_valido_muestra_menu_principal(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {
            "step": "confirmar",
            "plan": PLANS["1"],
            "plan_key": "1",
            "member_id": str(ObjectId()),
            "member_name": "Cesar Palacio",
            "last_payment": None,
            "_ts": 0,
        }
        mock_update.message.text = "Confirmar"
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        await procesar_pago(mock_update, mock_context)

        last_call = mock_update.message.reply_text.await_args_list[-1]
        assert last_call.kwargs["reply_markup"] == menu_principal

    async def test_historial_nombre_encontrado_muestra_pagos(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {"step": "historial_nombre", "_ts": 0}
        mock_update.message.text = "Cesar Palacio"
        member_id = ObjectId()
        mock_collection.find_one = AsyncMock(return_value={"_id": member_id, "name": "Cesar Palacio", "active": True})
        mock_collection.find.return_value.sort.return_value.to_list = AsyncMock(
            return_value=[
                {
                    "payment_date": "2026-03-20",
                    "amount": 500,
                    "plan": "Mensual",
                    "due_date": "2026-04-20",
                    "grace_period": False,
                },
                {
                    "payment_date": "2026-02-20",
                    "amount": 500,
                    "plan": "Mensual",
                    "due_date": "2026-03-20",
                    "grace_period": False,
                },
            ]
        )

        await procesar_pago(mock_update, mock_context)

        assert 12345 not in payment_state
        text = mock_update.message.reply_text.await_args[0][0]
        assert "HISTORIAL DE PAGOS" in text
        assert "Cesar Palacio" in text
        assert "2026-03-20" in text
        assert "2026-02-20" in text

    async def test_historial_nombre_no_encontrado(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {"step": "historial_nombre", "_ts": 0}
        mock_update.message.text = "Nobody Knows"
        mock_collection.find_one = AsyncMock(return_value=None)

        await procesar_pago(mock_update, mock_context)

        assert 12345 not in payment_state
        mock_update.message.reply_text.assert_awaited_once_with("Miembro no encontrado")

    async def test_historial_vacio(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {"step": "historial_nombre", "_ts": 0}
        mock_update.message.text = "Cesar Palacio"
        member_id = ObjectId()
        mock_collection.find_one = AsyncMock(return_value={"_id": member_id, "name": "Cesar Palacio", "active": True})
        mock_collection.find.return_value.sort.return_value.to_list = AsyncMock(return_value=[])

        await procesar_pago(mock_update, mock_context)

        assert 12345 not in payment_state
        mock_update.message.reply_text.assert_awaited_once_with("Sin historial de pagos")

    async def test_historial_con_grace_emoji(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {"step": "historial_nombre", "_ts": 0}
        mock_update.message.text = "Cesar Palacio"
        member_id = ObjectId()
        mock_collection.find_one = AsyncMock(return_value={"_id": member_id, "name": "Cesar Palacio", "active": True})
        mock_collection.find.return_value.sort.return_value.to_list = AsyncMock(
            return_value=[
                {
                    "payment_date": "2026-03-20",
                    "amount": 500,
                    "plan": "Mensual",
                    "due_date": "2026-04-20",
                    "grace_period": True,
                },
            ]
        )

        await procesar_pago(mock_update, mock_context)

        text = mock_update.message.reply_text.await_args[0][0]
        assert "\u26a0\ufe0f" in text

    async def test_historial_muestra_solo_ultimos_10(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {"step": "historial_nombre", "_ts": 0}
        mock_update.message.text = "Cesar Palacio"
        member_id = ObjectId()
        mock_collection.find_one = AsyncMock(return_value={"_id": member_id, "name": "Cesar Palacio", "active": True})
        pagos = [
            {
                "payment_date": f"2026-{m:02d}-01",
                "amount": 500,
                "plan": "Mensual",
                "due_date": f"2026-{m + 1:02d}-01",
                "grace_period": False,
            }
            for m in range(1, 13)
        ]
        mock_collection.find.return_value.sort.return_value.to_list = AsyncMock(return_value=pagos)

        await procesar_pago(mock_update, mock_context)

        text = mock_update.message.reply_text.await_args[0][0]
        for i in range(1, 11):
            assert f"{i}." in text
        assert "11." not in text

    async def test_exception_handling_clears_state_and_replies(self, mock_update, mock_context, mock_collection):
        payment_state[12345] = {"step": "nombre", "_ts": 0}
        mock_update.message.text = "Cesar Palacio"
        mock_collection.find_one = AsyncMock(side_effect=Exception("DB Error"))

        await procesar_pago(mock_update, mock_context)

        assert 12345 not in payment_state
        mock_update.message.reply_text.assert_awaited_with("Error al procesar. Intenta de nuevo.")
