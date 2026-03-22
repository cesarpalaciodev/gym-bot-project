from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, date
import logging

from database import get_collection
from keyboards import menu_pagos, menu_planes, menu_confirmar, menu_principal
from utils import (
    format_fecha,
    calcular_proximo_vencimiento,
    calcular_dias_vencido,
    calcular_vencimiento_con_gracia,
    es_tardio,
)
from config import PLANS

logger = logging.getLogger(__name__)

payment_state = {}


async def menu_payments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("💰 Menu pagos", reply_markup=menu_pagos)


async def registrar_pago_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    payment_state[user_id] = {"step": "nombre"}
    await update.message.reply_text("Ingresa el nombre del miembro")


async def historial_pagos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    payment_state[user_id] = {"step": "historial_nombre"}
    await update.message.reply_text("Ingresa el nombre del miembro para ver su historial")


async def procesar_pago(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    texto = update.message.text
    
    if user_id not in payment_state:
        return
    
    state = payment_state[user_id]
    members = get_collection("members")
    payments_col = get_collection("payments")
    
    try:
        if state["step"] == "nombre":
            member = members.find_one({"name": texto, "active": True})
            
            if not member:
                await update.message.reply_text("Miembro no encontrado")
                del payment_state[user_id]
                return
            
            last_payment = payments_col.find_one(
                {"member_id": str(member["_id"])},
                sort=[("payment_date", -1)]
            )
            
            payment_state[user_id] = {
                "step": "plan",
                "member_id": str(member["_id"]),
                "member_name": texto,
                "last_payment": last_payment,
            }
            
            await update.message.reply_text(
                f"Miembro: {texto}\n\n"
                f"Selecciona el plan:",
                reply_markup=menu_planes
            )
        
        elif state["step"] == "plan":
            if texto == "⬅️ Cancelar":
                del payment_state[user_id]
                await update.message.reply_text("Operacion cancelada")
                return
            
            plan_key = texto.split(".")[0]
            if plan_key not in PLANS:
                await update.message.reply_text("Selecciona un plan valido", reply_markup=menu_planes)
                return
            
            plan = PLANS[plan_key]
            payment_state[user_id]["plan"] = plan
            payment_state[user_id]["step"] = "confirmar"
            
            dias_vencido = 0
            if state["last_payment"]:
                vencimiento = datetime.strptime(state["last_payment"]["due_date"], "%Y-%m-%d").date()
                dias_vencido = calcular_dias_vencido(vencimiento)
            
            grace_text = ""
            if dias_vencido > 0:
                if dias_vencido <= 4:
                    grace_text = "\n⚠️ Dentro del periodo de gracia (1-4 dias)"
                else:
                    grace_text = f"\n⚠️ {dias_vencido} dias de retraso"
            
            await update.message.reply_text(
                f"📋 Resumen del pago:\n\n"
                f"👤 Miembro: {state['member_name']}\n"
                f"📦 Plan: {plan['name']}\n"
                f"💵 Monto: ${plan['price']}\n"
                f"📅 Duracion: {plan['months']} mes(es){grace_text}\n\n"
                f"¿Confirmar?",
                reply_markup=menu_confirmar
            )
        
        elif state["step"] == "confirmar":
            if texto == "❌ Cancelar":
                del payment_state[user_id]
                await update.message.reply_text("Operacion cancelada")
                return
            
            if texto != "✅ Confirmar":
                await update.message.reply_text("Selecciona una opcion valida", reply_markup=menu_confirmar)
                return
            
            plan = state["plan"]
            hoy = date.today()
            payment_date_str = format_fecha(hoy)
            
            grace_period = False
            if state["last_payment"]:
                ultimo_pago_date = datetime.strptime(state["last_payment"]["payment_date"], "%Y-%m-%d").date()
                vencimiento_anterior = datetime.strptime(state["last_payment"]["due_date"], "%Y-%m-%d").date()
                dias_vencido = calcular_dias_vencido(vencimiento_anterior)
                
                if dias_vencido > 4:
                    nuevo_vencimiento = calcular_proximo_vencimiento(hoy)
                else:
                    nuevo_vencimiento = calcular_proximo_vencimiento(ultimo_pago_date)
                    grace_period = True
            else:
                nuevo_vencimiento = calcular_proximo_vencimiento(hoy)
            
            payment_data = {
                "member_id": state["member_id"],
                "member_name": state["member_name"],
                "payment_date": payment_date_str,
                "amount": plan["price"],
                "plan": plan["name"],
                "due_date": format_fecha(nuevo_vencimiento),
                "grace_period": grace_period,
                "months": plan["months"],
                "created_at": datetime.utcnow(),
            }
            
            payments_col.insert_one(payment_data)
            
            await update.message.reply_text(
                f"✅ Pago registrado!\n\n"
                f"👤 Miembro: {state['member_name']}\n"
                f"💵 Monto: ${plan['price']}\n"
                f"📅 Pago: {payment_date_str}\n"
                f"📅 Vence: {format_fecha(nuevo_vencimiento)}\n"
                f"{'⚠️ Periodo de gracia' if grace_period else ''}",
                reply_markup=menu_principal
            )
            
            del payment_state[user_id]
        
        elif state["step"] == "historial_nombre":
            member = members.find_one({"name": texto, "active": True})
            
            if not member:
                await update.message.reply_text("Miembro no encontrado")
                del payment_state[user_id]
                return
            
            all_payments = list(payments_col.find(
                {"member_id": str(member["_id"])}
            ).sort("payment_date", -1))
            
            if not all_payments:
                await update.message.reply_text("Sin historial de pagos")
                del payment_state[user_id]
                return
            
            msg = f"📜 HISTORIAL DE PAGOS\n"
            msg += f"👤 {texto}\n\n"
            
            for i, p in enumerate(all_payments[:10], 1):
                msg += f"{i}. {p['payment_date']} - ${p['amount']} ({p['plan']})\n"
                msg += f"   Vence: {p['due_date']}"
                if p.get("grace_period"):
                    msg += " ⚠️"
                msg += "\n"
            
            await update.message.reply_text(msg)
            del payment_state[user_id]
    
    except Exception as e:
        logger.error(f"Error procesando pago: {e}")
        await update.message.reply_text("Error al procesar. Intenta de nuevo.")
        if user_id in payment_state:
            del payment_state[user_id]


def get_payment_state():
    return payment_state
