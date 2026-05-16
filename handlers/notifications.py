from __future__ import annotations

import logging
from datetime import date, datetime

from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import GROUP_ID
from services import get_report_service
from utils import calcular_dias_vencido

logger = logging.getLogger(__name__)


async def notificacion_5am(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not GROUP_ID:
        logger.warning("GROUP_ID no configurado")
        return

    svc = await get_report_service()
    hoy = date.today()

    all_members = await svc.members.find({"active": True}).to_list(None)

    texto = "RECORDATORIO MATUTINO\n\n"
    texto += f"Fecha: {hoy.strftime('%Y-%m-%d')}\n\n"

    activos = []
    hoy_vencen = []
    gracia = []
    vencidos = []

    for member in all_members:
        last_payment = await svc.payments.find_one({"member_id": str(member["_id"])}, sort=[("payment_date", -1)])

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

    texto += f"ACTIVOS: {len(activos)}\n\n"

    if hoy_vencen:
        texto += f"VENCEN HOY ({len(hoy_vencen)}):\n"
        for name in hoy_vencen:
            texto += f"  \u2022 {name}\n"
        texto += "\n"

    if gracia:
        texto += f"EN GRACIA ({len(gracia)}):\n"
        for name, dias in gracia:
            texto += f"  \u2022 {name} ({dias} dias)\n"
        texto += "\n"

    if vencidos:
        texto += f"VENCIDOS ({len(vencidos)}):\n"
        for name, dias in vencidos:
            texto += f"  \u2022 {name} ({dias} dias)\n"
        texto += "\n"

    if not activos and not hoy_vencen and not gracia and not vencidos:
        texto = "No hay miembros registrados\n"

    try:
        await context.bot.send_message(chat_id=GROUP_ID, text=texto)
        logger.info("Notificacion 5AM enviada al grupo")
    except TelegramError as e:
        logger.error(f"Error de Telegram enviando notificacion: {e}")
    except Exception as e:
        logger.exception(f"Error inesperado enviando notificacion: {e}")
