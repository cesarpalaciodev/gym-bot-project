"""Admin repository for MongoDB operations."""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from models.admin import Admin
from repositories.base import BaseRepository


class AdminRepository(BaseRepository[Admin]):
    """Repository for admin collection operations."""

    def __init__(self, collection: AsyncIOMotorCollection[Any]) -> None:
        super().__init__(collection)

    async def get_by_telegram_id(self, telegram_id: int) -> dict[str, Any] | None:
        """Get admin by Telegram ID."""
        return await self.find_one({"telegram_id": telegram_id})

    async def create_admin(self, admin: Admin) -> str:
        """Create a new admin record."""
        return await self.insert_one(admin.to_dict())

    async def delete_by_telegram_id(self, telegram_id: int) -> bool:
        """Delete admin by Telegram ID."""
        return await self.delete_one({"telegram_id": telegram_id})

    async def update_role(self, telegram_id: int, new_role: str) -> bool:
        """Update admin role."""
        return await self.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"role": new_role}},
        )

    async def list_all(self) -> list[dict[str, Any]]:
        """List all admins."""
        return await self.find_many()

    async def exists_by_telegram_id(self, telegram_id: int) -> bool:
        """Check if admin exists."""
        count = await self.count({"telegram_id": telegram_id})
        return count > 0
