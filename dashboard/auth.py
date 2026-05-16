from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import time
from typing import Any

from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorCollection

from config import ADMIN_ID
from database import get_collection

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("DASHBOARD_SECRET", secrets.token_hex(32))
COOKIE_NAME = "gym_session"
SESSION_DURATION = 86400 * 7

CSRF_TOKEN_NAME = "gym_csrf"


def _make_token() -> str:
    return secrets.token_urlsafe(32)


def _sign(value: str) -> str:
    return hmac.new(SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()[:12]


async def _sessions_col() -> AsyncIOMotorCollection[Any]:
    col = await get_collection("sessions")
    return col


async def create_session(chat_id: int) -> str:
    token = _make_token()
    expiry = time.time() + SESSION_DURATION
    col = await _sessions_col()
    await col.insert_one({"token": token, "chat_id": chat_id, "expiry": expiry})
    return f"{token}.{_sign(token)}"


async def get_session_from_cookie(cookie: str | None) -> dict[str, Any] | None:
    if not cookie or "." not in cookie:
        return None
    token, sig = cookie.split(".", 1)
    expected = _sign(token)
    if not hmac.compare_digest(sig, expected):
        return None
    col = await _sessions_col()
    data = await col.find_one({"token": token, "expiry": {"$gt": time.time()}})
    if data:
        return {"chat_id": data["chat_id"]}
    return None


async def _verify_admin(chat_id: int) -> dict[str, Any] | None:
    if ADMIN_ID > 0 and chat_id == ADMIN_ID:
        return {"chat_id": chat_id, "name": f"Admin {chat_id}"}
    try:
        admins = await get_collection("admins")
        admin = await admins.find_one({"telegram_id": chat_id})
        if admin:
            return {"chat_id": chat_id, "name": admin.get("name", str(chat_id))}
    except Exception:
        logger.exception("Error verifying admin")
    return None


async def get_current_admin(request: Request) -> dict[str, Any] | None:
    session = request.cookies.get(COOKIE_NAME)
    chat_id_q = request.query_params.get("chat_id")
    try:
        cid = int(chat_id_q) if chat_id_q else None
    except (ValueError, TypeError):
        cid = None

    data = None
    if session:
        data = await get_session_from_cookie(session)

    if data:
        cid = data["chat_id"]

    if cid:
        return await _verify_admin(cid)
    return None


def generate_csrf_token() -> str:
    token = secrets.token_urlsafe(32)
    sig = _sign(token)
    return f"{token}.{sig}"


def verify_csrf_token(token: str) -> bool:
    if "." not in token:
        return False
    value, sig = token.split(".", 1)
    expected = _sign(value)
    return hmac.compare_digest(sig, expected)
