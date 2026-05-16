from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dashboard.auth import (
    _sign,
    _verify_admin,
    create_session,
    get_current_admin,
    get_session_from_cookie,
)


@pytest.fixture(autouse=True)
def patch_sessions_col(mock_collection):
    mock_collection.find_one = AsyncMock(return_value=None)
    with patch("dashboard.auth.get_collection", AsyncMock(return_value=mock_collection)):
        yield mock_collection


class TestVerifyAdmin:
    @patch("dashboard.auth.ADMIN_ID", 12345)
    async def test_matches_admin_id(self):
        result = await _verify_admin(12345)
        assert result is not None
        assert result["chat_id"] == 12345

    @patch("dashboard.auth.ADMIN_ID", 12345)
    async def test_does_not_match(self):
        result = await _verify_admin(99999)
        assert result is None

    @patch("dashboard.auth.ADMIN_ID", 0)
    async def test_admin_id_zero_fallback_to_db(self):
        result = await _verify_admin(99999)
        assert result is None


class TestCreateSession:
    @patch("dashboard.auth.ADMIN_ID", 12345)
    async def test_create_and_verify_session(self, patch_sessions_col):
        token = await create_session(12345)
        assert "." in token
        payload, sig = token.split(".")
        expected_sig = _sign(payload)
        assert sig == expected_sig[:12]

    @patch("dashboard.auth.ADMIN_ID", 12345)
    async def test_session_expires(self, monkeypatch, patch_sessions_col):
        import time as time_module

        mock_col = patch_sessions_col
        mock_col.find_one = AsyncMock(return_value=None)
        original_time = time_module.time
        token = await create_session(12345)
        monkeypatch.setattr("dashboard.auth.time.time", lambda: original_time() + 86400 * 8)
        result = await get_session_from_cookie(token)
        assert result is None


class TestGetSessionFromCookie:
    @patch("dashboard.auth.ADMIN_ID", 12345)
    async def test_valid_session(self, patch_sessions_col):
        mock_col = patch_sessions_col
        mock_col.find_one = AsyncMock(return_value={"token": "test", "chat_id": 12345, "expiry": 9999999999})
        token = "valid_token." + _sign("valid_token")
        data = await get_session_from_cookie(token)
        assert data is not None
        assert data["chat_id"] == 12345

    async def test_none_cookie(self, patch_sessions_col):
        assert await get_session_from_cookie(None) is None

    async def test_malformed_cookie(self, patch_sessions_col):
        assert await get_session_from_cookie("invalid") is None

    async def test_tampered_cookie(self, patch_sessions_col):
        token = "payload." + _sign("payload")
        payload, sig = token.split(".", 1)
        tampered = f"{payload}x.{sig}"
        result = await get_session_from_cookie(tampered)
        assert result is None


class TestGetCurrentAdmin:
    @patch("dashboard.auth.ADMIN_ID", 12345)
    async def test_with_valid_session(self, patch_sessions_col):
        mock_col = patch_sessions_col
        mock_col.find_one = AsyncMock(return_value={"token": "test", "chat_id": 12345, "expiry": 9999999999})
        token = "valid_token." + _sign("valid_token")
        request = MagicMock()
        request.cookies.get.return_value = token
        request.query_params.get.return_value = None
        result = await get_current_admin(request)
        assert result is not None
        assert result["chat_id"] == 12345

    async def test_without_session(self, patch_sessions_col):
        request = MagicMock()
        request.cookies.get.return_value = None
        request.query_params.get.return_value = None
        result = await get_current_admin(request)
        assert result is None

    @patch("dashboard.auth.ADMIN_ID", 12345)
    async def test_with_chat_id_query_param(self, patch_sessions_col):
        request = MagicMock()
        request.cookies.get.return_value = None
        request.query_params.get.return_value = "12345"
        result = await get_current_admin(request)
        assert result is not None
        assert result["chat_id"] == 12345

    async def test_with_invalid_chat_id_query_param(self, patch_sessions_col):
        request = MagicMock()
        request.cookies.get.return_value = None
        request.query_params.get.return_value = "abc"
        result = await get_current_admin(request)
        assert result is None
