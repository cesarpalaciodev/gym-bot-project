from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from handlers.stats import ingresos_mes, menu_stats, miembros_activos, vencimientos_stats
from keyboards import menu_estadisticas


@pytest.fixture
def mock_collection_pair():
    """Creates separate mock collections for members and payments."""
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

    with patch("handlers.stats.get_collection", side_effect=side_effect):
        yield members_mock, payments_mock


@pytest.fixture
def fixed_today():
    today = date(2026, 5, 15)
    with patch("handlers.stats.date") as mock_stats_date:
        mock_stats_date.today.return_value = today
        with patch("utils.dates.date") as mock_utils_date:
            mock_utils_date.today.return_value = today
            yield today


class TestMenuStats:
    async def test_menu_stats_sends_menu(self, mock_update, mock_context):
        await menu_stats(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once_with("📈 Menu estadisticas", reply_markup=menu_estadisticas)


class TestMiembrosActivos:
    async def test_empty_members_list(self, mock_update, mock_context, patch_collections, fixed_today):
        members_mock, _ = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[])
        await miembros_activos(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "Total: 0" in msg
        assert "Activos: 0" in msg
        assert "Vencidos: 0" in msg

    async def test_all_active_members(self, mock_update, mock_context, patch_collections, fixed_today):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[{"_id": "m1", "name": "Juan", "active": True}])
        payments_mock.find_one = AsyncMock(return_value={"member_id": "m1", "due_date": "2026-05-15", "amount": 500})
        await miembros_activos(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "Total: 1" in msg
        assert "Activos: 1" in msg
        assert "En gracia: 0" in msg
        assert "Vencidos: 0" in msg

    async def test_members_in_grace_period(self, mock_update, mock_context, patch_collections, fixed_today):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(
            return_value=[{"_id": "m1", "name": "Pedro", "active": True}]
        )
        payments_mock.find_one = AsyncMock(return_value={"member_id": "m1", "due_date": "2026-05-12", "amount": 500})
        await miembros_activos(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "En gracia: 1" in msg
        assert "Activos: 0" in msg

    async def test_overdue_members(self, mock_update, mock_context, patch_collections, fixed_today):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[{"_id": "m1", "name": "Luis", "active": True}])
        payments_mock.find_one = AsyncMock(return_value={"member_id": "m1", "due_date": "2026-05-08", "amount": 500})
        await miembros_activos(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "Vencidos: 1" in msg
        assert "Activos: 0" in msg

    async def test_member_without_payment_is_overdue(self, mock_update, mock_context, patch_collections, fixed_today):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(
            return_value=[{"_id": "m1", "name": "Carlos", "active": True}]
        )
        payments_mock.find_one = AsyncMock(return_value=None)
        await miembros_activos(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "Vencidos: 1" in msg
        assert "Total: 1" in msg

    async def test_mixed_statuses_with_renovation_percentage(
        self, mock_update, mock_context, patch_collections, fixed_today
    ):
        members_mock, payments_mock = patch_collections
        members_data = [
            {"_id": "m1", "name": "Ana", "active": True},
            {"_id": "m2", "name": "Beto", "active": True},
            {"_id": "m3", "name": "Carla", "active": True},
            {"_id": "m4", "name": "Dave", "active": True},
        ]
        members_mock.find.return_value.to_list = AsyncMock(return_value=members_data)

        payment_map = {
            "m1": {"member_id": "m1", "due_date": "2026-05-15", "amount": 500},
            "m2": {"member_id": "m2", "due_date": "2026-05-12", "amount": 500},
            "m3": {"member_id": "m3", "due_date": "2026-05-08", "amount": 500},
        }

        async def find_one_side(query, sort=None):
            return payment_map.get(query.get("member_id"))

        payments_mock.find_one.side_effect = find_one_side

        await miembros_activos(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "Total: 4" in msg
        assert "Activos: 1" in msg
        assert "En gracia: 1" in msg
        assert "Vencidos: 2" in msg
        assert "25.0%" in msg

    async def test_single_active_shows_100_percent(self, mock_update, mock_context, patch_collections, fixed_today):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[{"_id": "m1", "name": "Eva", "active": True}])
        payments_mock.find_one = AsyncMock(return_value={"member_id": "m1", "due_date": "2026-05-15", "amount": 500})
        await miembros_activos(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "100.0%" in msg

    async def test_inactive_members_excluded_from_count(
        self, mock_update, mock_context, patch_collections, fixed_today
    ):
        members_mock, _ = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[])
        await miembros_activos(mock_update, mock_context)
        members_mock.find.assert_called_once_with({"active": True})


class TestIngresosMes:
    async def test_no_payments_this_or_last_month(self, mock_update, mock_context, patch_collections, fixed_today):
        _, payments_mock = patch_collections
        payments_mock.find.return_value.to_list = AsyncMock(return_value=[])
        await ingresos_mes(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "$0" in msg or "$0," in msg
        assert "Registros: 0" in msg

    async def test_current_month_payments_only(self, mock_update, mock_context, patch_collections, fixed_today):
        _, payments_mock = patch_collections
        payments_mock.find.return_value.to_list = AsyncMock(
            return_value=[
                {"amount": 500, "payment_date": "2026-05-10"},
                {"amount": 500, "payment_date": "2026-05-12"},
            ]
        )
        await ingresos_mes(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "$1,000" in msg
        assert "Registros: 2" in msg

    async def test_positive_change_from_last_month(self, mock_update, mock_context, patch_collections, fixed_today):
        _, payments_mock = patch_collections
        mock_find = MagicMock()
        mock_find.return_value.to_list = AsyncMock()
        mock_find.return_value.to_list.side_effect = [
            [{"amount": 800, "payment_date": "2026-05-10"}],
            [{"amount": 600, "payment_date": "2026-04-15"}],
        ]
        payments_mock.find = mock_find

        await ingresos_mes(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "$800" in msg
        assert "$600" in msg
        assert "+33.3%" in msg or "📈" in msg

    async def test_negative_change_from_last_month(self, mock_update, mock_context, patch_collections, fixed_today):
        _, payments_mock = patch_collections
        mock_find = MagicMock()
        mock_find.return_value.to_list = AsyncMock()
        mock_find.return_value.to_list.side_effect = [
            [{"amount": 300, "payment_date": "2026-05-10"}],
            [{"amount": 900, "payment_date": "2026-04-15"}],
        ]
        payments_mock.find = mock_find

        await ingresos_mes(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "$300" in msg
        assert "$900" in msg
        assert "-66.7%" in msg or "📉" in msg

    async def test_no_comparison_when_previous_month_empty(
        self, mock_update, mock_context, patch_collections, fixed_today
    ):
        _, payments_mock = patch_collections
        mock_find = MagicMock()
        mock_find.return_value.to_list = AsyncMock()
        mock_find.return_value.to_list.side_effect = [
            [{"amount": 500, "payment_date": "2026-05-10"}],
            [],
        ]
        payments_mock.find = mock_find

        await ingresos_mes(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "$500" in msg
        assert "Cambio" not in msg

    async def test_zero_current_month_with_previous(self, mock_update, mock_context, patch_collections, fixed_today):
        _, payments_mock = patch_collections
        mock_find = MagicMock()
        mock_find.return_value.to_list = AsyncMock()
        mock_find.return_value.to_list.side_effect = [
            [],
            [{"amount": 500, "payment_date": "2026-04-15"}],
        ]
        payments_mock.find = mock_find

        await ingresos_mes(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "$0" in msg or "$0," in msg
        assert "Registros: 0" in msg
        assert "$500" in msg
        assert "📉" in msg or "-100.0%" in msg


class TestVencimientosStats:
    async def test_no_active_members(self, mock_update, mock_context, patch_collections, fixed_today):
        members_mock, _ = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[])
        await vencimientos_stats(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "Hoy" in msg
        assert "0" in msg

    async def test_members_expiring_today(self, mock_update, mock_context, patch_collections, fixed_today):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[{"_id": "m1", "name": "Ana", "active": True}])
        payments_mock.find_one = AsyncMock(return_value={"member_id": "m1", "due_date": "2026-05-15", "amount": 500})
        await vencimientos_stats(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "Ana" in msg
        assert "Hoy" in msg

    async def test_members_expiring_this_week(self, mock_update, mock_context, patch_collections, fixed_today):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[{"_id": "m1", "name": "Luis", "active": True}])
        payments_mock.find_one = AsyncMock(return_value={"member_id": "m1", "due_date": "2026-05-18", "amount": 500})
        await vencimientos_stats(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "semana" in msg
        assert "Luis" in msg

    async def test_members_expiring_this_month(self, mock_update, mock_context, patch_collections, fixed_today):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(
            return_value=[{"_id": "m1", "name": "Carla", "active": True}]
        )
        payments_mock.find_one = AsyncMock(return_value={"member_id": "m1", "due_date": "2026-06-05", "amount": 500})
        await vencimientos_stats(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "Este mes" in msg
        assert "Carla" in msg

    async def test_mixed_expiry_ranges(self, mock_update, mock_context, patch_collections, fixed_today):
        members_mock, payments_mock = patch_collections
        members_data = [
            {"_id": "m1", "name": "Diana", "active": True},
            {"_id": "m2", "name": "Eduardo", "active": True},
            {"_id": "m3", "name": "Fer", "active": True},
        ]
        members_mock.find.return_value.to_list = AsyncMock(return_value=members_data)

        payment_map = {
            "m1": {"member_id": "m1", "due_date": "2026-05-15", "amount": 500},
            "m2": {"member_id": "m2", "due_date": "2026-05-18", "amount": 500},
            "m3": {"member_id": "m3", "due_date": "2026-06-05", "amount": 500},
        }

        async def find_one_side(query, sort=None):
            return payment_map.get(query.get("member_id"))

        payments_mock.find_one.side_effect = find_one_side

        await vencimientos_stats(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "Hoy" in msg and "Diana" in msg
        assert "semana" in msg and "Eduardo" in msg
        assert "Este mes" in msg and "Fer" in msg

    async def test_member_without_payment_skipped(self, mock_update, mock_context, patch_collections, fixed_today):
        members_mock, payments_mock = patch_collections
        members_mock.find.return_value.to_list = AsyncMock(return_value=[{"_id": "m1", "name": "Hugo", "active": True}])
        payments_mock.find_one = AsyncMock(return_value=None)
        await vencimientos_stats(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "Hugo" not in msg

    async def test_more_than_five_month_expirations_shows_overflow(
        self, mock_update, mock_context, patch_collections, fixed_today
    ):
        members_mock, payments_mock = patch_collections
        members_data = [{"_id": f"m{i}", "name": f"User{i}", "active": True} for i in range(8)]
        members_mock.find.return_value.to_list = AsyncMock(return_value=members_data)

        payment_map = {f"m{i}": {"member_id": f"m{i}", "due_date": "2026-06-01", "amount": 500} for i in range(8)}

        async def find_one_side(query, sort=None):
            return payment_map.get(query.get("member_id"))

        payments_mock.find_one.side_effect = find_one_side

        await vencimientos_stats(mock_update, mock_context)
        msg = mock_update.message.reply_text.call_args[0][0]
        assert "... y 3 mas" in msg
