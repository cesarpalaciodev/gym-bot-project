from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from bson import ObjectId
import logging

from database import get_collection
from keyboards import menu_miembros, menu_principal
from utils import format_fecha, parse_fecha, calcular_proximo_vencimiento
from models import Member

logger = logging.getLogger(__name__)

user_state = {}


async def menu_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("👥 Menu miembros", reply_markup=menu_miembros)


async def agregar_miembro_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_state[user_id] = "agregar_miembro"
    await update.message.reply_text(
        "Ingresa: Nombre, Telefono, Fecha\n"
        "Ejemplo:\n"
        "Cesar Palacio Garcia 3101234567 2026-03-20"
    )


async def agregar_varios_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_state[user_id] = "agregar_varios"
    await update.message.reply_text(
        "Ingresa uno por linea:\n"
        "Nombre Telefono YYYY-MM-DD\n"
        "Cesar Palacio Garcia 3101234567 2026-03-20\n"
        "Maria Lopez Hernandez 3158765432 2026-03-21"
    )


async def buscar_miembro_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_state[user_id] = "buscar_miembro"
    await update.message.reply_text("Ingresa el nombre a buscar")


async def eliminar_miembro_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_state[user_id] = "eliminar_miembro"
    await update.message.reply_text("Ingresa el nombre completo del miembro a eliminar")


async def eliminar_varios_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_state[user_id] = "eliminar_varios"
    await update.message.reply_text(
        "Ingresa los nombres uno por linea:\n"
        "Cesar Palacio Garcia\n"
        "Maria Lopez Hernandez"
    )


async def lista_miembros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    members = get_collection("members")
    all_members = list(members.find({"active": True}))
    
    if not all_members:
        await update.message.reply_text("No hay miembros registrados")
        return
    
    payments = get_collection("payments")
    texto = "👥 MIEMBROS REGISTRADOS:\n\n"
    
    for m in all_members:
        last_payment = payments.find_one(
            {"member_id": m["_id"]},
            sort=[("payment_date", -1)]
        )
        if last_payment:
            texto += f"• {m['name']}"
            if m.get("phone"):
                texto += f" 📱{m['phone']}"
            texto += f"\n  Ultimo pago: {last_payment['payment_date']}\n"
            texto += f"  Vence: {last_payment['due_date']}\n\n"
        else:
            texto += f"• {m['name']}"
            if m.get("phone"):
                texto += f" 📱{m['phone']}"
            texto += f"\n  Sin pagos registrados\n\n"
    
    await update.message.reply_text(texto)


