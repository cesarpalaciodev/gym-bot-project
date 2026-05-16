"""Audit repository for MongoDB operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from repositories.base import BaseRepository


class AuditRepository(BaseRepository[Any]):
    """Repository for audit log collection operations."""

    def __init__(self, collection: AsyncIOMotorCollection[Any]) -> None:
        super().__init__(collection)

    async def log_action(
        self,
        telegram_id: int,
        action: str,
        detail: str | None = None,
    ) -> str:
        """Log an action to the audit collection."""
        audit_entry = {
            "telegram_id": telegram_id,
            "action": action,
            "detail": detail,
            "created_at": datetime.utcnow(),
        }
        return await self.insert_one(audit_entry)

    async def get_recent_actions(
        self,
        telegram_id: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get recent audit entries, optionally filtered by user."""
        filter_dict = {}
        if telegram_id:
            filter_dict["telegram_id"] = telegram_id
        return await self.find_many(
            filter_dict=filter_dict,
            sort=[("created_at", -1)],
            limit=limit,
        )
