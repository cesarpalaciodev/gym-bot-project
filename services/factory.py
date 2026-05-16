"""Service factory with dependency injection."""

from __future__ import annotations

from typing import Any

from database import get_collection
from repositories.admin_repository import AdminRepository
from repositories.member_repository import MemberRepository
from repositories.payment_repository import PaymentRepository
from services.admin_service import AdminService
from services.export_service import ExportService
from services.member_service import MemberService
from services.notification_service import NotificationService
from services.payment_service import PaymentService
from services.report_service import ReportService
from services.stats_service import StatsService

# Singleton instances
_member_service: MemberService | None = None
_payment_service: PaymentService | None = None
_report_service: ReportService | None = None
_export_service: ExportService | None = None
_stats_service: StatsService | None = None
_notification_service: NotificationService | None = None
_admin_service: AdminService | None = None


async def _get_members_col() -> Any:
    return await get_collection("members")


async def _get_payments_col() -> Any:
    return await get_collection("payments")


async def _get_admins_col() -> Any:
    return await get_collection("admins")


async def get_member_service() -> MemberService:
    """Get or create MemberService singleton."""
    global _member_service
    if _member_service is None:
        members_col = await _get_members_col()
        payments_col = await _get_payments_col()
        _member_service = MemberService(members_col, payments_col)
    return _member_service


async def get_payment_service() -> PaymentService:
    """Get or create PaymentService singleton."""
    global _payment_service
    if _payment_service is None:
        members_col = await _get_members_col()
        payments_col = await _get_payments_col()
        _payment_service = PaymentService(members_col, payments_col)
    return _payment_service


async def get_report_service() -> ReportService:
    """Get or create ReportService singleton."""
    global _report_service
    if _report_service is None:
        members_col = await _get_members_col()
        payments_col = await _get_payments_col()
        _report_service = ReportService(members_col, payments_col)
    return _report_service


async def get_export_service() -> ExportService:
    """Get or create ExportService singleton."""
    global _export_service
    if _export_service is None:
        members_col = await _get_members_col()
        payments_col = await _get_payments_col()
        member_repo = MemberRepository(members_col)
        payment_repo = PaymentRepository(payments_col)
        _export_service = ExportService(member_repo, payment_repo)
    return _export_service


async def get_stats_service() -> StatsService:
    """Get or create StatsService singleton."""
    global _stats_service
    if _stats_service is None:
        members_col = await _get_members_col()
        payments_col = await _get_payments_col()
        member_repo = MemberRepository(members_col)
        payment_repo = PaymentRepository(payments_col)
        _stats_service = StatsService(member_repo, payment_repo)
    return _stats_service


async def get_notification_service() -> NotificationService:
    """Get or create NotificationService singleton."""
    global _notification_service
    if _notification_service is None:
        members_col = await _get_members_col()
        payments_col = await _get_payments_col()
        member_repo = MemberRepository(members_col)
        payment_repo = PaymentRepository(payments_col)
        _notification_service = NotificationService(member_repo, payment_repo)
    return _notification_service


async def get_admin_service() -> AdminService:
    """Get or create AdminService singleton."""
    global _admin_service
    if _admin_service is None:
        admins_col = await _get_admins_col()
        admin_repo = AdminRepository(admins_col)
        _admin_service = AdminService(admin_repo)
    return _admin_service


def reset_services() -> None:
    """Reset all service singletons (useful for testing)."""
    global _member_service, _payment_service, _report_service
    global _export_service, _stats_service, _notification_service, _admin_service
    _member_service = None
    _payment_service = None
    _report_service = None
    _export_service = None
    _stats_service = None
    _notification_service = None
    _admin_service = None
