from __future__ import annotations

import csv
import logging
import os
from datetime import date, datetime

from telegram import Update
from telegram.ext import ContextTypes

from keyboards import menu_exportar
from services import get_report_service

logger = logging.getLogger(__name__)


async def menu_exports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        await update.message.reply_text("💾 Menu exportar", reply_markup=menu_exportar)
    except Exception as e:
        logger.error(f"Error en menu_exports: {e}")


async def exportar_excel_miembros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        from openpyxl import Workbook

        from config import EXCEL_FILE, REPORTS_DIR

        os.makedirs(REPORTS_DIR, exist_ok=True)

        svc = await get_report_service()

        wb = Workbook()
        ws = wb.active
        ws.title = "Miembros"

        ws.append(["Nombre", "Fecha Registro", "Telefono", "Estado", "Ultimo Pago", "Vence", "Plan"])

        hoy = date.today()

        all_members = await svc.members.find({"active": True}).to_list(None)

        for member in all_members:
            last_payment = await svc.payments.find_one({"member_id": str(member["_id"])}, sort=[("payment_date", -1)])

            estado = "Activo"
            ult_pago = ""
            vence = ""
            plan = ""

            if last_payment:
                ult_pago = last_payment["payment_date"]
                vence = last_payment["due_date"]
                plan = last_payment["plan"]

                vencimiento_dt = datetime.strptime(vence, "%Y-%m-%d").date()
                if hoy > vencimiento_dt:
                    estado = "Vencido"

            ws.append(
                [
                    member["name"],
                    member["created_at"].strftime("%Y-%m-%d"),
                    member.get("phone", ""),
                    estado,
                    ult_pago,
                    vence,
                    plan,
                ]
            )

        wb.save(EXCEL_FILE)

        with open(EXCEL_FILE, "rb") as f:
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
        from openpyxl import Workbook

        from config import EXCEL_FILE, REPORTS_DIR

        os.makedirs(REPORTS_DIR, exist_ok=True)

        svc = await get_report_service()

        wb = Workbook()
        ws = wb.active
        ws.title = "Pagos"

        ws.append(["Miembro", "Fecha Pago", "Monto", "Plan", "Vence", "Gracia"])

        all_payments = await svc.payments.find({}).sort("payment_date", -1).to_list(None)

        for p in all_payments:
            ws.append(
                [
                    p["member_name"],
                    p["payment_date"],
                    p["amount"],
                    p["plan"],
                    p["due_date"],
                    "Si" if p.get("grace_period") else "No",
                ]
            )

        wb.save(EXCEL_FILE)

        with open(EXCEL_FILE, "rb") as f:
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
        from config import REPORTS_DIR

        svc = await get_report_service()

        hoy = date.today()

        all_members = await svc.members.find({"active": True}).to_list(None)

        mes_actual = await svc.payments.find(
            {"payment_date": {"$gte": hoy.replace(day=1).strftime("%Y-%m-%d"), "$lte": hoy.strftime("%Y-%m-%d")}}
        ).to_list(None)

        monto_mes = sum(p["amount"] for p in mes_actual)

        vencidos_hoy = 0
        for member in all_members:
            last = await svc.payments.find_one({"member_id": str(member["_id"])}, sort=[("payment_date", -1)])
            if last:
                vence = datetime.strptime(last["due_date"], "%Y-%m-%d").date()
                if vence == hoy:
                    vencidos_hoy += 1

        contenido = f"""
=======================================
       RESUMEN GYM - {hoy.strftime("%Y-%m-%d")}
=======================================

👥 MIEMBROS
• Total activos: {len(all_members)}
• Vencen hoy: {vencidos_hoy}

💰 FINANZAS
• Ingresos del mes: ${monto_mes:,}
• Pagos este mes: {len(mes_actual)}

📅 ULTIMOS PAGOS
"""

        for p in mes_actual[-10:]:
            contenido += f"• {p['member_name']}: ${p['amount']} ({p['payment_date']})\n"

        filename = f"{REPORTS_DIR}/resumen_{hoy.strftime('%Y%m%d')}.txt"
        os.makedirs(REPORTS_DIR, exist_ok=True)

        with open(filename, "w") as f:
            f.write(contenido)

        with open(filename, "rb") as f:
            await update.message.reply_document(f, filename=f"resumen_{hoy.strftime('%Y%m%d')}.txt")
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
        from config import REPORTS_DIR

        svc = await get_report_service()

        os.makedirs(REPORTS_DIR, exist_ok=True)
        filename = f"{REPORTS_DIR}/miembros.csv"

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Nombre", "Fecha Registro", "Telefono", "Estado", "Ultimo Pago", "Vence"])

            all_members = await svc.members.find({"active": True}).to_list(None)
            hoy = date.today()

            for member in all_members:
                last = await svc.payments.find_one({"member_id": str(member["_id"])}, sort=[("payment_date", -1)])

                estado = "Activo"
                ult_pago = ""
                vence = ""

                if last:
                    ult_pago = last["payment_date"]
                    vence = last["due_date"]
                    if hoy > datetime.strptime(vence, "%Y-%m-%d").date():
                        estado = "Vencido"

                writer.writerow(
                    [
                        member["name"],
                        member["created_at"].strftime("%Y-%m-%d"),
                        member.get("phone", ""),
                        estado,
                        ult_pago,
                        vence,
                    ]
                )

        with open(filename, "rb") as f:
            await update.message.reply_document(f, filename="miembros.csv")
    except (OSError, ValueError) as e:
        logger.error(f"Error exportando CSV miembros: {e}")
        await update.message.reply_text("Error al generar archivo CSV de miembros")
    except Exception as e:
        logger.error(f"Error inesperado en exportar_csv_miembros: {e}")
        await update.message.reply_text("Error al exportar miembros CSV")
