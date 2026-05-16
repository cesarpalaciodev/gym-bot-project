from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from config import PLANS
from utils import calcular_dias_vencido, calcular_due_date, format_fecha

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(
        self,
        members_col: AsyncIOMotorCollection[Any],
        payments_col: AsyncIOMotorCollection[Any],
        *,
        plans: dict[str, dict[str, Any]] | None = None,
        today_fn: Callable[[], date] | None = None,
    ) -> None:
        self.members = members_col
        self.payments = payments_col
        self._plans = plans or PLANS
        self._today = today_fn or date.today

    async def find_member(self, name: str) -> dict[str, Any] | None:
        return await self.members.find_one({"name": name, "active": True})

    async def get_last_payment(self, member_id: str) -> dict[str, Any] | None:
        return await self.payments.find_one({"member_id": member_id}, sort=[("payment_date", -1)])

    async def get_history(self, member_id: str, limit: int = 10) -> list[dict[str, Any]]:
        cursor = self.payments.find({"member_id": member_id}).sort("payment_date", -1)
        return await cursor.to_list(limit)

    async def register_payment(
        self, member_id: str, member_name: str, plan_key: str, last_payment: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        plan = self._plans.get(plan_key)
        if not plan:
            return None

        hoy = self._today()
        payment_date_str = format_fecha(hoy)
        grace_period = False

        if last_payment:
            vencimiento_anterior = datetime.strptime(last_payment["due_date"], "%Y-%m-%d").date()
            dia_pago = vencimiento_anterior.day
            dias_vencido = calcular_dias_vencido(vencimiento_anterior)
            ultimo_pago_date = datetime.strptime(last_payment["payment_date"], "%Y-%m-%d").date()

            if dias_vencido > 4:
                nuevo_vencimiento = calcular_due_date(hoy, hoy.day)
            else:
                nuevo_vencimiento = calcular_due_date(ultimo_pago_date, dia_pago)
                grace_period = True
        else:
            nuevo_vencimiento = calcular_due_date(hoy, hoy.day)

        payment_data = {
            "member_id": member_id,
            "member_name": member_name,
            "payment_date": payment_date_str,
            "amount": plan["price"],
            "plan": plan["name"],
            "due_date": format_fecha(nuevo_vencimiento),
            "grace_period": grace_period,
            "months": plan["months"],
            "created_at": datetime.utcnow(),
        }
        await self.payments.insert_one(payment_data)

        return {
            "plan_name": plan["name"],
            "price": plan["price"],
            "payment_date": payment_date_str,
            "due_date": format_fecha(nuevo_vencimiento),
            "grace_period": grace_period,
        }

    async def get_grace_info(self, last_payment: dict[str, Any] | None) -> tuple[int, str]:
        if not last_payment:
            return 0, ""
        vencimiento = datetime.strptime(last_payment["due_date"], "%Y-%m-%d").date()
        dias_vencido = calcular_dias_vencido(vencimiento)
        if dias_vencido == 0:
            return 0, ""
        if dias_vencido <= 4:
            return dias_vencido, "\n Dentro del periodo de gracia (1-4 dias)"
        return dias_vencido, f"\n {dias_vencido} dias de retraso"

    async def get_grace_text(self, last_payment: dict[str, Any] | None) -> str:
        _, grace_str = await self.get_grace_info(last_payment)
        return grace_str

    async def format_history(self, member_name: str, payments_list: list[dict[str, Any]]) -> str:
        if not payments_list:
            return ""
        msg = "HISTORIAL DE PAGOS\n"
        msg += f" {member_name}\n\n"
        for i, p in enumerate(payments_list[:10], 1):
            msg += f"{i}. {p['payment_date']} - ${p['amount']} ({p['plan']})\n"
            msg += f"   Vence: {p['due_date']}"
            if p.get("grace_period"):
                msg += " \u26a0\ufe0f"
            msg += "\n"
        return msg
