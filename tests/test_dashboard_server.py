from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_find_chain(return_value: list | None = None) -> MagicMock:
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=return_value or [])
    cursor.skip = MagicMock(return_value=cursor)
    chain = MagicMock()
    chain.sort.return_value = chain
    chain.limit.return_value = cursor
    chain.skip.return_value = chain
    chain.to_list = AsyncMock(return_value=return_value or [])
    return chain


def _make_agg_chain(return_value: list | None = None) -> MagicMock:
    chain = MagicMock()
    chain.to_list = AsyncMock(return_value=return_value or [])
    return chain


@pytest.fixture
def mock_db():
    members = AsyncMock()
    members.find_one = AsyncMock(return_value={"_id": "1", "name": "Test"})
    members.find = MagicMock()
    members.find.return_value = _make_find_chain(
        [{"_id": "1", "name": "Juan", "phone": "123"}, {"_id": "2", "name": "Maria", "phone": "456"}]
    )
    members.count_documents = AsyncMock(return_value=5)
    members.insert_one = AsyncMock()
    members.delete_one = AsyncMock()
    members.delete_many = AsyncMock()
    members.update_one = AsyncMock()

    payments = AsyncMock()
    payments.find_one = AsyncMock(return_value={"due_date": "2026-06-01", "payment_date": "2026-05-01"})
    payments.find = MagicMock()
    payments.find.return_value = _make_find_chain(
        [
            {
                "_id": "p1",
                "member_name": "Juan",
                "amount": 500,
                "payment_date": "2026-05-01",
                "plan": "Mensual",
                "due_date": "2026-06-01",
            }
        ]
    )
    payments.aggregate = MagicMock()
    payments.aggregate.return_value = _make_agg_chain([{"total": 1500}])
    payments.count_documents = AsyncMock(return_value=25)

    admins = AsyncMock()
    admins.find_one = AsyncMock(return_value={"telegram_id": 12345, "role": "admin"})

    sessions = AsyncMock()
    sessions.find_one = AsyncMock(return_value={"chat_id": 12345, "expiry": 9999999999})

    def get_collection_side_effect(name: str):
        if name == "members":
            return members
        if name == "payments":
            return payments
        if name == "admins":
            return admins
        if name == "sessions":
            return sessions
        return AsyncMock()

    return {
        "members": members,
        "payments": payments,
        "admins": admins,
        "sessions": sessions,
    }, get_collection_side_effect


@pytest.fixture
def client(mock_db):
    db_dict, side_effect = mock_db
    with (
        patch("dashboard.server.get_collection", side_effect=side_effect),
        patch("dashboard.auth.get_collection", side_effect=side_effect),
        patch("dashboard.auth.ADMIN_ID", 12345),
    ):
        from dashboard.server import app

        with TestClient(app) as c:
            yield c


class TestLogin:
    def test_login_page_returns_form_when_unauthenticated(self, client: TestClient) -> None:
        resp = client.get("/login")
        assert resp.status_code == 200
        assert "login" in resp.text.lower()

    def test_login_post_redirects_on_success(self, client: TestClient) -> None:
        with patch("dashboard.server._verify_admin") as mock_verify:
            mock_verify.return_value = {"chat_id": 12345, "name": "Admin"}
            resp = client.post("/login", data={"chat_id": "12345"}, follow_redirects=False)
            assert resp.status_code == 303
            assert resp.headers["location"] == "/"

    def test_login_post_returns_error_on_failure(self, client: TestClient) -> None:
        with patch("dashboard.server._verify_admin") as mock_verify:
            mock_verify.return_value = None
            resp = client.post("/login", data={"chat_id": "99999"})
            assert resp.status_code == 200
            assert "no autorizado" in resp.text.lower()

    def test_login_post_rejects_missing_chat_id(self, client: TestClient) -> None:
        resp = client.post("/login", data={})
        assert resp.status_code == 422


class TestLogout:
    def test_logout_redirects_and_deletes_cookie(self, client: TestClient) -> None:
        resp = client.get("/logout", follow_redirects=False)
        assert resp.status_code == 303
        assert resp.headers["location"] == "/login"


class TestIndex:
    def test_redirects_when_unauthenticated(self, client: TestClient) -> None:
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 303

    def test_returns_dashboard_when_authenticated(self, client: TestClient) -> None:
        with patch("dashboard.server.get_current_admin") as mock_admin:
            mock_admin.return_value = {"chat_id": 12345, "name": "Admin"}
            resp = client.get("/")
            assert resp.status_code == 200
            assert "Dashboard" in resp.text


