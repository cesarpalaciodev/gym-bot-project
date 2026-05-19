"""Payment repository for MongoDB operations."""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from models.payment import Payment
from repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Repository for payment collection operations."""

    def __init__(self, collection: AsyncIOMotorCollection[Any]) -> None:
        super().__init__(collection)

    async def get_last_by_member(self, member_id: str) -> dict[str, Any] | None:
        """Get most recent payment for a member."""
        cursor = self._collection.find({"member_id": member_id}).sort("payment_date", -1).limit(1)
        results = await cursor.to_list(length=1)
        return results[0] if results else None

    async def get_history_by_member(
        self,
        member_id: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get payment history for a member, most recent first."""
        cursor = self._collection.find({"member_id": member_id}).sort("payment_date", -1)
        if limit:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=None)

    async def create_payment(self, payment: Payment) -> str:
        """Create a new payment record."""
        return await self.insert_one(payment.to_dict())

    async def get_income_for_period(
        self,
        start_date: str,
        end_date: str,
    ) -> int:
        """Calculate total income for a date range."""
        pipeline: list[dict[str, Any]] = [
            {"$match": {"payment_date": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]
        cursor = self._collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0]["total"] if result else 0

    async def get_payments_for_period(
        self,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        """Get all payments within a date range."""
        return await self.find_many(
            {"payment_date": {"$gte": start_date, "$lte": end_date}},
            sort=[("payment_date", -1)],
        )

    async def delete_by_member(self, member_id: str) -> int:
        """Delete all payments for a member (returns count)."""
        return await self.delete_many({"member_id": member_id})

    async def get_all_payments(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get all payments ordered by date descending."""
        return await self.find_many(
            sort=[("payment_date", -1)],
            limit=limit,
        )
