from __future__ import annotations

import logging
import time
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from keyboards import menu_miembros
from services import get_member_service

logger = logging.getLogger(__name__)

user_state: dict[int, Any] = {}
STATE_TIMEOUT = 600


def _clean_stale_states() -> None:
    now = time.time()
    stale = [
        uid
        for uid, state in list(user_state.items())
        if isinstance(state, dict) and now - state.get("_ts", 0) > STATE_TIMEOUT
    ]
    for uid in stale:
        del user_state[uid]


def _set_state(user_id: int, value: Any) -> None:
    if isinstance(value, dict):
        value["_ts"] = time.time()
    user_state[user_id] = value


def _del_state(user_id: int) -> None:
    user_state.pop(user_id, None)


async def menu_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text("Menu miembros", reply_markup=menu_miembros)


async def agregar_miembro_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    _clean_stale_states()
    _set_state(user_id, "agregar_miembro")
    await update.message.reply_text(
        "Ingresa: Nombre, Telefono, Fecha\nEjemplo:\nCesar Palacio Garcia 3101234567 2026-03-20"
    )


async def agregar_varios_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    _clean_stale_states()
    _set_state(user_id, "agregar_varios")
    await update.message.reply_text(
        "Ingresa uno por linea:\n"
        "Nombre Telefono YYYY-MM-DD\n"
        "Cesar Palacio Garcia 3101234567 2026-03-20\n"
        "Maria Lopez Hernandez 3158765432 2026-03-21"
    )


async def buscar_miembro_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    _clean_stale_states()
    _set_state(user_id, "buscar_miembro")
    await update.message.reply_text("Ingresa el nombre a buscar")


async def eliminar_miembro_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    _clean_stale_states()
    _set_state(user_id, "eliminar_miembro")
    await update.message.reply_text("Ingresa el nombre completo del miembro a eliminar")


async def eliminar_varios_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    _clean_stale_states()
    _set_state(user_id, "eliminar_varios")
    await update.message.reply_text("Ingresa los nombres uno por linea:\nCesar Palacio Garcia\nMaria Lopez Hernandez")


async def lista_miembros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    svc = await get_member_service()
    all_members = await svc.list_members_with_payments()

    if not all_members:
        await update.message.reply_text("No hay miembros registrados")
        return

    texto = "MIEMBROS REGISTRADOS:\n\n"

    for member, last_payment in all_members:
        texto += f"\u2022 {member['name']}"
        if member.get("phone"):
            texto += f" {member['phone']}"
        if last_payment:
            texto += f"\n  Ingreso: {last_payment['payment_date']}\n"
            texto += f"  Vence: {last_payment['due_date']}\n\n"
        else:
            texto += "\n  Sin pagos registrados\n\n"

    await update.message.reply_text(texto)


async def procesar_miembro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    texto = update.message.text
    if not texto:
        return

    if user_id not in user_state:
        return

    estado = user_state[user_id]
    svc = await get_member_service()

    try:
        if estado == "agregar_miembro":
            partes = texto.rsplit(" ", 2)
            if len(partes) != 3:
                await update.message.reply_text("Formato incorrecto. Usa: Nombre Telefono YYYY-MM-DD")
                _del_state(user_id)
                return
            ok, msg = await svc.add_member(*partes)
            await update.message.reply_text(msg)
            _del_state(user_id)

        elif estado == "agregar_varios":
            agregados, errores = await svc.bulk_add(texto.split("\n"))
            await update.message.reply_text(f"Agregados: {agregados}\nErrores: {errores}")
            _del_state(user_id)

        elif estado == "buscar_miembro":
            data = await svc.get_member_with_last_payment(texto)
            if not data:
                await update.message.reply_text("Miembro no encontrado")
            else:
                member = data["member"]
                last_payment = data["last_payment"]
                msg = f"{member['name']}\n"
                if member.get("phone"):
                    msg += f" {member['phone']}\n"
                if last_payment:
                    msg += f" Ultimo pago: {last_payment['payment_date']}\n"
                    msg += f" Vence: {last_payment['due_date']}\n"
                    msg += f" Plan: {last_payment['plan']}"
                await update.message.reply_text(msg)
            _del_state(user_id)

        elif estado == "eliminar_miembro":
            ok, msg = await svc.delete_member(texto)
            await update.message.reply_text(msg)
            _del_state(user_id)

        elif estado == "eliminar_varios":
            nombres = [n.strip() for n in texto.split("\n") if n.strip()]
            eliminados, no_encontrados = await svc.bulk_delete(nombres)
            await update.message.reply_text(f"Eliminados: {eliminados}\nNo encontrados: {no_encontrados}")
            _del_state(user_id)

    except Exception as e:
        logger.error(f"Error procesando miembro: {e}")
        await update.message.reply_text("Error al procesar. Intenta de nuevo.")
        _del_state(user_id)


def get_user_state() -> dict[int, Any]:
    return user_state
