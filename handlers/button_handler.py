from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from keyboards import (
    menu_principal,
)
from services import get_admin_service
from utils import check_rate_limit, es_admin_grupo

from . import admins, export, members, payments, reports, stats

logger = logging.getLogger(__name__)


async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    user_id = update.effective_user.id if update.effective_user else 0
    if not await check_rate_limit(user_id):
        await update.message.reply_text("Demasiadas solicitudes. Espera unos segundos.")
        return

    texto = update.message.text
    if not texto:
        return
    chat = update.effective_chat

    if chat and chat.type != "private" and not await es_admin_grupo(update, context):
        return

    try:
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
        elif texto == "📄 TXT resumen":
            await export.exportar_txt_resumen(update, context)
        elif texto == "⚙️ Administración":
            if user_id:
                svc = await get_admin_service()
                if await svc.is_super_admin(user_id):
                    await admins.menu_admins(update, context)
                else:
                    await update.message.reply_text("Solo Super Admin puede acceder")
        else:
            await members.procesar_miembro(update, context)
            await payments.procesar_pago(update, context)
    except Exception as e:
        logger.error(f"Error en botones (texto={texto!r}): {e}")
        if update.message:
            await update.message.reply_text("Ocurrio un error. Intenta de nuevo.")
