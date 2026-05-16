from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from bson import ObjectId
from dateutil.relativedelta import relativedelta
from motor.motor_asyncio import AsyncIOMotorCollection

from models import Member
from utils import calcular_due_date, format_fecha, parse_fecha

logger = logging.getLogger(__name__)


class MemberService:
    def __init__(
        self,
        members_col: AsyncIOMotorCollection[Any],
        payments_col: AsyncIOMotorCollection[Any],
        *,
        today_fn: Callable[[], date] | None = None,
    ) -> None:
        self.members = members_col
        self.payments = payments_col
        self._today = today_fn or date.today

    async def add_member(self, name: str, phone: str, fecha_str: str) -> tuple[bool, str]:
        phone = phone.strip()
        if not (phone.isdigit() and len(phone) == 10 and phone.startswith("3")):
            return False, "Telefono invalido. Debe ser 10 digitos colombianos (ej: 3101234567)"
        fecha = parse_fecha(fecha_str)
        if not fecha:
            return False, "Fecha invalida. Formato: YYYY-MM-DD"
        if await self.members.find_one({"name": name}):
            return False, f"El miembro '{name}' ya existe"

        hoy = self._today()
        member = Member(name=name, phone=phone)
        result = await self.members.insert_one(member.to_dict())
        member_id = result.inserted_id

        dia_pago = fecha.day
        base = hoy + relativedelta(months=1) if hoy.day > dia_pago else hoy
        vencimiento = calcular_due_date(base, dia_pago)

        payment_data = {
            "member_id": str(member_id),
            "member_name": name,
            "payment_date": fecha_str,
            "amount": 0,
            "plan": "inicial",
            "due_date": format_fecha(vencimiento),
            "grace_period": False,
            "months": 1,
            "created_at": datetime.utcnow(),
        }
        await self.payments.insert_one(payment_data)
        return True, f"Miembro '{name}' agregado\nVence: {format_fecha(vencimiento)}"

    async def find_member(self, name: str, active_only: bool = True) -> dict[str, Any] | None:
        query: dict[str, Any] = {"name": name}
        if active_only:
            query["active"] = True
        return await self.members.find_one(query)

    async def delete_member(self, name: str) -> tuple[bool, str]:
        member = await self.find_member(name, active_only=False)
        if not member:
            return False, f"Miembro '{name}' no encontrado"
        await self.members.delete_one({"_id": ObjectId(member["_id"])})
        await self.payments.delete_many({"member_id": str(member["_id"])})
        logger.info("Miembro eliminado: %s", member["name"])
        return True, f"'{name}' eliminado de la base de datos"

    async def list_active_members(self) -> list[dict[str, Any]]:
        return await self.members.find({"active": True}).to_list(None)

    async def bulk_add(self, lines: list[str]) -> tuple[int, int]:
        agregados = 0
        errores = 0
        hoy = self._today()
        for linea in lines:
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
            if await self.members.find_one({"name": nombre}):
                errores += 1
                continue
            member = Member(name=nombre, phone=telefono)
            result = await self.members.insert_one(member.to_dict())
            member_id = result.inserted_id
            dia_pago = fecha.day
            base = hoy + relativedelta(months=1) if hoy.day > dia_pago else hoy
            vencimiento = calcular_due_date(base, dia_pago)
            await self.payments.insert_one(
                {
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
            )
            agregados += 1
        return agregados, errores

    async def bulk_delete(self, names: list[str]) -> tuple[int, int]:
        eliminados = 0
        no_encontrados = 0
        for nombre in names:
            nombre = nombre.strip()
            if not nombre:
                continue
            member = await self.find_member(nombre, active_only=False)
            if member:
                await self.members.delete_one({"_id": ObjectId(member["_id"])})
                await self.payments.delete_many({"member_id": str(member["_id"])})
                eliminados += 1
            else:
                no_encontrados += 1
        return eliminados, no_encontrados

    async def get_member_with_last_payment(self, name: str) -> dict[str, Any] | None:
        member = await self.find_member(name)
        if not member:
            return None
        last_payment = await self.payments.find_one({"member_id": str(member["_id"])}, sort=[("payment_date", -1)])
        return {"member": member, "last_payment": last_payment}

    async def list_members_with_payments(self) -> list[tuple[dict[str, Any], dict[str, Any] | None]]:
        all_members = await self.members.find({"active": True}).to_list(None)
        result: list[tuple[dict[str, Any], dict[str, Any] | None]] = []
        for member in all_members:
            last_payment = await self.payments.find_one({"member_id": str(member["_id"])}, sort=[("payment_date", -1)])
            result.append((member, last_payment))
        return result
