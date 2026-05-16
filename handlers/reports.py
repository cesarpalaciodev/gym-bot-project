from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import EXCEL_FILE
from keyboards import menu_reportes
from services import get_report_service

logger = logging.getLogger(__name__)


async def menu_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        await update.message.reply_text("Menu reportes", reply_markup=menu_reportes)
    except Exception as e:
        logger.error(f"Error en menu_reports: {e}")


async def deudores(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        svc = await get_report_service()
        texto = await svc.get_overdue_text()
        await update.message.reply_text(texto)
    except Exception as e:
        logger.error(f"Error en deudores: {e}")
        await update.message.reply_text("Error al generar reporte de deudores")


async def excel_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        svc = await get_report_service()
        filepath = await svc.generate_excel(EXCEL_FILE)
        with open(filepath, "rb") as f:
            await update.message.reply_document(f, filename="reporte_miembros.xlsx")
    except (OSError, ValueError) as e:
        logger.error(f"Error generando Excel: {e}")
        await update.message.reply_text("Error al generar reporte Excel")
    except Exception as e:
        logger.error(f"Error inesperado en excel_reporte: {e}")
        await update.message.reply_text("Error al generar reporte")
