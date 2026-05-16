import logging
from datetime import date, datetime

from telegram.ext import ContextTypes

from config import GROUP_ID
from database import get_collection
from utils import calcular_dias_vencido

logger = logging.getLogger(__name__)


async def notificacion_5am(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not GROUP_ID:
        logger.warning("GROUP_ID no configurado")
        return

    members = await get_collection("members")
    payments = await get_collection("payments")

    hoy = date.today()

    all_members = await members.find({"active": True}).to_list(None)

    texto = "🔔 RECORDATORIO MATUTINO\n\n"
    texto += f"📅 Fecha: {hoy.strftime('%Y-%m-%d')}\n\n"

    activos = []
    hoy_vencen = []
    gracia = []
    vencidos = []

    for member in all_members:
        last_payment = await payments.find_one({"member_id": str(member["_id"])}, sort=[("payment_date", -1)])

        if not last_payment:
            vencidos.append((member["name"], 0))
            continue

        vencimiento = datetime.strptime(last_payment["due_date"], "%Y-%m-%d").date()
        dias_vencido = calcular_dias_vencido(vencimiento)

        if dias_vencido == 0:
            if hoy == vencimiento:
                hoy_vencen.append(member["name"])
            else:
                activos.append(member["name"])
        elif dias_vencido <= 4:
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
        await context.bot.send_message(chat_id=GROUP_ID, text=texto)
        logger.info("Notificacion 5AM enviada al grupo")
    except Exception as e:
        logger.error(f"Error enviando notificacion: {e}")
