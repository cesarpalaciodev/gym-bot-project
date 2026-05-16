from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from database import get_collection

ALL_ROLES = {"super_admin", "admin", "viewer"}
ROLE_HIERARCHY = {"super_admin": 3, "admin": 2, "viewer": 1}


def require_role(min_role: str) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
    def decorator(func: Callable[..., Awaitable[None]]) -> Callable[..., Awaitable[None]]:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> None:
            user = update.effective_user
            if not user:
                return await func(update, context, *args, **kwargs)

            admins = await get_collection("admins")
            admin = await admins.find_one({"telegram_id": user.id})
            if not admin:
                if update.message:
                    await update.message.reply_text("No autorizado. Solo administradores.")
                return None

            user_level = ROLE_HIERARCHY.get(admin.get("role", ""), 0)
            required_level = ROLE_HIERARCHY.get(min_role, 0)
            if user_level < required_level:
                if update.message:
                    await update.message.reply_text("No tienes permisos suficientes.")
                return None

            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator


async def es_admin_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return False

    if chat.type == "private":
        return True

    from telegram.error import TelegramError

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in {"creator", "administrator"}
    except TelegramError:
        return False
