from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, time, timedelta

from database import get_collection
from keyboards import (
    menu_principal,
    menu_miembros,
    menu_pagos,
    menu_reportes,
    menu_estadisticas,
    menu_exportar,
    menu_admin,
    menu_principal_admin,
)

from . import members, payments, reports, stats, admins, export


def is_within_schedule() -> bool:
    """Check if current time is within 5 AM - 9:30 PM Colombia (UTC-5)"""
    utc_now = datetime.utcnow()
    colombia_offset = timedelta(hours=-5)
    colombia_time = utc_now + colombia_offset
    
    now = colombia_time.time()
    start_time = time(5, 0)    # 5:00 AM Colombia
    end_time = time(21, 30)    # 9:30 PM Colombia
    return start_time <= now <= end_time


async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_within_schedule():
        await update.message.reply_text(
            "🌙 El bot esta Disponible de 5:00 AM a 9:00 PM\n\n"
            "Vuelve a escribir en ese horario."
        )
        return
    
    texto = update.message.text
    user_id = update.effective_user.id
    
    admins_col = get_collection("admins")
    admin = admins_col.find_one({"telegram_id": user_id})
    
    if not admin:
        return
    
    is_super_admin = admin["role"] == "super_admin"
    
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
    
    elif texto == "⚙️ Admin":
        if is_super_admin:
            await admins.menu_admins(update, context)
        else:
            await update.message.reply_text("Solo Super Admin")
    
    elif texto == "👥 Miembros activos":
        await stats.miembros_activos(update, context)
    
    elif texto == "💰 Ingresos del mes":
        await stats.ingresos_mes(update, context)
    
    elif texto == "📅 Vencimientos":
        await stats.vencimientos_stats(update, context)
    
    elif texto == "⬅️ Volver":
        if is_super_admin:
            await update.message.reply_text("🏋️ Menu principal", reply_markup=menu_principal)
        else:
            await update.message.reply_text("🏋️ Menu principal", reply_markup=menu_principal_admin)
    
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
    
    elif texto == "➕ Agregar admin":
        await admins.agregar_admin_start(update, context)
    
    elif texto == "👥 Lista admins":
        await admins.lista_admins(update, context)
    
    elif texto == "🗑 Quitar admin":
        await admins.quitar_admin_start(update, context)
    
    elif texto == "🔄 Cambiar rol":
        await admins.cambiar_rol_start(update, context)
    
    else:
        await members.procesar_miembro(update, context)
        await payments.procesar_pago(update, context)
        await admins.procesar_admin(update, context)
