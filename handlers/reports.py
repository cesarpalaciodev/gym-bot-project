from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging

from database import get_collection
from keyboards import menu_reportes
from utils import format_fecha, calcular_proximo_vencimiento

logger = logging.getLogger(__name__)


async def menu_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("📊 Menu reportes", reply_markup=menu_reportes)


async def deudores(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    members = get_collection("members")
    payments = get_collection("payments")
    
    hoy = date.today()
    texto = "⚠️ MIEMBROS CON PAGOS VENCIDOS:\n\n"
    
    all_members = list(members.find({"active": True}))
    
    if not all_members:
        await update.message.reply_text("No hay miembros registrados")
        return
    
    deudores_count = 0
    
    for member in all_members:
        last_payment = payments.find_one(
            {"member_id": str(member["_id"])},
            sort=[("payment_date", -1)]
        )
        
        if not last_payment:
            continue
        
        vencimiento = datetime.strptime(last_payment["due_date"], "%Y-%m-%d").date()
        
        if hoy > vencimiento:
            dias_vencido = (hoy - vencimiento).days
            if dias_vencido > 4:
                texto += f"• {member['name']}\n"
                texto += f"  💀 Vencio: {last_payment['due_date']}\n"
                texto += f"  📅 Dias vencido: {dias_vencido}\n\n"
                deudores_count += 1
    
    if deudores_count == 0:
        texto = "✅ No hay miembros con pagos vencidos"
    
    await update.message.reply_text(texto)


async def excel_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from config import EXCEL_FILE
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill
    import os
    
    members = get_collection("members")
    payments = get_collection("payments")
    
    os.makedirs("reports", exist_ok=True)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Miembros"
    
    ws.append(["Nombre", "Fecha Registro", "Ultimo Pago", "Vence", "Plan", "Estado"])
    
    verde = PatternFill(start_color="90EE90", fill_type="solid")
    rojo = PatternFill(start_color="FF7F7F", fill_type="solid")
    amarillo = PatternFill(start_color="FFFF99", fill_type="solid")
    
    hoy = date.today()
    
    all_members = list(members.find({"active": True}))
    
    for member in all_members:
        last_payment = payments.find_one(
            {"member_id": str(member["_id"])},
            sort=[("payment_date", -1)]
        )
        
        if last_payment:
            vencimiento = datetime.strptime(last_payment["due_date"], "%Y-%m-%d").date()
            dias_vencido = (hoy - vencimiento).days
            
            if dias_vencido <= 4:
                estado = "Al dia"
                fill = verde
            else:
                estado = "Vencido"
                fill = rojo
            
            ws.append([
                member["name"],
                member["created_at"].strftime("%Y-%m-%d"),
                last_payment["payment_date"],
                last_payment["due_date"],
                last_payment["plan"],
                estado,
            ])
            
            fila = ws.max_row
            ws[f"F{fila}"].fill = fill
    
    wb.save(EXCEL_FILE)
    
    await update.message.reply_document(
        open(EXCEL_FILE, "rb"),
        filename="reporte_miembros.xlsx"
    )
