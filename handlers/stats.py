from __future__ import annotations

import logging
from datetime import date

from telegram import Update
from telegram.ext import ContextTypes

from keyboards import menu_estadisticas
from services import get_stats_service

logger = logging.getLogger(__name__)


async def menu_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        await update.message.reply_text("\U0001f4c8 Menu estadisticas", reply_markup=menu_estadisticas)
    except Exception as e:
        logger.error(f"Error en menu_stats: {e}")


async def miembros_activos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        svc = await get_stats_service()
        stats = await svc.get_member_stats()

        msg = "ESTADISTICAS DE MIEMBROS\n\n"
        msg += f"Total: {stats.total}\n"
        msg += f"Activos: {stats.activos}\n"
        msg += f"En gracia: {stats.en_gracia}\n"
        msg += f"Vencidos: {stats.vencidos}\n"

        if stats.total > 0:
            msg += f"\nPorcentaje de renovacion: {stats.renewal_rate:.1f}%"

        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error en miembros_activos: {e}")
        await update.message.reply_text("Error al obtener estadisticas de miembros")


async def ingresos_mes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        svc = await get_stats_service()
        stats = await svc.get_income_stats()

        msg = "INGRESOS\n\n"
        msg += f"Este mes: ${stats.monto_actual:,}\n"
        msg += f"Mes pasado: ${stats.monto_pasado:,}\n"
        msg += f"Registros: {stats.registros}\n\n"

        cambio = stats.change_percentage
        if cambio is not None:
            emoji = "\u25b2" if cambio >= 0 else "\u25bc"
            msg += f"{emoji} Cambio: {cambio:+.1f}%"

        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error en ingresos_mes: {e}")
        await update.message.reply_text("Error al obtener estadisticas de ingresos")


async def vencimientos_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        svc = await get_stats_service()
        hoy = date.today()
        stats = await svc.get_expiration_stats(reference_date=hoy)

        msg = "VENCIMIENTOS PROXIMOS\n\n"
        msg += f"Hoy ({hoy.strftime('%Y-%m-%d')}): {len(stats.hoy)}\n"
        for name in stats.hoy:
            msg += f"  \u2022 {name}\n"

        msg += f"\nEsta semana: {len(stats.esta_semana)}\n"
        for name, fecha in stats.esta_semana:
            msg += f"  \u2022 {name} ({fecha})\n"

        msg += f"\nEste mes: {len(stats.este_mes)}\n"
        for name, fecha in stats.este_mes[:5]:
            msg += f"  \u2022 {name} ({fecha})\n"
        if len(stats.este_mes) > 5:
            msg += f"  ... y {len(stats.este_mes) - 5} mas\n"

        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error en vencimientos_stats: {e}")
        await update.message.reply_text("Error al obtener estadisticas de vencimientos")
