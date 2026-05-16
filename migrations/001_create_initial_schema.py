from __future__ import annotations

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

VERSION = 1
DESCRIPTION = "Create initial collections and indexes"


async def up(db: AsyncIOMotorDatabase[Any]) -> None:
    existing = await db.list_collection_names()

    if "members" not in existing:
        await db.create_collection("members")
        logger.info("Colección 'members' creada")
    if "payments" not in existing:
        await db.create_collection("payments")
        logger.info("Colección 'payments' creada")
    if "admins" not in existing:
        await db.create_collection("admins")
        logger.info("Colección 'admins' creada")
    if "audit_log" not in existing:
        await db.create_collection("audit_log")
        logger.info("Colección 'audit_log' creada")

    await db.members.create_index("name", background=True)
    await db.members.create_index([("phone", 1)], background=True, sparse=True)
    await db.payments.create_index("member_id", background=True)
    await db.payments.create_index("payment_date", background=True)
    await db.payments.create_index([("member_id", 1), ("payment_date", -1)], background=True)
    await db.admins.create_index("telegram_id", unique=True, background=True)
    await db.audit_log.create_index("created_at", background=True, expireAfterSeconds=7776000)

    logger.info("Migration 001 applied: initial schema created")


async def down(db: AsyncIOMotorDatabase[Any]) -> None:
    logger.warning("Rollback 001: dropping collections is destructive")
    for col in ("members", "payments", "admins", "audit_log"):
        if col in await db.list_collection_names():
            await db[col].drop()
            logger.info(f"Colección '{col}' eliminada")
