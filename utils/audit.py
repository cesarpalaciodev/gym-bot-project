from __future__ import annotations

import logging
from datetime import UTC, datetime

from database import get_collection

logger = logging.getLogger(__name__)


async def log_action(
    telegram_id: int | None,
    username: str | None,
    action: str,
    detail: str | None = None,
    member_name: str | None = None,
) -> None:
    try:
        audit = await get_collection("audit_log")
        await audit.insert_one(
            {
                "telegram_id": telegram_id,
                "username": username,
                "action": action,
                "detail": detail,
                "member_name": member_name,
                "created_at": datetime.now(UTC),
            }
        )
    except Exception as e:
        logger.error(f"Error logging audit: {e}")
