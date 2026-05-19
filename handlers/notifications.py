from __future__ import annotations

import logging

from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import GROUP_ID
from services import get_notification_service

logger = logging.getLogger(__name__)


async def notificacion_5am(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not GROUP_ID:
        logger.warning("GROUP_ID no configurado")
        return

    svc = await get_notification_service()
    data = await svc.generate_daily_notification()
    texto = data.format_message()

    try:
        await context.bot.send_message(chat_id=GROUP_ID, text=texto)
        logger.info("Notificacion 5AM enviada al grupo")
    except TelegramError as e:
        logger.error(f"Error de Telegram enviando notificacion: {e}")
    except Exception as e:
        logger.exception(f"Error inesperado enviando notificacion: {e}")
