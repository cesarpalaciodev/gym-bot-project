from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import logging

from database import get_collection
from keyboards import menu_reportes
from config import GRACE_DAYS
from utils import format_fecha

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
        
        payment_date = datetime.strptime(last_payment["payment_date"], "%Y-%m-%d").date()
        dia_pago = payment_date.day
        
        if hoy.day < dia_pago:
            continue
        
        if hoy.day == dia_pago:
            next_due = hoy + relativedelta(months=1)
            ultimo_dia = calendar.monthrange(next_due.year, next_due.month)[1]
            dia_real = min(dia_pago, ultimo_dia)
            next_due = next_due.replace(day=dia_real)
            
            texto += f"• {member['name']}\n"
            texto += f"  ⏰ Vence hoy: {format_fecha(next_due)}\n\n"
            deudores_count += 1
        else:
            meses_vencidos = (hoy.year - payment_date.year) * 12 + (hoy.month - payment_date.month)
            
            if meses_vencidos > 1:
                grace_text = f" ({meses_vencidos-1} meses)" if meses_vencidos <= 4 else ""
                texto += f"• {member['name']}\n"
                texto += f"  💀 ultimo pago: {last_payment['payment_date']}\n"
                texto += f"  📅 Meses vencido: {meses_vencidos-1}{grace_text}\n\n"
                deudores_count += 1
    
    if deudores_count == 0:
        texto = "✅ Todos los miembros estan al dia"
    
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
    
    ws.append(["Nombre", "Fecha Registro", "Ultimo Pago", "Vence", "Plan", "Dias Vencido", "Estado"])
    
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
            dia_pago = vencimiento.day
            
            if hoy.day < dia_pago:
                estado = "Al dia"
                dias_display = 0
                fill = verde
            elif hoy.day == dia_pago:
                estado = "Vence hoy"
                dias_display = 0
                fill = amarillo
            else:
                dias_vencido = (hoy - vencimiento).days
                if dias_vencido <= GRACE_DAYS:
                    estado = "En gracia"
                    dias_display = dias_vencido
                    fill = amarillo
                else:
                    estado = "Vencido"
                    dias_display = dias_vencido
                    fill = rojo
            
            ws.append([
                member["name"],
                member["created_at"].strftime("%Y-%m-%d"),
                last_payment["payment_date"],
                last_payment["due_date"],
                last_payment["plan"],
                dias_display,
                estado,
            ])
            
            fila = ws.max_row
            ws[f"G{fila}"].fill = fill
    
    wb.save(EXCEL_FILE)
    
    await update.message.reply_document(
        open(EXCEL_FILE, "rb"),
        filename="reporte_miembros.xlsx"
    )
