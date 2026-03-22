from pymongo import MongoClient
from pymongo.database import Database
from datetime import datetime
import logging

from config import MONGO_URI

logger = logging.getLogger(__name__)

_client: MongoClient = None
_db: Database = None


def get_database() -> Database:
    global _client, _db
    if _db is None:
        try:
            _client = MongoClient(MONGO_URI)
            _db = _client.get_database()
            _db.command("ping")
            logger.info("Conexion a MongoDB establecida")
        except Exception as e:
            logger.error(f"Error conectando a MongoDB: {e}")
            raise
    return _db


def close_database() -> None:
    global _client, _db
    if _client:
        _client.close()
        _db = None
        _client = None


def init_collections() -> None:
    db = get_database()
    db.members.create_index("name")
    db.admins.create_index("telegram_id", unique=True)
    db.payments.create_index("member_id")
    db.payments.create_index("payment_date")
    logger.info("Colecciones inicializadas")


def get_collection(name: str):
    return get_database()[name]
