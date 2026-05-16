"""Notification service for generating daily reports."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime

from repositories.member_repository import MemberRepository
from repositories.payment_repository import PaymentRepository
from utils.dates import calcular_dias_vencido

logger = logging.getLogger(__name__)


@dataclass
class DailyNotificationData:
    """Data for daily notification report."""

    fecha: date
    activos: list[str] = field(default_factory=list)
    hoy_vencen: list[str] = field(default_factory=list)
    gracia: list[tuple[str, int]] = field(default_factory=list)
    vencidos: list[tuple[str, int]] = field(default_factory=list)

    @property
    def total_activos(self) -> int:
        return len(self.activos)

    @property
    def total_hoy_vencen(self) -> int:
        return len(self.hoy_vencen)

    @property
    def total_gracia(self) -> int:
        return len(self.gracia)

    @property
    def total_vencidos(self) -> int:
        return len(self.vencidos)

    def is_empty(self) -> bool:
        """Check if there's no data to report."""
        return not self.activos and not self.hoy_vencen and not self.gracia and not self.vencidos

    def format_message(self) -> str:
        """Format the notification data as a Telegram message."""
        if self.is_empty():
            return "No hay miembros registrados\n"

        texto = "RECORDATORIO MATUTINO\n\n"
        texto += f"Fecha: {self.fecha.strftime('%Y-%m-%d')}\n\n"
        texto += f"ACTIVOS: {self.total_activos}\n\n"

        if self.hoy_vencen:
            texto += f"VENCEN HOY ({self.total_hoy_vencen}):\n"
            for name in self.hoy_vencen:
                texto += f"  • {name}\n"
            texto += "\n"

        if self.gracia:
            texto += f"EN GRACIA ({self.total_gracia}):\n"
            for name, dias in self.gracia:
                texto += f"  • {name} ({dias} dias)\n"
            texto += "\n"

        if self.vencidos:
            texto += f"VENCIDOS ({self.total_vencidos}):\n"
            for name, dias in self.vencidos:
                texto += f"  • {name} ({dias} dias)\n"
            texto += "\n"

        return texto


class NotificationService:
    """Service for generating notification content."""

    def __init__(
        self,
        member_repo: MemberRepository,
        payment_repo: PaymentRepository,
    ) -> None:
        self._member_repo = member_repo
        self._payment_repo = payment_repo

    async def generate_daily_notification(self, reference_date: date | None = None) -> DailyNotificationData:
        """Generate data for daily morning notification.

        Args:
            reference_date: Date to generate report for (defaults to today).

        Returns:
            DailyNotificationData with categorized members.
        """
        hoy = reference_date or date.today()
        all_members = await self._member_repo.get_all_active()

        data = DailyNotificationData(fecha=hoy)

        for member in all_members:
            last_payment = await self._payment_repo.get_last_by_member(str(member["_id"]))

            if not last_payment:
                data.vencidos.append((member["name"], 0))
                continue

            vencimiento = datetime.strptime(last_payment["due_date"], "%Y-%m-%d").date()
            dias_vencido = calcular_dias_vencido(vencimiento)

            if dias_vencido == 0:
                if hoy == vencimiento:
                    data.hoy_vencen.append(member["name"])
                else:
                    data.activos.append(member["name"])
            elif dias_vencido <= 4:
                data.gracia.append((member["name"], dias_vencido))
            else:
                data.vencidos.append((member["name"], dias_vencido))

        return data
