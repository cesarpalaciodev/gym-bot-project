from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from keyboards import (
    menu_principal,
    menu_miembros,
    menu_pagos,
    menu_reportes,
    menu_estadisticas,
    menu_exportar,
)

from . import members, payments, reports, stats, export


async def verificar_admin_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == "private":
        return True
    
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["creator", "administrator"]
    except Exception:
        return True


async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    texto = update.message.text
    user_id = update.effective_user.id
    
    chat = update.effective_chat
    
    if chat.type != "private":
        if not await verificar_admin_grupo(update, context):
            return
    
    if texto == "👥 Miembros":
        await members.menu_members(update, context)
    
    elif texto == "💰 Pagos":
        await payments.menu_payments(update, context)
    
    elif texto == "📊 Reportes":
        await reports.menu_reports(update, context)
    
    elif texto == "📈 Estadísticas":
        await stats.menu_stats(update, context)
    
    elif texto == "💾 Exportar":
        await export.menu_exports(update, context)
    
    elif texto == "👥 Miembros activos":
        await stats.miembros_activos(update, context)
    
    elif texto == "💰 Ingresos del mes":
        await stats.ingresos_mes(update, context)
    
    elif texto == "📅 Vencimientos":
        await stats.vencimientos_stats(update, context)
    
    elif texto == "⬅️ Volver":
        await update.message.reply_text("🏋️ Menu principal", reply_markup=menu_principal)
    
    elif texto == "➕ Agregar miembro":
        await members.agregar_miembro_start(update, context)
    
    elif texto == "👥 Agregar varios":
        await members.agregar_varios_start(update, context)
    
    elif texto == "🔍 Buscar miembro":
        await members.buscar_miembro_start(update, context)
    
    elif texto == "📋 Lista miembros":
        await members.lista_miembros(update, context)
    
    elif texto == "🗑 Eliminar miembro":
        await members.eliminar_miembro_start(update, context)
    
    elif texto == "🗑 Eliminar varios":
        await members.eliminar_varios_start(update, context)
    
    elif texto == "💰 Registrar pago":
        await payments.registrar_pago_start(update, context)
    
    elif texto == "📜 Historial":
        await payments.historial_pagos(update, context)
    
    elif texto == "⚠️ Deudores":
        await reports.deudores(update, context)
    
    elif texto == "📊 Excel":
        await reports.excel_reporte(update, context)
    
    elif texto == "📊 Excel miembros":
        await export.exportar_excel_miembros(update, context)
    
    elif texto == "📊 Excel pagos":
        await export.exportar_excel_pagos(update, context)
    
    elif texto == "📄 PDF resumen":
        await export.exportar_pdf_resumen(update, context)
    
    else:
        await members.procesar_miembro(update, context)
        await payments.procesar_pago(update, context)
