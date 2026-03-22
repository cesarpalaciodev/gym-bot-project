from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_collection
from keyboards import menu_principal, menu_principal_admin


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    admins = get_collection("admins")
    admin = admins.find_one({"telegram_id": user_id})
    
    if not admin:
        await update.message.reply_text("Acceso no autorizado")
        return
    
    if admin["role"] == "super_admin":
        await update.message.reply_text(
            "🏋️ Sistema del gimnasio\n\nModo: Super Admin",
            reply_markup=menu_principal,
        )
    else:
        await update.message.reply_text(
            "🏋️ Sistema del gimnasio",
            reply_markup=menu_principal_admin,
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
