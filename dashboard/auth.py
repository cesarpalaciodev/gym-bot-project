from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Any

from fastapi import Request

from config import ADMIN_ID
from database import get_collection

SECRET_KEY = secrets.token_hex(32)
COOKIE_NAME = "gym_session"
SESSION_DURATION = 86400 * 7  # 7 days

_sessions: dict[str, dict[str, Any]] = {}


def _make_token() -> str:
    return secrets.token_urlsafe(32)


def _sign(value: str) -> str:
    return hmac.new(SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()[:12]


def create_session(chat_id: int) -> str:
    token = _make_token()
    expiry = time.time() + SESSION_DURATION
    _sessions[token] = {"chat_id": chat_id, "expiry": expiry}
    return f"{token}.{_sign(token)}"


def get_session_from_cookie(cookie: str | None) -> dict[str, Any] | None:
    if not cookie or "." not in cookie:
        return None
    token, sig = cookie.split(".", 1)
    expected = _sign(token)
    if not hmac.compare_digest(sig, expected):
        return None
    data = _sessions.get(token)
    if not data:
        return None
    if time.time() > data["expiry"]:
        del _sessions[token]
        return None
    return data


async def _verify_admin(chat_id: int) -> dict[str, Any] | None:
    if ADMIN_ID > 0 and chat_id == ADMIN_ID:
        return {"chat_id": chat_id, "name": f"Admin {chat_id}"}
    try:
        admins = await get_collection("admins")
        admin = await admins.find_one({"telegram_id": chat_id})
        if admin:
            return {"chat_id": chat_id, "name": admin.get("name", str(chat_id))}
    except Exception:
        pass
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
        data = get_session_from_cookie(session)

    if data:
        cid = data["chat_id"]

    if cid:
        return await _verify_admin(cid)
    return None
