from __future__ import annotations

import logging
import os
from datetime import time

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config import TOKEN
from database import init_collections
from handlers import (
    botones,
    getgroupid,
    help_command,
    notificacion_5am,
    start,
)

logging.basicConfig(
    filename="logs/bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def setup_database() -> None:
    try:
        await init_collections()
    except (ConnectionError, OSError, ValueError) as e:
        logger.error(f"Error inicializando base de datos: {e}")
        raise


async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or not update.message:
        return

    if chat.type == "private":
        await update.message.reply_text("Usa este comando en un grupo")
        return

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in {"creator", "administrator"}:
            await update.message.reply_text("No autorizado")
            return
    except TelegramError:
        await update.message.reply_text("No autorizado")
        return

    from handlers import export

    try:
        await export.exportar_excel_miembros(update, context)
        await update.message.reply_text("Backup completado")
    except (OSError, ValueError) as e:
        logger.error(f"Error en backup: {e}")
        await update.message.reply_text("Error al crear backup")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id if update.effective_user else 0
    context.user_data.clear()
    from handlers.admins import _del_state as del_admin_state
    from handlers.members import _del_state as del_member_state
    from handlers.payments import _del_state as del_payment_state

    del_member_state(user_id)
    del_payment_state(user_id)
    del_admin_state(user_id)
    if update.message:
        await update.message.reply_text("✅ Operación cancelada")


def main() -> None:
    logger.info("Iniciando bot...")

    import asyncio

    asyncio.run(setup_database())

    app = Application.builder().token(TOKEN).build()

    job_queue = app.job_queue
    if job_queue:
        job_queue.run_daily(
            notificacion_5am,
            time=time(hour=10, minute=0),
        )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("getgroupid", getgroupid))
    app.add_handler(CommandHandler("backup", backup_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, botones))

    logger.info("Bot iniciado")
    print("Bot corriendo...", flush=True)

    app.run_polling(
        poll_interval=3,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    main()
