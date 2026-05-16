"""Member repository for MongoDB operations."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from models.member import Member
from repositories.base import BaseRepository


class MemberRepository(BaseRepository[Member]):
    """Repository for member collection operations."""

    def __init__(self, collection: AsyncIOMotorCollection[Any]) -> None:
        super().__init__(collection)

    async def get_by_id(self, member_id: str) -> dict[str, Any] | None:
        """Get member by ObjectId."""
        return await self.find_one({"_id": ObjectId(member_id)})

    async def get_by_name(self, name: str, active_only: bool = True) -> dict[str, Any] | None:
        """Get member by exact name match."""
        filter_dict = {"name": name}
        if active_only:
            filter_dict["active"] = True
        return await self.find_one(filter_dict)

    async def search_by_name(self, name: str) -> list[dict[str, Any]]:
        """Search members by partial name match."""
        return await self.find_many({"name": {"$regex": name, "$options": "i"}, "active": True})

    async def get_all_active(self) -> list[dict[str, Any]]:
        """Get all active members."""
        return await self.find_many({"active": True})

    async def create_member(self, member: Member) -> str:
        """Create a new member and return ID."""
        return await self.insert_one(member.to_dict())

    async def soft_delete(self, member_id: str) -> bool:
        """Soft delete by setting active=False."""
        return await self.update_one(
            {"_id": ObjectId(member_id)},
            {"$set": {"active": False}},
        )

    async def hard_delete(self, member_id: str) -> bool:
        """Permanently delete member."""
        return await self.delete_one({"_id": ObjectId(member_id)})

    async def update_phone(self, member_id: str, phone: str) -> bool:
        """Update member phone number."""
        return await self.update_one(
            {"_id": ObjectId(member_id)},
            {"$set": {"phone": phone}},
        )

    async def exists_by_name(self, name: str) -> bool:
        """Check if member exists by name."""
        count = await self.count({"name": name, "active": True})
        return count > 0
