from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os
import csv
import logging

from database import get_collection
from keyboards import menu_exportar

logger = logging.getLogger(__name__)


async def menu_exports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("💾 Menu exportar", reply_markup=menu_exportar)


async def exportar_excel_miembros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from config import REPORTS_DIR, EXCEL_FILE
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill
    
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    members = get_collection("members")
    payments = get_collection("payments")
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Miembros"
    
    ws.append(["Nombre", "Fecha Registro", "Telefono", "Estado", "Ultimo Pago", "Vence", "Plan"])
    
    verde = PatternFill(start_color="90EE90", fill_type="solid")
    rojo = PatternFill(start_color="FF7F7F", fill_type="solid")
    
    hoy = date.today()
    
    all_members = list(members.find({"active": True}))
    
    for member in all_members:
        last_payment = payments.find_one(
            {"member_id": str(member["_id"])},
            sort=[("payment_date", -1)]
        )
        
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
        
        ws.append([
            member["name"],
            member["created_at"].strftime("%Y-%m-%d"),
            member.get("phone", ""),
            estado,
            ult_pago,
            vence,
            plan,
        ])
    
    wb.save(EXCEL_FILE)
    
    await update.message.reply_document(
        open(EXCEL_FILE, "rb"),
        filename="miembros_export.xlsx"
    )


async def exportar_excel_pagos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from config import REPORTS_DIR, EXCEL_FILE
    from openpyxl import Workbook
    
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    payments = get_collection("payments")
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Pagos"
    
    ws.append(["Miembro", "Fecha Pago", "Monto", "Plan", "Vence", "Gracia"])
    
    all_payments = list(payments.find({}).sort("payment_date", -1))
    
    for p in all_payments:
        ws.append([
            p["member_name"],
            p["payment_date"],
            p["amount"],
            p["plan"],
            p["due_date"],
            "Si" if p.get("grace_period") else "No",
        ])
    
    wb.save(EXCEL_FILE)
    
    await update.message.reply_document(
        open(EXCEL_FILE, "rb"),
        filename="pagos_export.xlsx"
    )


async def exportar_pdf_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from config import REPORTS_DIR
    import io
    
    members = get_collection("members")
    payments = get_collection("payments")
    
    hoy = date.today()
    
    all_members = list(members.find({"active": True}))
    
    mes_actual = list(payments.find({
        "payment_date": {
            "$gte": hoy.replace(day=1).strftime("%Y-%m-%d"),
            "$lte": hoy.strftime("%Y-%m-%d")
        }
    }))
    
    monto_mes = sum(p["amount"] for p in mes_actual)
    
    vencidos_hoy = 0
    for member in all_members:
        last = payments.find_one(
            {"member_id": str(member["_id"])},
            sort=[("payment_date", -1)]
        )
        if last:
            vence = datetime.strptime(last["due_date"], "%Y-%m-%d").date()
            if vence == hoy:
                vencidos_hoy += 1
    
    contenido = f"""
=======================================
       RESUMEN GYM - {hoy.strftime('%Y-%m-%d')}
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
    
    await update.message.reply_document(
        open(filename, "rb"),
        filename=f"resumen_{hoy.strftime('%Y%m%d')}.txt"
    )


async def exportar_csv_miembros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from config import REPORTS_DIR
    import io
    
    members = get_collection("members")
    payments = get_collection("payments")
    
    os.makedirs(REPORTS_DIR, exist_ok=True)
    filename = f"{REPORTS_DIR}/miembros.csv"
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Nombre", "Fecha Registro", "Telefono", "Estado", "Ultimo Pago", "Vence"])
        
        all_members = list(members.find({"active": True}))
        hoy = date.today()
        
        for member in all_members:
            last = payments.find_one(
                {"member_id": str(member["_id"])},
                sort=[("payment_date", -1)]
            )
            
            estado = "Activo"
            ult_pago = ""
            vence = ""
            
            if last:
                ult_pago = last["payment_date"]
                vence = last["due_date"]
                if hoy > datetime.strptime(vence, "%Y-%m-%d").date():
                    estado = "Vencido"
            
            writer.writerow([
                member["name"],
                member["created_at"].strftime("%Y-%m-%d"),
                member.get("phone", ""),
                estado,
                ult_pago,
                vence,
            ])
    
    await update.message.reply_document(
        open(filename, "rb"),
        filename="miembros.csv"
    )
