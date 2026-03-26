from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from keyboards import menu_principal


async def verificar_admin_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == "private":
        return True
    
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["creator", "administrator"]
    except TelegramError:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await verificar_admin_grupo(update, context):
        await update.message.reply_text("No tienes acceso. Debes ser admin del grupo.")
        return
    
    await update.message.reply_text(
        "🏋️ Sistema del gimnasio",
        reply_markup=menu_principal,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ayuda = """
🏋️ COMANDOS DISPONIBLES

👥 MIEMBROS
➕ Agregar miembro - Registrar nuevo miembro
👥 Agregar varios - Registro masivo
🔍 Buscar miembro - Buscar por nombre
📋 Lista miembros - Ver todos
🗑 Eliminar miembro - Eliminar uno
🗑 Eliminar varios - Eliminacion masiva

💰 PAGOS
💰 Registrar pago - Registrar pago
📜 Historial - Ver historial

📊 REPORTES
⚠️ Deudores - Ver morosos
📊 Excel - Generar reporte

📈 ESTADISTICAS
👥 Miembros activos
💰 Ingresos del mes
📅 Vencimientos

💾 EXPORTAR
📊 Excel miembros
📊 Excel pagos
📄 PDF resumen
"""
    await update.message.reply_text(ayuda)
