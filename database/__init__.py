from __future__ import annotations

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, OperationFailure

from config import MONGO_URI

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient[Any] | None = None
_db: AsyncIOMotorDatabase[Any] | None = None


async def get_database() -> AsyncIOMotorDatabase[Any]:
    global _client, _db
    if _db is None:
        if not MONGO_URI:
            raise ValueError("MONGO_URI no está configurado")
        try:
            _client = AsyncIOMotorClient(
                MONGO_URI,
                maxPoolSize=10,
                minPoolSize=1,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            _db = _client.get_database()
            await _db.command("ping")
            logger.info("Conectado a MongoDB (Motor async)")
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"Error conectando a MongoDB: {e}")
            raise
    return _db


async def close_database() -> None:
    global _client, _db
    if _client:
        _client.close()
    _client = None
    _db = None


async def init_collections() -> None:
    db = await get_database()

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
    if "sessions" not in existing:
        await db.create_collection("sessions")
        logger.info("Colección 'sessions' creada")

    await db.members.create_index("name", background=True)
    await db.members.create_index([("phone", 1)], background=True, sparse=True)
    await db.members.create_index([("active", 1)], background=True)
    await db.payments.create_index("member_id", background=True)
    await db.payments.create_index("payment_date", background=True)
    await db.payments.create_index([("member_id", 1), ("payment_date", -1)], background=True)
    await db.admins.create_index("telegram_id", unique=True, background=True)
    await db.audit_log.create_index("created_at", background=True, expireAfterSeconds=7776000)
    await db.rate_limits.create_index("created_at", background=True, expireAfterSeconds=10)
    await db.sessions.create_index("token", unique=True, background=True)
    await db.sessions.create_index("expiry", expireAfterSeconds=0, background=True)

    logger.info("Colecciones e índices inicializados")


async def get_collection(name: str) -> AsyncIOMotorCollection[Any]:
    db = await get_database()
    return db[name]
