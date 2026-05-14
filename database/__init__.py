from __future__ import annotations

import logging
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, OperationFailure

from config import MONGO_URI

logger = logging.getLogger(__name__)

_client: MongoClient[Any] | None = None
_db: Database[Any] | None = None


def get_database() -> Database[Any]:
    global _client, _db
    if _db is None:
        if not MONGO_URI:
            raise ValueError("MONGO_URI no está configurado")
        try:
            _client = MongoClient(
                MONGO_URI,
                maxPoolSize=10,
                minPoolSize=1,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            _db = _client.get_database()
            _db.command("ping")
            logger.info("Conectado a MongoDB")
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"Error conectando a MongoDB: {e}")
            raise
    return _db


def close_database() -> None:
    global _client, _db
    if _client:
        _client.close()
    _client = None
    _db = None


def init_collections() -> None:
    db = get_database()

    existing = set(db.list_collection_names())

    if "members" not in existing:
        db.create_collection("members")
        logger.info("Colección 'members' creada")
    if "payments" not in existing:
        db.create_collection("payments")
        logger.info("Colección 'payments' creada")
    if "admins" not in existing:
        db.create_collection("admins")
        logger.info("Colección 'admins' creada")
    if "audit_log" not in existing:
        db.create_collection("audit_log")
        logger.info("Colección 'audit_log' creada")

    db.members.create_index("name", background=True)
    db.members.create_index([("phone", 1)], background=True, sparse=True)
    db.payments.create_index("member_id", background=True)
    db.payments.create_index("payment_date", background=True)
    db.payments.create_index([("member_id", 1), ("payment_date", -1)], background=True)
    db.admins.create_index("telegram_id", unique=True, background=True)
    db.audit_log.create_index("created_at", background=True, expireAfterSeconds=7776000)

    logger.info("Colecciones e índices inicializados")


def get_collection(name: str) -> Any:
    return get_database()[name]
