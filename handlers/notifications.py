from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, date
import logging

from database import get_collection
from config import GROUP_ID, GRACE_DAYS

logger = logging.getLogger(__name__)


async def notificacion_5am(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not GROUP_ID:
        logger.warning("GROUP_ID no configurado")
        return
    
    members = get_collection("members")
    payments = get_collection("payments")
    
    hoy = date.today()
    
    all_members = list(members.find({"active": True}))
    
    texto = "🔔 RECORDATORIO MATUTINO\n\n"
    texto += f"📅 Fecha: {hoy.strftime('%Y-%m-%d')}\n\n"
    
    activos = []
    hoy_vencen = []
    gracia = []
    vencidos = []
    
    for member in all_members:
        last_payment = payments.find_one(
            {"member_id": str(member["_id"])},
            sort=[("payment_date", -1)]
        )
        
        if not last_payment:
            vencidos.append((member["name"], 0))
            continue
        
        vencimiento = datetime.strptime(last_payment["due_date"], "%Y-%m-%d").date()
        
        dia_pago = vencimiento.day
        
        if hoy.day < dia_pago:
            activos.append(member["name"])
        elif hoy.day == dia_pago:
            hoy_vencen.append(member["name"])
        else:
            dias_vencido = (hoy - vencimiento).days
            if dias_vencido <= GRACE_DAYS:
                gracia.append((member["name"], dias_vencido))
            else:
                vencidos.append((member["name"], dias_vencido))
    
    texto += f"✅ ACTIVOS: {len(activos)}\n\n"
    
    if hoy_vencen:
        texto += f"⏰ VENCEN HOY ({len(hoy_vencen)}):\n"
        for name in hoy_vencen:
            texto += f"  • {name}\n"
        texto += "\n"
    
    if gracia:
        texto += f"⚠️ EN GRACIA ({len(gracia)}):\n"
        for name, dias in gracia:
            texto += f"  • {name} ({dias} dias)\n"
        texto += "\n"
    
    if vencidos:
        texto += f"💀 VENCIDOS ({len(vencidos)}):\n"
        for name, dias in vencidos:
            texto += f"  • {name} ({dias} dias)\n"
        texto += "\n"
    
    if not activos and not hoy_vencen and not gracia and not vencidos:
        texto = "✅ No hay miembros registrados\n"
    
    try:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=texto
        )
        logger.info("Notificacion 5AM enviada al grupo")
    except Exception as e:
        logger.error(f"Error enviando notificacion: {e}")
