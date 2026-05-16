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
    with (
        patch("handlers.stats.date") as mock_stats_date,
        patch("utils.dates.date") as mock_utils_date,
    ):
        mock_stats_date.today.return_value = today
        mock_utils_date.today.return_value = today
        yield today


def make_update(text: str = "") -> MagicMock:
    update = MagicMock()
    update.message = MagicMock()
    update.message.text = text
    update.message.reply_text = AsyncMock()
    update.effective_user.id = 12345
    update.effective_chat = MagicMock()
    update.effective_chat.type = "private"
    return update


@pytest.mark.usefixtures("patch_collections", "fixed_today")
class TestMenuStats:
    async def test_menu_stats_replies(self, mock_update, mock_context):
        from handlers.stats import menu_stats

        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        await menu_stats(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once()

    async def test_menu_stats_no_message(self, mock_update, mock_context):
        from handlers.stats import menu_stats

        mock_update.message = None
        await menu_stats(mock_update, mock_context)


@pytest.mark.usefixtures("patch_collections", "fixed_today")
class TestMiembrosActivos:
    async def test_active_members_stats(self, mock_collection_pair):
        members_mock, payments_mock = mock_collection_pair
        members_mock.find.return_value.to_list = AsyncMock(
            return_value=[
                {"_id": "1", "name": "Juan"},
                {"_id": "2", "name": "Maria"},
            ]
        )
        payments_mock.find_one = AsyncMock(
            side_effect=[
                {"due_date": "2026-06-15", "payment_date": "2026-05-01"},
                {"due_date": "2026-05-10", "payment_date": "2026-04-01"},
            ]
        )

        from handlers.stats import miembros_activos

        update = make_update()
        context = MagicMock()
        await miembros_activos(update, context)
        update.message.reply_text.assert_awaited_once()
        msg = update.message.reply_text.call_args[0][0]
        assert "Total: 2" in msg

    async def test_no_message_returns(self, mock_collection_pair):
        from handlers.stats import miembros_activos

        update = MagicMock()
        update.message = None
        context = MagicMock()
        await miembros_activos(update, context)

    async def test_db_error_returns_error_message(self, mock_collection_pair):
        members_mock, _ = mock_collection_pair
        members_mock.find.side_effect = Exception("DB error")

        from handlers.stats import miembros_activos

        update = make_update()
        context = MagicMock()
        await miembros_activos(update, context)
        msg = update.message.reply_text.call_args[0][0]
        assert "Error" in msg


@pytest.mark.usefixtures("patch_collections", "fixed_today")
class TestIngresosMes:
    async def test_income_stats(self, mock_collection_pair):
        from services.report_service import ReportService

        members_mock, payments_mock = mock_collection_pair
        svc = ReportService(members_mock, payments_mock)
        with patch("handlers.stats.get_report_service", return_value=svc):
            payments_mock.find.return_value.to_list = AsyncMock(return_value=[{"amount": 500}])
            payments_mock.aggregate.return_value.to_list = AsyncMock(return_value=[{"_id": None, "total": 5000}])

            from handlers.stats import ingresos_mes

            update = make_update()
            context = MagicMock()
            with patch("handlers.stats.date") as mock_date:
                mock_date.today.return_value = date(2026, 5, 15)
                await ingresos_mes(update, context)
            update.message.reply_text.assert_awaited_once()

    async def test_no_message_returns(self, mock_collection_pair):
        from handlers.stats import ingresos_mes

        update = MagicMock()
        update.message = None
        context = MagicMock()
        await ingresos_mes(update, context)

    async def test_db_error_returns_error_message(self, mock_collection_pair):
        members_mock, payments_mock = mock_collection_pair
        svc_mock = AsyncMock()
        svc_mock.get_income_data = AsyncMock(side_effect=Exception("DB error"))

        with patch("handlers.stats.get_report_service", return_value=svc_mock):
            from handlers.stats import ingresos_mes

            update = make_update()
            context = MagicMock()
            with patch("handlers.stats.date") as mock_date:
                mock_date.today.return_value = date(2026, 5, 15)
                await ingresos_mes(update, context)
            msg = update.message.reply_text.call_args[0][0]
            assert "Error" in msg


@pytest.mark.usefixtures("patch_collections", "fixed_today")
class TestVencimientosStats:
    async def test_expirations_stats(self, mock_collection_pair):
        members_mock, payments_mock = mock_collection_pair
        members_mock.find.return_value.to_list = AsyncMock(
            return_value=[
                {"_id": "1", "name": "Juan"},
            ]
        )
        payments_mock.find_one = AsyncMock(return_value={"due_date": "2026-05-15", "payment_date": "2026-05-01"})

        from handlers.stats import vencimientos_stats

        update = make_update()
        context = MagicMock()
        await vencimientos_stats(update, context)
        update.message.reply_text.assert_awaited_once()
        msg = update.message.reply_text.call_args[0][0]
        assert "VENCIMIENTOS" in msg

    async def test_no_message_returns(self, mock_collection_pair):
        from handlers.stats import vencimientos_stats

        update = MagicMock()
        update.message = None
        context = MagicMock()
        await vencimientos_stats(update, context)

    async def test_db_error_returns_error_message(self, mock_collection_pair):
        members_mock, _ = mock_collection_pair
        members_mock.find.side_effect = Exception("DB error")

        from handlers.stats import vencimientos_stats

        update = make_update()
        context = MagicMock()
        await vencimientos_stats(update, context)
        msg = update.message.reply_text.call_args[0][0]
        assert "Error" in msg
