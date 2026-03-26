import logging
import os
from datetime import time
import signal

os.makedirs("logs", exist_ok=True)
os.makedirs("reports", exist_ok=True)

PORT = int(os.environ.get("PORT", 8000))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from config import TOKEN, ADMIN_ID
from database import init_collections
from handlers import (
    start,
    help_command,
    botones,
    notificacion_5am,
)

logging.basicConfig(
    filename="logs/bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def setup_database() -> None:
    try:
        init_collections()
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        raise


async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type != "private":
        try:
            member = await context.bot.get_chat_member(chat.id, user.id)
            if member.status not in ["creator", "administrator"]:
                await update.message.reply_text("No autorizado")
                return
        except Exception:
            await update.message.reply_text("No autorizado")
            return
    else:
        await update.message.reply_text("Usa este comando en un grupo")
        return
    
    from handlers import export
    try:
        await export.exportar_excel_miembros(update, context)
        await update.message.reply_text("Backup completado")
    except Exception as e:
        logger.error(f"Error en backup: {e}")
        await update.message.reply_text("Error al crear backup")


def should_run_bot() -> bool:
    """Bot runs 24/7"""
    return True


def main() -> None:
    logger.info("Iniciando bot...")
    
    setup_database()
    
    app = Application.builder().token(TOKEN).build()
    
    job_queue = app.job_queue
    
    # Notificacion 5 AM Colombia = 10:00 UTC
    job_queue.run_daily(
        notificacion_5am,
        time=time(hour=10, minute=0)
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("backup", backup_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, botones))
    
    logger.info("Bot iniciado")
    print("Bot corriendo...", flush=True)
    
    app.run_polling(poll_interval=3, drop_pending_updates=True)


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    os.makedirs("backup", exist_ok=True)
    main()