async def procesar_miembro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    texto = update.message.text
    
    if user_id not in user_state:
        return
    
    estado = user_state[user_id]
    members = get_collection("members")
    payments = get_collection("payments")
    
    try:
        if estado == "agregar_miembro":
            partes = texto.rsplit(" ", 2)
            if len(partes) != 3:
                await update.message.reply_text("Formato incorrecto. Usa: Nombre Telefono YYYY-MM-DD")
                del user_state[user_id]
                return
            
            nombre, telefono, fecha_str = partes
            
            telefono = telefono.strip()
            if not (telefono.isdigit() and len(telefono) == 10 and telefono.startswith("3")):
                await update.message.reply_text("Telefono invalido. Debe ser un numero colombiano de 10 digitos (ej: 3101234567)")
                del user_state[user_id]
                return
            
            fecha = parse_fecha(fecha_str)
            
            if not fecha:
                await update.message.reply_text("Fecha invalida. Formato: YYYY-MM-DD")
                del user_state[user_id]
                return
            
            if members.find_one({"name": nombre}):
                await update.message.reply_text(f"El miembro '{nombre}' ya existe")
                del user_state[user_id]
                return
            
            member = Member(name=nombre, phone=telefono)
            result = members.insert_one(member.to_dict())
            member_id = result.inserted_id
            
            vencimiento = fecha + relativedelta(months=2)
            ultimo_dia = calendar.monthrange(vencimiento.year, vencimiento.month)[1]
            dia_real = min(fecha.day, ultimo_dia)
            vencimiento = vencimiento.replace(day=dia_real)
            
            payment_data = {
                "member_id": str(member_id),
                "member_name": nombre,
                "payment_date": fecha_str,
                "amount": 0,
                "plan": "inicial",
                "due_date": format_fecha(vencimiento),
                "grace_period": False,
                "months": 1,
                "created_at": datetime.utcnow(),
            }
            payments.insert_one(payment_data)
            
            await update.message.reply_text(f"✅ Miembro '{nombre}' agregado\nVence: {format_fecha(vencimiento)}")
            del user_state[user_id]
        
        elif estado == "agregar_varios":
            lineas = texto.split("\n")
            agregados = 0
            errores = 0
            
            for linea in lineas:
                linea = linea.strip()
                if not linea:
                    continue
                
                partes = linea.rsplit(" ", 2)
                if len(partes) != 3:
                    errores += 1
                    continue
                
                nombre, telefono, fecha_str = partes
                telefono = telefono.strip()
                
                if not (telefono.isdigit() and len(telefono) == 10 and telefono.startswith("3")):
                    errores += 1
                    continue
                
                fecha = parse_fecha(fecha_str)
                
                if not fecha:
                    errores += 1
                    continue
                
                if members.find_one({"name": nombre}):
                    errores += 1
                    continue
                
                member = Member(name=nombre, phone=telefono)
                result = members.insert_one(member.to_dict())
                member_id = result.inserted_id
                
                vencimiento = fecha + relativedelta(months=2)
                ultimo_dia = calendar.monthrange(vencimiento.year, vencimiento.month)[1]
                dia_real = min(fecha.day, ultimo_dia)
                vencimiento = vencimiento.replace(day=dia_real)
                
                payment_data = {
                    "member_id": str(member_id),
                    "member_name": nombre,
                    "payment_date": fecha_str,
                    "amount": 0,
                    "plan": "inicial",
                    "due_date": format_fecha(vencimiento),
                    "grace_period": False,
                    "months": 1,
                    "created_at": datetime.utcnow(),
                }
                payments.insert_one(payment_data)
                agregados += 1
            
            await update.message.reply_text(
                f"✅ Agregados: {agregados}\n"
                f"❌ Errores: {errores}"
            )
            del user_state[user_id]
        
        elif estado == "buscar_miembro":
            member = members.find_one({"name": texto, "active": True})
            
            if not member:
                await update.message.reply_text("Miembro no encontrado")
            else:
                last_payment = payments.find_one(
                    {"member_id": str(member["_id"])},
                    sort=[("payment_date", -1)]
                )
                
                msg = f"👤 {member['name']}\n"
                msg += f"📅 Registro: {member['created_at'].strftime('%Y-%m-%d')}\n"
                if member.get("phone"):
                    msg += f"📱 {member['phone']}\n"
                
                if last_payment:
                    msg += f"💰 Ultimo pago: {last_payment['payment_date']}\n"
                    msg += f"📅 Vence: {last_payment['due_date']}\n"
                    msg += f"📋 Plan: {last_payment['plan']}"
                
                await update.message.reply_text(msg)
            
            del user_state[user_id]
        
        elif estado == "eliminar_miembro":
            member = members.find_one({"name": texto})
            payments_col = get_collection("payments")
            
            logger.info(f"Buscando miembro para eliminar: '{texto}'")
            logger.info(f"Miembro encontrado: {member}")
            
            if not member:
                await update.message.reply_text(f"Miembro '{texto}' no encontrado")
            else:
                members.delete_one({"_id": ObjectId(member["_id"])})
                payments_col.delete_many({"member_id": str(member["_id"])})
                logger.info(f"Miembro eliminado: {member['name']}")
                await update.message.reply_text(f"✅ '{texto}' eliminado de la base de datos")
            
            del user_state[user_id]
        
        elif estado == "eliminar_varios":
            nombres = texto.split("\n")
            eliminados = 0
            no_encontrados = 0
            payments_col = get_collection("payments")
            
            for nombre in nombres:
                nombre = nombre.strip()
                if not nombre:
                    continue
                
                member = members.find_one({"name": nombre})
                if member:
                    members.delete_one({"_id": ObjectId(member["_id"])})
                    payments_col.delete_many({"member_id": str(member["_id"])})
                    eliminados += 1
                else:
                    no_encontrados += 1
            
            await update.message.reply_text(
                f"✅ Eliminados: {eliminados}\n"
                f"❌ No encontrados: {no_encontrados}"
            )
            del user_state[user_id]
    
    except Exception as e:
        logger.error(f"Error procesando miembro: {e}")
        await update.message.reply_text("Error al procesar. Intenta de nuevo.")
        del user_state[user_id]


def get_user_state():
    return user_state