class TestStatsPage:
    def test_returns_stats_page(self, client: TestClient) -> None:
        with patch("dashboard.server.get_current_admin") as mock_admin:
            mock_admin.return_value = {"chat_id": 12345, "name": "Admin"}
            resp = client.get("/dashboard/stats")
            assert resp.status_code == 200

    def test_redirects_when_unauthenticated(self, client: TestClient) -> None:
        resp = client.get("/dashboard/stats", follow_redirects=False)
        assert resp.status_code == 303


class TestMembersPage:
    def test_returns_members_page(self, client: TestClient) -> None:
        with patch("dashboard.server.get_current_admin") as mock_admin:
            mock_admin.return_value = {"chat_id": 12345, "name": "Admin"}
            resp = client.get("/dashboard/members")
            assert resp.status_code == 200

    def test_redirects_when_unauthenticated(self, client: TestClient) -> None:
        resp = client.get("/dashboard/members", follow_redirects=False)
        assert resp.status_code == 303


class TestPaymentsPage:
    def test_returns_payments_page(self, client: TestClient) -> None:
        with patch("dashboard.server.get_current_admin") as mock_admin:
            mock_admin.return_value = {"chat_id": 12345, "name": "Admin"}
            resp = client.get("/dashboard/payments")
            assert resp.status_code == 200

    def test_supports_pagination(self, client: TestClient) -> None:
        with patch("dashboard.server.get_current_admin") as mock_admin:
            mock_admin.return_value = {"chat_id": 12345, "name": "Admin"}
            resp = client.get("/dashboard/payments?page=2")
            assert resp.status_code == 200


class TestHealthPage:
    def test_returns_health_page(self, client: TestClient) -> None:
        with patch("dashboard.server.get_current_admin") as mock_admin:
            mock_admin.return_value = {"chat_id": 12345, "name": "Admin"}
            resp = client.get("/dashboard/health")
            assert resp.status_code == 200

    def test_shows_db_status(self, client: TestClient) -> None:
        with patch("dashboard.server.get_current_admin") as mock_admin:
            mock_admin.return_value = {"chat_id": 12345, "name": "Admin"}
            resp = client.get("/dashboard/health")
            assert "Connected" in resp.text or "Disconnected" in resp.text


class TestApiStats:
    def test_unauthorized_returns_error(self, client: TestClient) -> None:
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_returns_stats_json(self, client: TestClient, mock_db) -> None:
        db_dict, _ = mock_db
        db_dict["admins"].find_one = AsyncMock(return_value={"telegram_id": 12345, "role": "admin"})
        db_dict["sessions"].find_one = AsyncMock(return_value={"chat_id": 12345, "expiry": 9999999999})
        with patch("dashboard.auth._sign", return_value="testsig"):
            client.cookies.set("gym_session", "testtoken.testsig")
            resp = client.get("/api/stats")
            assert resp.status_code == 200
            data = resp.json()
            assert "active_members" in data
            assert "monthly_income" in data


class TestApiMembers:
    def test_unauthorized_returns_error(self, client: TestClient) -> None:
        resp = client.get("/api/members")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_returns_members_json(self, client: TestClient, mock_db) -> None:
        db_dict, _ = mock_db
        db_dict["admins"].find_one = AsyncMock(return_value={"telegram_id": 12345, "role": "admin"})
        db_dict["sessions"].find_one = AsyncMock(return_value={"chat_id": 12345, "expiry": 9999999999})
        with patch("dashboard.auth._sign", return_value="testsig"):
            client.cookies.set("gym_session", "testtoken.testsig")
            resp = client.get("/api/members")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)


class TestApiPayments:
    def test_unauthorized_returns_error(self, client: TestClient) -> None:
        resp = client.get("/api/payments")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_returns_payments_json(self, client: TestClient, mock_db) -> None:
        db_dict, _ = mock_db
        db_dict["admins"].find_one = AsyncMock(return_value={"telegram_id": 12345, "role": "admin"})
        db_dict["sessions"].find_one = AsyncMock(return_value={"chat_id": 12345, "expiry": 9999999999})
        with patch("dashboard.auth._sign", return_value="testsig"):
            client.cookies.set("gym_session", "testtoken.testsig")
            resp = client.get("/api/payments")
            assert resp.status_code == 200
            data = resp.json()
            assert "total" in data
            assert "data" in data

    def test_payments_pagination(self, client: TestClient, mock_db) -> None:
        db_dict, _ = mock_db
        db_dict["admins"].find_one = AsyncMock(return_value={"telegram_id": 12345, "role": "admin"})
        db_dict["sessions"].find_one = AsyncMock(return_value={"chat_id": 12345, "expiry": 9999999999})
        with patch("dashboard.auth._sign", return_value="testsig"):
            client.cookies.set("gym_session", "testtoken.testsig")
            resp = client.get("/api/payments?page=1&limit=10")
            assert resp.status_code == 200
            data = resp.json()
            assert data["limit"] == 10


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
