from __future__ import annotations

import logging
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from telegram import Update
from telegram.ext import ContextTypes

from keyboards import menu_estadisticas
from services import get_report_service
from utils import calcular_dias_vencido

logger = logging.getLogger(__name__)


async def menu_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        await update.message.reply_text("📈 Menu estadisticas", reply_markup=menu_estadisticas)
    except Exception as e:
        logger.error(f"Error en menu_stats: {e}")


async def miembros_activos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        svc = await get_report_service()
        all_members = await svc.members.find({"active": True}).to_list(None)
        total = len(all_members)

        activos = 0
        gracia = 0
        vencidos = 0

        for member in all_members:
            last_payment = await svc.payments.find_one({"member_id": str(member["_id"])}, sort=[("payment_date", -1)])

            if not last_payment:
                vencidos += 1
                continue

            vencimiento = datetime.strptime(last_payment["due_date"], "%Y-%m-%d").date()
            dias_vencido = calcular_dias_vencido(vencimiento)

            if dias_vencido == 0:
                activos += 1
            elif dias_vencido <= 4:
                gracia += 1
            else:
                vencidos += 1

        msg = "ESTADISTICAS DE MIEMBROS\n\n"
        msg += f"Total: {total}\n"
        msg += f"Activos: {activos}\n"
        msg += f"En gracia: {gracia}\n"
        msg += f"Vencidos: {vencidos}\n"

        if total > 0:
            msg += f"\nPorcentaje de renovacion: {(activos / total) * 100:.1f}%"

        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error en miembros_activos: {e}")
        await update.message.reply_text("Error al obtener estadisticas de miembros")


async def ingresos_mes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        svc = await get_report_service()
        data = await svc.get_income_data()

        monto_actual = data["current_amount"]
        monto_pasado = data["previous_amount"]
        registros = len(data["current_month_payments"])

        msg = "INGRESOS\n\n"
        msg += f"Este mes: ${monto_actual:,}\n"
        msg += f"Mes pasado: ${monto_pasado:,}\n"
        msg += f"Registros: {registros}\n\n"

        if monto_pasado > 0:
            cambio = ((monto_actual - monto_pasado) / monto_pasado) * 100
            emoji = "" if cambio >= 0 else ""
            msg += f"{emoji} Cambio: {cambio:+.1f}%"

        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error en ingresos_mes: {e}")
        await update.message.reply_text("Error al obtener estadisticas de ingresos")


async def vencimientos_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        svc = await get_report_service()

        hoy = date.today()

        all_members = await svc.members.find({"active": True}).to_list(None)

        hoy_vencen = []
        semana_vencen = []
        mes_vencen = []

        fin_semana = hoy + relativedelta(days=7)
        fin_mes = hoy + relativedelta(months=1)

        for member in all_members:
            last_payment = await svc.payments.find_one({"member_id": str(member["_id"])}, sort=[("payment_date", -1)])

            if not last_payment:
                continue

            vencimiento = datetime.strptime(last_payment["due_date"], "%Y-%m-%d").date()

            if vencimiento == hoy:
                hoy_vencen.append(member["name"])
            elif hoy < vencimiento <= fin_semana:
                semana_vencen.append((member["name"], last_payment["due_date"]))
            elif fin_semana < vencimiento <= fin_mes:
                mes_vencen.append((member["name"], last_payment["due_date"]))

        msg = "VENCIMIENTOS PROXIMOS\n\n"
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
    except Exception as e:
        logger.error(f"Error en vencimientos_stats: {e}")
        await update.message.reply_text("Error al obtener estadisticas de vencimientos")
