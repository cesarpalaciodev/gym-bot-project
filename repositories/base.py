"""Base repository class for MongoDB collections."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from motor.motor_asyncio import AsyncIOMotorCollection

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository providing common CRUD operations."""

    def __init__(self, collection: AsyncIOMotorCollection[Any]) -> None:
        self._collection = collection

    @property
    def collection(self) -> AsyncIOMotorCollection[Any]:
        return self._collection

    async def find_one(self, filter_dict: dict[str, Any]) -> dict[str, Any] | None:
        """Find a single document matching the filter."""
        return await self._collection.find_one(filter_dict)

    async def find_many(
        self,
        filter_dict: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Find multiple documents matching the filter."""
        cursor = self._collection.find(filter_dict or {})
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=None)

    async def insert_one(self, document: dict[str, Any]) -> str:
        """Insert a document and return its ID."""
        result = await self._collection.insert_one(document)
        return str(result.inserted_id)

    async def update_one(
        self,
        filter_dict: dict[str, Any],
        update_dict: dict[str, Any],
    ) -> bool:
        """Update a single document. Returns True if modified."""
        result = await self._collection.update_one(filter_dict, update_dict)
        return result.modified_count > 0

    async def delete_one(self, filter_dict: dict[str, Any]) -> bool:
        """Delete a single document. Returns True if deleted."""
        result = await self._collection.delete_one(filter_dict)
        return result.deleted_count > 0

    async def delete_many(self, filter_dict: dict[str, Any]) -> int:
        """Delete multiple documents. Returns count deleted."""
        result = await self._collection.delete_many(filter_dict)
        return result.deleted_count

    async def count(self, filter_dict: dict[str, Any] | None = None) -> int:
        """Count documents matching filter."""
        return await self._collection.count_documents(filter_dict or {})
