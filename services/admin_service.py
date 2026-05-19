"""Admin service for managing administrators."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from models.admin import Admin
from repositories.admin_repository import AdminRepository

logger = logging.getLogger(__name__)


@dataclass
class AdminInfo:
    """Admin information for display."""

    telegram_id: int
    name: str
    role: str


class AdminService:
    """Service for admin management operations."""

    def __init__(self, admin_repo: AdminRepository) -> None:
        self._admin_repo = admin_repo

    async def is_super_admin(self, telegram_id: int) -> bool:
        """Check if user is a super admin."""
        admin = await self._admin_repo.get_by_telegram_id(telegram_id)
        return admin is not None and admin.get("role") == "super_admin"

    async def is_admin(self, telegram_id: int) -> bool:
        """Check if user is any type of admin."""
        admin = await self._admin_repo.get_by_telegram_id(telegram_id)
        return admin is not None

    async def get_admin_role(self, telegram_id: int) -> str | None:
        """Get admin role for a user."""
        admin = await self._admin_repo.get_by_telegram_id(telegram_id)
        return admin.get("role") if admin else None

    async def list_all_admins(self) -> list[AdminInfo]:
        """List all administrators."""
        admins = await self._admin_repo.list_all()
        return [
            AdminInfo(
                telegram_id=a["telegram_id"],
                name=a["name"],
                role=a["role"],
            )
            for a in admins
        ]

    async def add_admin(self, telegram_id: int, name: str, role: str = "admin") -> bool:
        """Add a new admin.

        Returns:
            True if added successfully, False if already exists.
        """
        if await self._admin_repo.exists_by_telegram_id(telegram_id):
            return False

        admin = Admin(telegram_id=telegram_id, name=name, role=role)
        await self._admin_repo.create_admin(admin)
        return True

    async def remove_admin(self, telegram_id: int) -> bool:
        """Remove an admin.

        Returns:
            True if removed, False if not found.
        """
        return await self._admin_repo.delete_by_telegram_id(telegram_id)

    async def change_role(self, telegram_id: int, new_role: str) -> bool:
        """Change admin role.

        Returns:
            True if changed, False if admin not found.
        """
        if not await self._admin_repo.exists_by_telegram_id(telegram_id):
            return False

        await self._admin_repo.update_role(telegram_id, new_role)
        return True

    async def validate_telegram_id(self, text: str) -> int | None:
        """Validate and parse telegram ID from text.

        Returns:
            Parsed ID or None if invalid.
        """
        try:
            return int(text.strip())
        except ValueError:
            return None

    async def get_admin_display_info(self, telegram_id: int) -> AdminInfo | None:
        """Get admin info for display."""
        admin = await self._admin_repo.get_by_telegram_id(telegram_id)
        if not admin:
            return None
        return AdminInfo(
            telegram_id=admin["telegram_id"],
            name=admin["name"],
            role=admin["role"],
        )
