from __future__ import annotations

import time as time_module
from collections import defaultdict

from telegram import Update
from telegram.ext import ContextTypes

from database import get_collection
from keyboards import (
    menu_principal,
)
from utils import es_admin_grupo

from . import admins, export, members, payments, reports, stats

RATE_LIMIT: defaultdict[int, list[float]] = defaultdict(list)
RATE_MAX = 10
RATE_WINDOW = 5


async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id if update.effective_user else 0
    now = time_module.time()
    window_start = now - RATE_WINDOW
    RATE_LIMIT[user_id] = [t for t in RATE_LIMIT[user_id] if t > window_start]
    if len(RATE_LIMIT[user_id]) >= RATE_MAX:
        return
    RATE_LIMIT[user_id].append(now)

    if not update.message or not update.message.text:
        return
    texto = update.message.text
    chat = update.effective_chat

    if chat and chat.type != "private" and not await es_admin_grupo(update, context):
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
    elif texto == "📄 TXT resumen":
        await export.exportar_txt_resumen(update, context)
    elif texto == "⚙️ Administración":
        if user_id:
            admins_col = get_collection("admins")
            admin = admins_col.find_one({"telegram_id": user_id})
            if admin and admin.get("role") == "super_admin":
                await admins.menu_admins(update, context)
            else:
                await update.message.reply_text("Solo Super Admin puede acceder")
    else:
        await members.procesar_miembro(update, context)
        await payments.procesar_pago(update, context)
