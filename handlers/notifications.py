from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, date
import logging

from database import get_collection
from config import ADMIN_ID

logger = logging.getLogger(__name__)


async def notificacion_5am(context: ContextTypes.DEFAULT_TYPE) -> None:
    members = get_collection("members")
    payments = get_collection("payments")
    
    hoy = date.today()
    
    all_members = list(members.find({"active": True}))
    
    texto = "🔔 RECORDATORIO MATUTINO\n\n"
    texto += f"📅 Fecha: {hoy.strftime('%Y-%m-%d')}\n\n"
    
    hoy_vencen = []
    vencidos = []
    
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
        elif vencimiento < hoy:
            dias = (hoy - vencimiento).days
            vencidos.append((member["name"], dias))
    
    if hoy_vencen:
        texto += f"⏰ VENCEN HOY ({len(hoy_vencen)}):\n"
        for name in hoy_vencen:
            texto += f"  • {name}\n"
        texto += "\n"
    
    if vencidos:
        texto += f"💀 VENCIDOS ({len(vencidos)}):\n"
        for name, dias in vencidos:
            texto += f"  • {name} ({dias} dias)\n"
        texto += "\n"
    
    if not hoy_vencen and not vencidos:
        texto += "✅ No hay vencimientos hoy\n"
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=texto
        )
        logger.info("Notificacion 5AM enviada")
    except Exception as e:
        logger.error(f"Error enviando notificacion: {e}")
