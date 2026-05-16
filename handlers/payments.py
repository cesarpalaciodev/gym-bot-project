from __future__ import annotations

import logging
import time
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from config import PLANS
from keyboards import menu_confirmar, menu_pagos, menu_planes, menu_principal
from services import get_payment_service

logger = logging.getLogger(__name__)

payment_state: dict[int, Any] = {}
STATE_TIMEOUT = 600


def _clean_stale_states() -> None:
    now = time.time()
    stale = [
        uid
        for uid, state in list(payment_state.items())
        if isinstance(state, dict) and now - state.get("_ts", 0) > STATE_TIMEOUT
    ]
    for uid in stale:
        del payment_state[uid]


def _set_state(user_id: int, value: Any) -> None:
    if isinstance(value, dict):
        value["_ts"] = time.time()
    payment_state[user_id] = value


def _del_state(user_id: int) -> None:
    payment_state.pop(user_id, None)


async def menu_payments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text("Menu pagos", reply_markup=menu_pagos)


async def registrar_pago_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    _clean_stale_states()
    _set_state(user_id, {"step": "nombre"})
    await update.message.reply_text("Ingresa el nombre del miembro")


async def historial_pagos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    _clean_stale_states()
    _set_state(user_id, {"step": "historial_nombre"})
    await update.message.reply_text("Ingresa el nombre del miembro para ver su historial")


async def procesar_pago(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    texto = update.message.text
    if not texto:
        return

    if user_id not in payment_state:
        return

    state = payment_state[user_id]
    svc = await get_payment_service()

    try:
        if state["step"] == "nombre":
            member = await svc.find_member(texto)

            if not member:
                await update.message.reply_text("Miembro no encontrado")
                _del_state(user_id)
                return

            last_payment = await svc.get_last_payment(str(member["_id"]))

            _set_state(
                user_id,
                {
                    "step": "plan",
                    "member_id": str(member["_id"]),
                    "member_name": texto,
                    "last_payment": last_payment,
                },
            )

            await update.message.reply_text(f"Miembro: {texto}\n\nSelecciona el plan:", reply_markup=menu_planes)

        elif state["step"] == "plan":
            if texto == "Cancelar":
                _del_state(user_id)
                await update.message.reply_text("Operacion cancelada")
                return

            plan_key = texto.split(".")[0]
            if plan_key not in PLANS:
                await update.message.reply_text("Selecciona un plan valido", reply_markup=menu_planes)
                return

            plan = PLANS[plan_key]
            payment_state[user_id]["plan"] = plan
            payment_state[user_id]["plan_key"] = plan_key
            payment_state[user_id]["step"] = "confirmar"

            grace_text = await svc.get_grace_text(state["last_payment"])

            await update.message.reply_text(
                f"Resumen del pago:\n\n"
                f"Miembro: {state['member_name']}\n"
                f"Plan: {plan['name']}\n"
                f"Monto: ${plan['price']}\n"
                f"Duracion: {plan['months']} mes(es){grace_text}\n\n"
                f"Confirmar?",
                reply_markup=menu_confirmar,
            )

        elif state["step"] == "confirmar":
            if texto == "Cancelar":
                _del_state(user_id)
                await update.message.reply_text("Operacion cancelada")
                return

            if texto != "Confirmar":
                await update.message.reply_text("Selecciona una opcion valida", reply_markup=menu_confirmar)
                return

            result = await svc.register_payment(
                state["member_id"], state["member_name"], state["plan_key"], state.get("last_payment")
            )

            if not result:
                await update.message.reply_text("Error al registrar pago. Plan invalido.")
                _del_state(user_id)
                return

            await update.message.reply_text(
                f"Pago registrado!\n\n"
                f"Miembro: {state['member_name']}\n"
                f"Monto: ${result['price']}\n"
                f"Pago: {result['payment_date']}\n"
                f"Vence: {result['due_date']}\n"
                f"{'Periodo de gracia' if result['grace_period'] else ''}",
                reply_markup=menu_principal,
            )

            _del_state(user_id)

        elif state["step"] == "historial_nombre":
            member = await svc.find_member(texto)

            if not member:
                await update.message.reply_text("Miembro no encontrado")
                _del_state(user_id)
                return

            all_payments = await svc.get_history(str(member["_id"]), limit=10)

            if not all_payments:
                await update.message.reply_text("Sin historial de pagos")
                _del_state(user_id)
                return

            msg = await svc.format_history(texto, all_payments)
            await update.message.reply_text(msg)
            _del_state(user_id)

    except Exception as e:
        logger.error(f"Error procesando pago: {e}")
        await update.message.reply_text("Error al procesar. Intenta de nuevo.")
        if user_id in payment_state:
            _del_state(user_id)


def get_payment_state() -> dict[int, Any]:
    return payment_state
