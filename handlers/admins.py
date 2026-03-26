from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
import logging

from database import get_collection
from keyboards import menu_admin, menu_confirmar
from models import Admin

logger = logging.getLogger(__name__)

admin_state = {}


async def menu_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    admins = get_collection("admins")
    admin = admins.find_one({"telegram_id": user_id})
    
    if not admin or admin["role"] != "super_admin":
        await update.message.reply_text("Solo Super Admin puede acceder")
        return
    
    await update.message.reply_text("⚙️ Menu Admin", reply_markup=menu_admin)


async def agregar_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    admins_col = get_collection("admins")
    admin = admins_col.find_one({"telegram_id": user_id})
    
    if not admin or admin["role"] != "super_admin":
        await update.message.reply_text("Solo Super Admin puede acceder")
        return
    
    admin_state[user_id] = "agregar_admin"
    await update.message.reply_text(
        "Ingresa el ID de Telegram del nuevo admin:\n\n"
        "Para obtener el ID, el usuario puede usar @userinfobot"
    )


async def lista_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    admins_col = get_collection("admins")
    admin = admins_col.find_one({"telegram_id": user_id})
    
    if not admin or admin["role"] != "super_admin":
        await update.message.reply_text("Solo Super Admin puede acceder")
        return
    
    all_admins = list(admins_col.find({}))
    
    if not all_admins:
        await update.message.reply_text("No hay admins registrados")
        return
    
    msg = "👥 ADMINISTRADORES:\n\n"
    for a in all_admins:
        role_emoji = {"super_admin": "👑", "admin": "⭐", "viewer": "👁️"}.get(a["role"], "❓")
        msg += f"{role_emoji} {a['name']}\n"
        msg += f"   ID: {a['telegram_id']}\n"
        msg += f"   Rol: {a['role']}\n\n"
    
    await update.message.reply_text(msg)


async def quitar_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    admins_col = get_collection("admins")
    admin = admins_col.find_one({"telegram_id": user_id})
    
    if not admin or admin["role"] != "super_admin":
        await update.message.reply_text("Solo Super Admin puede acceder")
        return
    
    admin_state[user_id] = "quitar_admin"
    await update.message.reply_text("Ingresa el ID de Telegram del admin a eliminar")


async def cambiar_rol_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    admins_col = get_collection("admins")
    admin = admins_col.find_one({"telegram_id": user_id})
    
    if not admin or admin["role"] != "super_admin":
        await update.message.reply_text("Solo Super Admin puede acceder")
        return
    
    admin_state[user_id] = "cambiar_rol_id"
    await update.message.reply_text("Ingresa el ID de Telegram del admin")


async def procesar_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    texto = update.message.text.strip()
    
    if user_id not in admin_state:
        return
    
    admins_col = get_collection("admins")
    estado = admin_state[user_id]
    
    try:
        if estado == "agregar_admin":
            try:
                telegram_id = int(texto)
            except ValueError:
                await update.message.reply_text("ID invalido. Debe ser un numero.")
                del admin_state[user_id]
                return
            
            if admins_col.find_one({"telegram_id": telegram_id}):
                await update.message.reply_text("Este usuario ya es admin")
                del admin_state[user_id]
                return
            
            admin_state[user_id] = {"step": "agregar_nombre", "telegram_id": telegram_id}
            await update.message.reply_text("Ingresa el nombre del nuevo admin:")
        
        elif estado == "agregar_nombre":
            if isinstance(admin_state[user_id], dict) and admin_state[user_id].get("step") == "agregar_nombre":
                nuevo_admin = Admin(
                    telegram_id=admin_state[user_id]["telegram_id"],
                    name=texto,
                    role="admin"
                )
                admins_col.insert_one(nuevo_admin.to_dict())
                
                await update.message.reply_text(
                    f"✅ Admin agregado:\n"
                    f"👤 {texto}\n"
                    f"🆔 {nuevo_admin.telegram_id}\n"
                    f"📋 Rol: admin"
                )
                del admin_state[user_id]
        
        elif estado == "quitar_admin":
            try:
                telegram_id = int(texto)
            except ValueError:
                await update.message.reply_text("ID invalido")
                del admin_state[user_id]
                return
            
            result = admins_col.delete_one({"telegram_id": telegram_id})
            
            if result.deleted_count > 0:
                await update.message.reply_text("✅ Admin eliminado")
            else:
                await update.message.reply_text("Admin no encontrado")
            
            del admin_state[user_id]
        
        elif estado == "cambiar_rol_id":
            try:
                telegram_id = int(texto)
            except ValueError:
                await update.message.reply_text("ID invalido")
                del admin_state[user_id]
                return
            
            target_admin = admins_col.find_one({"telegram_id": telegram_id})
            
            if not target_admin:
                await update.message.reply_text("Admin no encontrado")
                del admin_state[user_id]
                return
            
            admin_state[user_id] = {
                "step": "cambiar_rol_rol",
                "telegram_id": telegram_id,
                "name": target_admin["name"]
            }
            
            await update.message.reply_text(
                f"Admin: {target_admin['name']}\n"
                f"Rol actual: {target_admin['role']}\n\n"
                f"Selecciona nuevo rol:\n"
                f"1. admin\n"
                f"2. viewer"
            )
        
        elif isinstance(estado, dict) and estado.get("step") == "cambiar_rol_rol":
            rol_map = {"1": "admin", "2": "viewer"}
            
            if texto not in rol_map:
                await update.message.reply_text("Selecciona 1 o 2")
                return
            
            nuevo_rol = rol_map[texto]
            
            admins_col.update_one(
                {"telegram_id": estado["telegram_id"]},
                {"$set": {"role": nuevo_rol, "updated_at": datetime.utcnow()}}
            )
            
            await update.message.reply_text(
                f"✅ Rol actualizado:\n"
                f"👤 {estado['name']}\n"
                f"📋 Nuevo rol: {nuevo_rol}"
            )
            del admin_state[user_id]
    
    except Exception as e:
        logger.error(f"Error procesando admin: {e}")
        await update.message.reply_text("Error al procesar. Intenta de nuevo.")
        if user_id in admin_state:
            del admin_state[user_id]


def get_admin_state():
    return admin_state
