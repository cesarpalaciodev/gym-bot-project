from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from database import get_collection
from services.member_service import MemberService
from services.payment_service import PaymentService
from services.report_service import ReportService

_member_service: MemberService | None = None
_payment_service: PaymentService | None = None
_report_service: ReportService | None = None


async def _get_members_col() -> AsyncIOMotorCollection[dict[str, Any]]:
    return await get_collection("members")


async def _get_payments_col() -> AsyncIOMotorCollection[dict[str, Any]]:
    return await get_collection("payments")


async def get_member_service() -> MemberService:
    global _member_service
    if _member_service is None:
        _member_service = MemberService(await _get_members_col(), await _get_payments_col())
    return _member_service


async def get_payment_service() -> PaymentService:
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService(await _get_members_col(), await _get_payments_col())
    return _payment_service


async def get_report_service() -> ReportService:
    global _report_service
    if _report_service is None:
        _report_service = ReportService(await _get_members_col(), await _get_payments_col())
    return _report_service


def reset_services() -> None:
    global _member_service, _payment_service, _report_service
    _member_service = None
    _payment_service = None
    _report_service = None
