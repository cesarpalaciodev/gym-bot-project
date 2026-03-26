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


async def getgroupid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    await update.message.reply_text(f"Group ID: {chat.id}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ayuda = """
🏋️ COMANDOS DISPONIBLES

👥 MIEMBROS
➕ Agregar miembro - Nombre Telefono YYYY-MM-DD
👥 Agregar varios - Registro masivo (uno por linea)
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
👥 Miembros activos - Ver estadisticas
💰 Ingresos del mes - Ver ingresos
📅 Vencimientos - Ver vencimientos

💾 EXPORTAR
📊 Excel miembros - Exportar a Excel

📌 NOTA: El dia de pago es el mismo dia de registro.
Si te registras el 03, pagas el 03 de cada mes.
"""
    await update.message.reply_text(ayuda)
