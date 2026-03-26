from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging

from database import get_collection
from keyboards import menu_estadisticas

logger = logging.getLogger(__name__)


async def menu_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("📈 Menu estadisticas", reply_markup=menu_estadisticas)


async def miembros_activos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    members = get_collection("members")
    payments = get_collection("payments")
    
    hoy = date.today()
    
    all_members = list(members.find({"active": True}))
    total = len(all_members)
    
    activos = 0
    gracia = 0
    vencidos = 0
    
    for member in all_members:
        last_payment = payments.find_one(
            {"member_id": str(member["_id"])},
            sort=[("payment_date", -1)]
        )
        
        if not last_payment:
            vencidos += 1
            continue
        
        vencimiento = datetime.strptime(last_payment["due_date"], "%Y-%m-%d").date()
        dias_vencido = (hoy - vencimiento).days
        
        if dias_vencido <= 0:
            activos += 1
        elif dias_vencido <= 4:
            gracia += 1
        else:
            vencidos += 1
    
    msg = "📊 ESTADISTICAS DE MIEMBROS\n\n"
    msg += f"👥 Total: {total}\n"
    msg += f"✅ Activos: {activos}\n"
    msg += f"⚠️ En gracia: {gracia}\n"
    msg += f"💀 Vencidos: {vencidos}\n"
    
    if total > 0:
        msg += f"\n📈 Porcentaje de renovacion: {(activos/total)*100:.1f}%"
    
    await update.message.reply_text(msg)


async def ingresos_mes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payments = get_collection("payments")
    
    hoy = date.today()
    inicio_mes = hoy.replace(day=1)
    
    mes_actual_payments = list(payments.find({
        "payment_date": {
            "$gte": format_fecha(inicio_mes),
            "$lte": format_fecha(hoy)
        }
    }))
    
    monto_actual = sum(p["amount"] for p in mes_actual_payments)
    
    inicio_mes_pasado = (inicio_mes - relativedelta(months=1))
    fin_mes_pasado = inicio_mes - relativedelta(days=1)
    
    mes_pasado_payments = list(payments.find({
        "payment_date": {
            "$gte": format_fecha(inicio_mes_pasado),
            "$lte": format_fecha(fin_mes_pasado)
        }
    }))
    
    monto_pasado = sum(p["amount"] for p in mes_pasado_payments)
    
    msg = "💰 INGRESOS\n\n"
    msg += f"Este mes: ${monto_actual:,}\n"
    msg += f"Mes pasado: ${monto_pasado:,}\n"
    msg += f"Registros: {len(mes_actual_payments)}\n\n"
    
    if monto_pasado > 0:
        cambio = ((monto_actual - monto_pasado) / monto_pasado) * 100
        emoji = "📈" if cambio >= 0 else "📉"
        msg += f"{emoji} Cambio: {cambio:+.1f}%"
    
    await update.message.reply_text(msg)


async def vencimientos_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    members = get_collection("members")
    payments = get_collection("payments")
    
    hoy = date.today()
    
    all_members = list(members.find({"active": True}))
    
    hoy_vencen = []
    semana_vencen = []
    mes_vencen = []
    
    fin_semana = hoy + relativedelta(days=7)
    fin_mes = hoy + relativedelta(months=1)
    
    for member in all_members:
        last_payment = payments.find_one(
            {"member_id": str(member["_id"])},
            sort=[("payment_date", -1)]
        )
        
        if not last_payment:
            continue
        
        vencimiento = datetime.strptime(last_payment["due_date"], "%Y-%m-%d").date()
        
        if vencimiento == hoy:
            hoy_vencen.append(member["name"])
        elif hoy < vencimiento <= fin_semana:
            semana_vencen.append((member["name"], last_payment["due_date"]))
        elif fin_semana < vencimiento <= fin_mes:
            mes_vencen.append((member["name"], last_payment["due_date"]))
    
    msg = "📅 VENCIMIENTOS PROXIMOS\n\n"
    msg += f"Hoy ({hoy.strftime('%Y-%m-%d')}): {len(hoy_vencen)}\n"
    for name in hoy_vencen:
        msg += f"  • {name}\n"
    
    msg += f"\nEsta semana: {len(semana_vencen)}\n"
    for name, fecha in semana_vencen:
        msg += f"  • {name} ({fecha})\n"
    
    msg += f"\nEste mes: {len(mes_vencen)}\n"
    for name, fecha in mes_vencen[:5]:
        msg += f"  • {name} ({fecha})\n"
    if len(mes_vencen) > 5:
        msg += f"  ... y {len(mes_vencen) - 5} mas\n"
    
    await update.message.reply_text(msg)


def format_fecha(fecha: date) -> str:
    return fecha.strftime("%Y-%m-%d")
