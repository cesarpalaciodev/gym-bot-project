from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import reset_services


@pytest.fixture(autouse=True)
def _reset_services():
    reset_services()
    yield


@pytest.fixture
def mock_collection_pair():
    members = AsyncMock()
    members.find = MagicMock()
    members.find.return_value.to_list = AsyncMock(return_value=[])
    members.find_one = AsyncMock()

    payments = AsyncMock()
    payments.find = MagicMock()
    payments.find.return_value.to_list = AsyncMock(return_value=[])
    payments.find_one = AsyncMock()

    return members, payments


@pytest.fixture
def patch_collections(mock_collection_pair):
    members_mock, payments_mock = mock_collection_pair

    async def side_effect(name: str):
        if name == "members":
            return members_mock
        return payments_mock

    with patch("services.factory.get_collection", side_effect=side_effect):
        yield members_mock, payments_mock


@pytest.fixture
def fixed_today():
    today = date(2026, 5, 15)
    with patch("handlers.notifications.date") as mock_notif_date:
        mock_notif_date.today.return_value = today
        with patch("utils.dates.date") as mock_utils_date:
            mock_utils_date.today.return_value = today
            yield today


@pytest.fixture
def patch_group_id():
    with patch("handlers.notifications.GROUP_ID", "-100123"):
        yield


@pytest.fixture
def mock_send_message(mock_context):
    mock_context.bot.send_message = AsyncMock()
    yield mock_context.bot.send_message


class TestNotificacion5am:
    async def test_skips_when_group_id_not_set(self, mock_context, patch_collections, caplog):
        with patch("handlers.notifications.GROUP_ID", ""):
            from handlers.notifications import notificacion_5am

            await notificacion_5am(mock_context)
        mock_context.bot.send_message.assert_not_called()

    async def test_sends_empty_message_when_no_active_members(
        self, mock_context, patch_collections, fixed_today, patch_group_id, mock_send_message
    ):
        members_mock, _ = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[])
        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        mock_send_message.assert_awaited_once()
        text = mock_send_message.call_args[1]["text"]
        assert "No hay miembros registrados" in text

    async def test_all_members_active(
        self, mock_context, patch_collections, fixed_today, patch_group_id, mock_send_message
    ):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[{"_id": "m1", "name": "Juan", "active": True}])
        payments_mock.find_one = AsyncMock(return_value={"member_id": "m1", "due_date": "2026-05-20", "amount": 500})
        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_send_message.call_args[1]["text"]
        assert "ACTIVOS: 1" in text
        assert "VENCIDOS" not in text
        assert "GRACIA" not in text

    async def test_members_expiring_today(self, mock_context, patch_collections, fixed_today, patch_group_id):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[{"_id": "m1", "name": "Ana", "active": True}])
        payments_mock.find_one = AsyncMock(return_value={"member_id": "m1", "due_date": "2026-05-15", "amount": 500})
        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_context.bot.send_message.call_args[1]["text"]
        assert "VENCEN HOY" in text
        assert "Ana" in text
        assert "ACTIVOS: 0" in text

    async def test_members_in_grace_period(self, mock_context, patch_collections, fixed_today, patch_group_id):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(
            return_value=[{"_id": "m1", "name": "Pedro", "active": True}]
        )
        payments_mock.find_one = AsyncMock(return_value={"member_id": "m1", "due_date": "2026-05-12", "amount": 500})
        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_context.bot.send_message.call_args[1]["text"]
        assert "EN GRACIA" in text
        assert "Pedro" in text
        assert "3 dias" in text

    async def test_overdue_members(self, mock_context, patch_collections, fixed_today, patch_group_id):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[{"_id": "m1", "name": "Luis", "active": True}])
        payments_mock.find_one = AsyncMock(return_value={"member_id": "m1", "due_date": "2026-05-08", "amount": 500})
        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_context.bot.send_message.call_args[1]["text"]
        assert "VENCIDOS" in text
        assert "Luis" in text
        assert "7 dias" in text

    async def test_member_without_payment_recorded_as_overdue(
        self, mock_context, patch_collections, fixed_today, patch_group_id
    ):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(
            return_value=[{"_id": "m1", "name": "Carlos", "active": True}]
        )
        payments_mock.find_one = AsyncMock(return_value=None)
        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_context.bot.send_message.call_args[1]["text"]
        assert "VENCIDOS" in text
        assert "Carlos" in text
        assert "0 dias" in text

    async def test_mixed_members_status(
        self, mock_context, patch_collections, fixed_today, patch_group_id, mock_send_message
    ):
        members_mock, payments_mock = patch_collections
        members_data = [
            {"_id": "m1", "name": "Ana", "active": True},
            {"_id": "m2", "name": "Beto", "active": True},
            {"_id": "m3", "name": "Carla", "active": True},
            {"_id": "m4", "name": "Dave", "active": True},
            {"_id": "m5", "name": "Eva", "active": True},
        ]
        members_mock.find.return_value.to_list = AsyncMock(return_value=members_data)

        payment_map = {
            "m1": {"member_id": "m1", "due_date": "2026-05-20", "amount": 500},
            "m2": {"member_id": "m2", "due_date": "2026-05-15", "amount": 500},
            "m3": {"member_id": "m3", "due_date": "2026-05-12", "amount": 500},
            "m4": {"member_id": "m4", "due_date": "2026-05-08", "amount": 500},
        }

        async def find_one_side(query, sort=None):
            return payment_map.get(query.get("member_id"))

        payments_mock.find_one.side_effect = find_one_side

        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_send_message.call_args[1]["text"]
        assert "ACTIVOS: 1" in text
        assert "VENCEN HOY" in text and "Beto" in text
        assert "EN GRACIA" in text and "Carla" in text
        assert "VENCIDOS" in text and "Dave" in text and "Eva" in text

    async def test_sends_to_correct_group_id(self, mock_context, patch_collections, fixed_today, mock_send_message):
        members_mock, _ = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[])
        with patch("handlers.notifications.GROUP_ID", "-100999"):
            from handlers.notifications import notificacion_5am

            await notificacion_5am(mock_context)
        mock_send_message.assert_awaited_once()
        assert mock_send_message.call_args[1]["chat_id"] == "-100999"

    async def test_logs_error_when_send_fails(
        self, mock_context, patch_collections, fixed_today, patch_group_id, caplog
    ):
        members_mock, _ = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[])
        mock_context.bot.send_message = AsyncMock(side_effect=Exception("Network error"))
        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        assert any("Error" in rec.message for rec in caplog.records)

    async def test_notificacion_includes_date_header(
        self, mock_context, patch_collections, fixed_today, patch_group_id, mock_send_message
    ):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[{"_id": "m1", "name": "Juan", "active": True}])
        payments_mock.find_one = AsyncMock(return_value={"member_id": "m1", "due_date": "2026-05-20", "amount": 500})
        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_send_message.call_args[1]["text"]
        assert "RECORDATORIO MATUTINO" in text
        assert "2026-05-15" in text
