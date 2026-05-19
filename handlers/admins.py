from __future__ import annotations

import logging
import time
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from keyboards import menu_admin
from services import get_admin_service

logger = logging.getLogger(__name__)

admin_state: dict[int, Any] = {}
STATE_TIMEOUT = 600


def _clean_stale_states() -> None:
    now = time.time()
    stale = [
        uid
        for uid, state in list(admin_state.items())
        if isinstance(state, dict) and now - state.get("_ts", 0) > STATE_TIMEOUT
    ]
    for uid in stale:
        del admin_state[uid]


def _set_state(user_id: int, value: Any) -> None:
    if isinstance(value, dict):
        value["_ts"] = time.time()
    admin_state[user_id] = value


def _del_state(user_id: int) -> None:
    admin_state.pop(user_id, None)


async def menu_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    svc = await get_admin_service()

    if not await svc.is_super_admin(user_id):
        await update.message.reply_text("Solo Super Admin puede acceder")
        return

    await update.message.reply_text("Menu Admin", reply_markup=menu_admin)


async def agregar_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    svc = await get_admin_service()

    if not await svc.is_super_admin(user_id):
        await update.message.reply_text("Solo Super Admin puede acceder")
        return

    _clean_stale_states()
    _set_state(user_id, "agregar_admin")
    await update.message.reply_text(
        "Ingresa el ID de Telegram del nuevo admin:\n\nPara obtener el ID, el usuario puede usar @userinfobot"
    )


async def lista_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    svc = await get_admin_service()

    if not await svc.is_super_admin(user_id):
        await update.message.reply_text("Solo Super Admin puede acceder")
        return

    all_admins = await svc.list_all_admins()

    if not all_admins:
        await update.message.reply_text("No hay admins registrados")
        return

    msg = "ADMINISTRADORES:\n\n"
    for a in all_admins:
        role_emoji = {"super_admin": "", "admin": "", "viewer": ""}.get(a.role, "")
        msg += f"{role_emoji} {a.name}\n"
        msg += f"   ID: {a.telegram_id}\n"
        msg += f"   Rol: {a.role}\n\n"

    await update.message.reply_text(msg)


async def quitar_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    svc = await get_admin_service()

    if not await svc.is_super_admin(user_id):
        await update.message.reply_text("Solo Super Admin puede acceder")
        return

    _clean_stale_states()
    _set_state(user_id, "quitar_admin")
    await update.message.reply_text("Ingresa el ID de Telegram del admin a eliminar")


async def cambiar_rol_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    svc = await get_admin_service()

    if not await svc.is_super_admin(user_id):
        await update.message.reply_text("Solo Super Admin puede acceder")
        return

    _clean_stale_states()
    _set_state(user_id, "cambiar_rol_id")
    await update.message.reply_text("Ingresa el ID de Telegram del admin")


async def procesar_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    texto = update.message.text
    if not texto:
        return

    if user_id not in admin_state:
        return

    svc = await get_admin_service()
    estado = admin_state[user_id]

    try:
        if estado == "agregar_admin":
            telegram_id = await svc.validate_telegram_id(texto)
            if telegram_id is None:
                await update.message.reply_text("ID invalido. Debe ser un numero.")
                _del_state(user_id)
                return

            if await svc.is_admin(telegram_id):
                await update.message.reply_text("Este usuario ya es admin")
                _del_state(user_id)
                return

            _set_state(user_id, {"step": "agregar_nombre", "telegram_id": telegram_id})
            await update.message.reply_text("Ingresa el nombre del nuevo admin:")

        elif isinstance(estado, dict) and estado.get("step") == "agregar_nombre":
            telegram_id = estado["telegram_id"]
            await svc.add_admin(telegram_id, texto, role="admin")

            await update.message.reply_text(f"Admin agregado:\n{texto}\n{telegram_id}\nRol: admin")
            _del_state(user_id)

        elif estado == "quitar_admin":
            telegram_id = await svc.validate_telegram_id(texto)
            if telegram_id is None:
                await update.message.reply_text("ID invalido")
                _del_state(user_id)
                return

            removed = await svc.remove_admin(telegram_id)
            if removed:
                await update.message.reply_text("Admin eliminado")
            else:
                await update.message.reply_text("Admin no encontrado")

            _del_state(user_id)

        elif estado == "cambiar_rol_id":
            telegram_id = await svc.validate_telegram_id(texto)
            if telegram_id is None:
                await update.message.reply_text("ID invalido")
                _del_state(user_id)
                return

            target = await svc.get_admin_display_info(telegram_id)

            if not target:
                await update.message.reply_text("Admin no encontrado")
                _del_state(user_id)
                return

            _set_state(user_id, {"step": "cambiar_rol_rol", "telegram_id": telegram_id, "name": target.name})

            await update.message.reply_text(
                f"Admin: {target.name}\nRol actual: {target.role}\n\nSelecciona nuevo rol:\n1. admin\n2. viewer"
            )

        elif isinstance(estado, dict) and estado.get("step") == "cambiar_rol_rol":
            rol_map = {"1": "admin", "2": "viewer"}

            if texto.strip() not in rol_map:
                await update.message.reply_text("Selecciona 1 o 2")
                return

            nuevo_rol = rol_map[texto.strip()]

            changed = await svc.change_role(estado["telegram_id"], nuevo_rol)
            if changed:
                await update.message.reply_text(f"Rol actualizado:\n{estado['name']}\nNuevo rol: {nuevo_rol}")
            else:
                await update.message.reply_text("Admin no encontrado")

            _del_state(user_id)

    except Exception as e:
        logger.error(f"Error procesando admin: {e}")
        await update.message.reply_text("Error al procesar. Intenta de nuevo.")
        if user_id in admin_state:
            _del_state(user_id)


def get_admin_state() -> dict[int, Any]:
    return admin_state
