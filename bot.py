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
from models import Admin
from database import get_collection
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
        admins = get_collection("admins")
        
        if not admins.find_one({"telegram_id": ADMIN_ID}):
            super_admin = Admin(
                telegram_id=ADMIN_ID,
                name="Super Admin",
                role="super_admin"
            )
            admins.insert_one(super_admin.to_dict())
            logger.info("Super Admin creado")
        else:
            logger.info("Super Admin ya existe")
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        raise


async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("No autorizado")
        return
    
    from handlers import export
    try:
        await export.exportar_excel_miembros(update, context)
        await update.message.reply_text("Backup completado")
    except Exception as e:
        logger.error(f"Error en backup: {e}")
        await update.message.reply_text("Error al crear backup")


def should_run_bot() -> bool:
    """Check if bot should run based on Colombia time (5 AM - 9:30 PM)"""
    from datetime import datetime, time, timedelta
    utc_now = datetime.utcnow()
    colombia_offset = timedelta(hours=-5)
    colombia_time = utc_now + colombia_offset
    
    now = colombia_time.time()
    start_time = time(5, 0)     # 5:00 AM Colombia
    end_time = time(21, 30)     # 9:30 PM Colombia
    return start_time <= now <= end_time


def stop_bot(context: ContextTypes.DEFAULT_TYPE = None):
    """Stop the bot at scheduled time"""
    import sys
    logger.info("Bot deteniendo por horario (9:30 PM Colombia)")
    print("Bot se detiene - fuera de horario", flush=True)
    sys.exit(0)


def main() -> None:
    if not should_run_bot():
        logger.info("Fuera de horario - bot no iniciara")
        print("Fuera de horario - bot no iniciara", flush=True)
        return
    
    logger.info("Iniciando bot...")
    
    setup_database()
    
    app = Application.builder().token(TOKEN).build()
    
    job_queue = app.job_queue
    
    # Notificacion 5 AM Colombia = 10:00 UTC
    job_queue.run_daily(
        notificacion_5am,
        time=time(hour=10, minute=0)
    )
    
    # Detener bot a las 9:30 PM Colombia = 2:30 UTC
    job_queue.run_daily(
        stop_bot,
        time=time(hour=2, minute=30)
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
