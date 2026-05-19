"""Export service for generating Excel, CSV, and TXT reports."""

from __future__ import annotations

import csv
import logging
import os
from datetime import date, datetime

from config import EXCEL_FILE, REPORTS_DIR
from repositories.member_repository import MemberRepository
from repositories.payment_repository import PaymentRepository

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting data to various formats."""

    def __init__(
        self,
        member_repo: MemberRepository,
        payment_repo: PaymentRepository,
    ) -> None:
        self._member_repo = member_repo
        self._payment_repo = payment_repo

    async def export_members_to_excel(self, filepath: str | None = None) -> str:
        """Export active members to Excel file.

        Returns:
            Path to the generated Excel file.
        """
        from openpyxl import Workbook

        filepath = filepath or EXCEL_FILE
        os.makedirs(os.path.dirname(filepath) or REPORTS_DIR, exist_ok=True)

        wb = Workbook()
        ws = wb.active
        ws.title = "Miembros"

        ws.append(["Nombre", "Fecha Registro", "Telefono", "Estado", "Ultimo Pago", "Vence", "Plan"])

        hoy = date.today()
        all_members = await self._member_repo.get_all_active()

        for member in all_members:
            last_payment = await self._payment_repo.get_last_by_member(str(member["_id"]))

            estado = "Activo"
            ult_pago = ""
            vence = ""
            plan = ""

            if last_payment:
                ult_pago = last_payment["payment_date"]
                vence = last_payment["due_date"]
                plan = last_payment["plan"]

                vencimiento_dt = datetime.strptime(vence, "%Y-%m-%d").date()
                if hoy > vencimiento_dt:
                    estado = "Vencido"

            ws.append(
                [
                    member["name"],
                    member["created_at"].strftime("%Y-%m-%d"),
                    member.get("phone", ""),
                    estado,
                    ult_pago,
                    vence,
                    plan,
                ]
            )

        wb.save(filepath)
        return filepath

    async def export_payments_to_excel(self, filepath: str | None = None) -> str:
        """Export all payments to Excel file.

        Returns:
            Path to the generated Excel file.
        """
        from openpyxl import Workbook

        filepath = filepath or EXCEL_FILE
        os.makedirs(os.path.dirname(filepath) or REPORTS_DIR, exist_ok=True)

        wb = Workbook()
        ws = wb.active
        ws.title = "Pagos"

        ws.append(["Miembro", "Fecha Pago", "Monto", "Plan", "Vence", "Gracia"])

        all_payments = await self._payment_repo.get_all_payments()

        for p in all_payments:
            ws.append(
                [
                    p["member_name"],
                    p["payment_date"],
                    p["amount"],
                    p["plan"],
                    p["due_date"],
                    "Si" if p.get("grace_period") else "No",
                ]
            )

        wb.save(filepath)
        return filepath

    async def generate_txt_summary(self, filepath: str | None = None) -> str:
        """Generate TXT summary report.

        Returns:
            Path to the generated TXT file.
        """
        hoy = date.today()
        all_members = await self._member_repo.get_all_active()

        mes_actual = await self._payment_repo.get_payments_for_period(
            hoy.replace(day=1).strftime("%Y-%m-%d"),
            hoy.strftime("%Y-%m-%d"),
        )

        monto_mes = sum(p["amount"] for p in mes_actual)

        vencidos_hoy = 0
        for member in all_members:
            last = await self._payment_repo.get_last_by_member(str(member["_id"]))
            if last:
                vence = datetime.strptime(last["due_date"], "%Y-%m-%d").date()
                if vence == hoy:
                    vencidos_hoy += 1

        contenido = f"""
=======================================
       RESUMEN GYM - {hoy.strftime("%Y-%m-%d")}
=======================================

👥 MIEMBROS
• Total activos: {len(all_members)}
• Vencen hoy: {vencidos_hoy}

💰 FINANZAS
• Ingresos del mes: ${monto_mes:,}
• Pagos este mes: {len(mes_actual)}

📅 ULTIMOS PAGOS
"""

        for p in mes_actual[-10:]:
            contenido += f"• {p['member_name']}: ${p['amount']} ({p['payment_date']})\n"

        if filepath is None:
            filepath = f"{REPORTS_DIR}/resumen_{hoy.strftime('%Y%m%d')}.txt"

        os.makedirs(os.path.dirname(filepath) or REPORTS_DIR, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(contenido)

        return filepath

    async def export_members_to_csv(self, filepath: str | None = None) -> str:
        """Export active members to CSV file.

        Returns:
            Path to the generated CSV file.
        """
        if filepath is None:
            filepath = f"{REPORTS_DIR}/miembros.csv"

        os.makedirs(os.path.dirname(filepath) or REPORTS_DIR, exist_ok=True)

        hoy = date.today()
        all_members = await self._member_repo.get_all_active()

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Nombre", "Fecha Registro", "Telefono", "Estado", "Ultimo Pago", "Vence"])

            for member in all_members:
                last = await self._payment_repo.get_last_by_member(str(member["_id"]))

                estado = "Activo"
                ult_pago = ""
                vence = ""

                if last:
                    ult_pago = last["payment_date"]
                    vence = last["due_date"]
                    if hoy > datetime.strptime(vence, "%Y-%m-%d").date():
                        estado = "Vencido"

                writer.writerow(
                    [
                        member["name"],
                        member["created_at"].strftime("%Y-%m-%d"),
                        member.get("phone", ""),
                        estado,
                        ult_pago,
                        vence,
                    ]
                )

        return filepath
