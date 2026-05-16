"""Statistics service for calculating member and payment statistics."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from dateutil.relativedelta import relativedelta

from repositories.member_repository import MemberRepository
from repositories.payment_repository import PaymentRepository
from utils.dates import calcular_dias_vencido

logger = logging.getLogger(__name__)


@dataclass
class MemberStats:
    """Statistics for active members."""

    total: int
    activos: int
    en_gracia: int
    vencidos: int

    @property
    def renewal_rate(self) -> float:
        """Calculate renewal rate percentage."""
        if self.total > 0:
            return (self.activos / self.total) * 100
        return 0.0


@dataclass
class IncomeStats:
    """Statistics for income comparison."""

    monto_actual: int
    monto_pasado: int
    registros: int

    @property
    def change_percentage(self) -> float | None:
        """Calculate percentage change from previous month."""
        if self.monto_pasado > 0:
            return ((self.monto_actual - self.monto_pasado) / self.monto_pasado) * 100
        return None


@dataclass
class ExpirationStats:
    """Statistics for upcoming expirations."""

    hoy: list[str]
    esta_semana: list[tuple[str, str]]
    este_mes: list[tuple[str, str]]


class StatsService:
    """Service for calculating various statistics."""

    def __init__(
        self,
        member_repo: MemberRepository,
        payment_repo: PaymentRepository,
    ) -> None:
        self._member_repo = member_repo
        self._payment_repo = payment_repo

    async def get_member_stats(self) -> MemberStats:
        """Calculate statistics for active members.

        Returns:
            MemberStats with counts of active, grace, and overdue members.
        """
        all_members = await self._member_repo.get_all_active()
        total = len(all_members)

        activos = 0
        gracia = 0
        vencidos = 0

        for member in all_members:
            last_payment = await self._payment_repo.get_last_by_member(str(member["_id"]))

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

        return MemberStats(
            total=total,
            activos=activos,
            en_gracia=gracia,
            vencidos=vencidos,
        )

    async def get_income_stats(self) -> IncomeStats:
        """Calculate income statistics for current and previous month.

        Returns:
            IncomeStats with current month, previous month, and record count.
        """
        from services.report_service import ReportService

        # Use ReportService for income data since it has the complex logic
        report_svc = ReportService(self._member_repo.collection, self._payment_repo.collection)
        data = await report_svc.get_income_data()

        return IncomeStats(
            monto_actual=data["current_amount"],
            monto_pasado=data["previous_amount"],
            registros=len(data["current_month_payments"]),
        )

    async def get_expiration_stats(self, reference_date: date | None = None) -> ExpirationStats:
        """Calculate upcoming expiration statistics.

        Args:
            reference_date: Date to calculate from (defaults to today).

        Returns:
            ExpirationStats with members expiring today, this week, and this month.
        """
        hoy = reference_date or date.today()
        all_members = await self._member_repo.get_all_active()

        hoy_vencen: list[str] = []
        semana_vencen: list[tuple[str, str]] = []
        mes_vencen: list[tuple[str, str]] = []

        fin_semana = hoy + relativedelta(days=7)
        fin_mes = hoy + relativedelta(months=1)

        for member in all_members:
            last_payment = await self._payment_repo.get_last_by_member(str(member["_id"]))

            if not last_payment:
                continue

            vencimiento = datetime.strptime(last_payment["due_date"], "%Y-%m-%d").date()

            if vencimiento == hoy:
                hoy_vencen.append(member["name"])
            elif hoy < vencimiento <= fin_semana:
                semana_vencen.append((member["name"], last_payment["due_date"]))
            elif fin_semana < vencimiento <= fin_mes:
                mes_vencen.append((member["name"], last_payment["due_date"]))

        return ExpirationStats(
            hoy=hoy_vencen,
            esta_semana=semana_vencen,
            este_mes=mes_vencen,
        )
