from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from keyboards import menu_exportar
from services import get_export_service

logger = logging.getLogger(__name__)


async def menu_exports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        await update.message.reply_text("\U0001f4be Menu exportar", reply_markup=menu_exportar)
    except Exception as e:
        logger.error(f"Error en menu_exports: {e}")


async def exportar_excel_miembros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        svc = await get_export_service()
        filepath = await svc.export_members_to_excel()

        with open(filepath, "rb") as f:
            await update.message.reply_document(f, filename="miembros_export.xlsx")
    except (OSError, ValueError) as e:
        logger.error(f"Error exportando miembros Excel: {e}")
        await update.message.reply_text("Error al generar archivo Excel de miembros")
    except Exception as e:
        logger.error(f"Error inesperado en exportar_excel_miembros: {e}")
        await update.message.reply_text("Error al exportar miembros")


async def exportar_excel_pagos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        svc = await get_export_service()
        filepath = await svc.export_payments_to_excel()

        with open(filepath, "rb") as f:
            await update.message.reply_document(f, filename="pagos_export.xlsx")
    except (OSError, ValueError) as e:
        logger.error(f"Error exportando pagos Excel: {e}")
        await update.message.reply_text("Error al generar archivo Excel de pagos")
    except Exception as e:
        logger.error(f"Error inesperado en exportar_excel_pagos: {e}")
        await update.message.reply_text("Error al exportar pagos")


async def exportar_txt_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        svc = await get_export_service()
        filepath = await svc.generate_txt_summary()

        with open(filepath, "rb") as f:
            await update.message.reply_document(f, filename="resumen.txt")
    except (OSError, ValueError) as e:
        logger.error(f"Error exportando TXT resumen: {e}")
        await update.message.reply_text("Error al generar archivo TXT de resumen")
    except Exception as e:
        logger.error(f"Error inesperado en exportar_txt_resumen: {e}")
        await update.message.reply_text("Error al exportar resumen")


async def exportar_csv_miembros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        svc = await get_export_service()
        filepath = await svc.export_members_to_csv()

        with open(filepath, "rb") as f:
            await update.message.reply_document(f, filename="miembros.csv")
    except (OSError, ValueError) as e:
        logger.error(f"Error exportando CSV miembros: {e}")
        await update.message.reply_text("Error al generar archivo CSV de miembros")
    except Exception as e:
        logger.error(f"Error inesperado en exportar_csv_miembros: {e}")
        await update.message.reply_text("Error al exportar miembros CSV")
