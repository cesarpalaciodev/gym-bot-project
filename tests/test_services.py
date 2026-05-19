"""Unit tests for services layer with mocked repositories."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest

from services.admin_service import AdminInfo, AdminService
from services.notification_service import DailyNotificationData, NotificationService
from services.stats_service import ExpirationStats, IncomeStats, MemberStats, StatsService

# ── Helpers ─────────────────────────────────────────────────────────────


def make_async_mock_repo(**methods):
    """Create a mock repository with async methods."""
    repo = AsyncMock()
    for name, return_value in methods.items():
        setattr(repo, name, AsyncMock(return_value=return_value))
    return repo


# ── AdminService ────────────────────────────────────────────────────────


class TestAdminService:
    @pytest.fixture
    def admin_repo(self):
        return make_async_mock_repo(
            get_by_telegram_id=None,
            list_all=[],
            create_admin="abc123",
            delete_by_telegram_id=False,
            update_role=False,
            exists_by_telegram_id=False,
        )

    @pytest.fixture
    def svc(self, admin_repo):
        return AdminService(admin_repo)

    async def test_is_super_admin_true(self, svc, admin_repo):
        admin_repo.get_by_telegram_id.return_value = {"telegram_id": 123, "role": "super_admin"}
        assert await svc.is_super_admin(123) is True

    async def test_is_super_admin_false_wrong_role(self, svc, admin_repo):
        admin_repo.get_by_telegram_id.return_value = {"telegram_id": 123, "role": "admin"}
        assert await svc.is_super_admin(123) is False

    async def test_is_super_admin_false_not_found(self, svc, admin_repo):
        admin_repo.get_by_telegram_id.return_value = None
        assert await svc.is_super_admin(123) is False

    async def test_is_admin_true(self, svc, admin_repo):
        admin_repo.get_by_telegram_id.return_value = {"telegram_id": 456}
        assert await svc.is_admin(456) is True

    async def test_is_admin_false(self, svc, admin_repo):
        admin_repo.get_by_telegram_id.return_value = None
        assert await svc.is_admin(789) is False

    async def test_get_admin_role(self, svc, admin_repo):
        admin_repo.get_by_telegram_id.return_value = {"telegram_id": 1, "role": "viewer"}
        assert await svc.get_admin_role(1) == "viewer"

    async def test_get_admin_role_not_found(self, svc, admin_repo):
        admin_repo.get_by_telegram_id.return_value = None
        assert await svc.get_admin_role(999) is None

    async def test_list_all_admins(self, svc, admin_repo):
        admin_repo.list_all.return_value = [
            {"telegram_id": 1, "name": "Alice", "role": "super_admin"},
            {"telegram_id": 2, "name": "Bob", "role": "admin"},
        ]
        admins = await svc.list_all_admins()
        assert len(admins) == 2
        assert isinstance(admins[0], AdminInfo)
        assert admins[0].telegram_id == 1
        assert admins[0].name == "Alice"
        assert admins[1].role == "admin"

    async def test_list_all_admins_empty(self, svc, admin_repo):
        admin_repo.list_all.return_value = []
        admins = await svc.list_all_admins()
        assert admins == []

    async def test_add_admin_new(self, svc, admin_repo):
        admin_repo.exists_by_telegram_id.return_value = False
        result = await svc.add_admin(555, "NewAdmin", role="admin")
        assert result is True
        admin_repo.create_admin.assert_awaited_once()

    async def test_add_admin_duplicate(self, svc, admin_repo):
        admin_repo.exists_by_telegram_id.return_value = True
        result = await svc.add_admin(555, "NewAdmin")
        assert result is False
        admin_repo.create_admin.assert_not_awaited()

    async def test_remove_admin_found(self, svc, admin_repo):
        admin_repo.delete_by_telegram_id.return_value = True
        result = await svc.remove_admin(777)
        assert result is True
        admin_repo.delete_by_telegram_id.assert_awaited_once_with(777)

    async def test_remove_admin_not_found(self, svc, admin_repo):
        admin_repo.delete_by_telegram_id.return_value = False
        result = await svc.remove_admin(777)
        assert result is False

    async def test_change_role_found(self, svc, admin_repo):
        admin_repo.exists_by_telegram_id.return_value = True
        result = await svc.change_role(888, "viewer")
        assert result is True
        admin_repo.update_role.assert_awaited_once_with(888, "viewer")

    async def test_change_role_not_found(self, svc, admin_repo):
        admin_repo.exists_by_telegram_id.return_value = False
        result = await svc.change_role(888, "viewer")
        assert result is False
        admin_repo.update_role.assert_not_awaited()

    async def test_validate_telegram_id_valid(self, svc):
        result = await svc.validate_telegram_id("12345")
        assert result == 12345

    async def test_validate_telegram_id_with_whitespace(self, svc):
        result = await svc.validate_telegram_id("  67890  ")
        assert result == 67890

    async def test_validate_telegram_id_invalid(self, svc):
        result = await svc.validate_telegram_id("abc")
        assert result is None

    async def test_validate_telegram_id_empty(self, svc):
        result = await svc.validate_telegram_id("")
        assert result is None

    async def test_get_admin_display_info_found(self, svc, admin_repo):
        admin_repo.get_by_telegram_id.return_value = {"telegram_id": 111, "name": "Carlos", "role": "admin"}
        info = await svc.get_admin_display_info(111)
        assert info is not None
        assert info.telegram_id == 111
        assert info.name == "Carlos"
        assert info.role == "admin"

    async def test_get_admin_display_info_not_found(self, svc, admin_repo):
        admin_repo.get_by_telegram_id.return_value = None
        info = await svc.get_admin_display_info(999)
        assert info is None


# ── StatsService ────────────────────────────────────────────────────────


class TestMemberStats:
    def test_renewal_rate_normal(self):
        stats = MemberStats(total=10, activos=7, en_gracia=2, vencidos=1)
        assert stats.renewal_rate == 70.0

    def test_renewal_rate_zero_members(self):
        stats = MemberStats(total=0, activos=0, en_gracia=0, vencidos=0)
        assert stats.renewal_rate == 0.0

    def test_renewal_rate_all_active(self):
        stats = MemberStats(total=5, activos=5, en_gracia=0, vencidos=0)
        assert stats.renewal_rate == 100.0

    def test_renewal_rate_none_active(self):
        stats = MemberStats(total=5, activos=0, en_gracia=0, vencidos=5)
        assert stats.renewal_rate == 0.0


class TestIncomeStats:
    def test_change_percentage_positive(self):
        stats = IncomeStats(monto_actual=1500, monto_pasado=1000, registros=5)
        assert stats.change_percentage == 50.0

    def test_change_percentage_negative(self):
        stats = IncomeStats(monto_actual=800, monto_pasado=1000, registros=3)
        assert stats.change_percentage == -20.0

    def test_change_percentage_none_when_past_zero(self):
        stats = IncomeStats(monto_actual=500, monto_pasado=0, registros=2)
        assert stats.change_percentage is None

    def test_change_percentage_exact_double(self):
        stats = IncomeStats(monto_actual=2000, monto_pasado=1000, registros=10)
        assert stats.change_percentage == 100.0


class TestStatsService:
    @pytest.fixture
    def member_repo(self):
        return make_async_mock_repo(get_all_active=[])

    @pytest.fixture
    def payment_repo(self):
        return make_async_mock_repo(
            get_last_by_member=None,
            get_payments_for_period=[],
            get_all_payments=[],
        )

    @pytest.fixture
    def svc(self, member_repo, payment_repo):
        return StatsService(member_repo, payment_repo)

    async def test_get_member_stats_empty(self, svc, member_repo):
        member_repo.get_all_active.return_value = []
        stats = await svc.get_member_stats()
        assert stats.total == 0
        assert stats.activos == 0
        assert stats.en_gracia == 0
        assert stats.vencidos == 0

    async def test_get_member_stats_with_active(self, svc, member_repo, payment_repo):
        member_repo.get_all_active.return_value = [{"_id": "m1", "name": "Juan"}]
        payment_repo.get_last_by_member.return_value = {
            "member_id": "m1",
            "due_date": "2026-06-01",
            "amount": 500,
        }
        stats = await svc.get_member_stats()
        assert stats.activos == 1
        assert stats.en_gracia == 0
        assert stats.vencidos == 0

    async def test_get_member_stats_no_payment_counts_as_vencido(self, svc, member_repo, payment_repo):
        member_repo.get_all_active.return_value = [
            {"_id": "m1", "name": "SinPago"},
            {"_id": "m2", "name": "Otro"},
        ]
        payment_repo.get_last_by_member.return_value = None
        stats = await svc.get_member_stats()
        assert stats.vencidos == 2
        assert stats.total == 2

    async def test_get_expiration_stats_empty(self, svc, member_repo):
        member_repo.get_all_active.return_value = []
        stats = await svc.get_expiration_stats(reference_date=date(2026, 5, 15))
        assert stats.hoy == []
        assert stats.esta_semana == []
        assert stats.este_mes == []

    async def test_get_expiration_stats_hoy(self, svc, member_repo, payment_repo):
        member_repo.get_all_active.return_value = [{"_id": "m1", "name": "Hoy"}]
        payment_repo.get_last_by_member.return_value = {
            "member_id": "m1",
            "due_date": "2026-05-15",
        }
        today = date(2026, 5, 15)
        stats = await svc.get_expiration_stats(reference_date=today)
        assert stats.hoy == ["Hoy"]
        assert stats.esta_semana == []

    async def test_get_expiration_stats_skips_no_payment(self, svc, member_repo, payment_repo):
        member_repo.get_all_active.return_value = [{"_id": "m1", "name": "Skip"}]
        payment_repo.get_last_by_member.return_value = None
        stats = await svc.get_expiration_stats(reference_date=date(2026, 5, 15))
        assert stats.hoy == []
        assert stats.esta_semana == []
        assert stats.este_mes == []


# ── NotificationService ─────────────────────────────────────────────────


class TestDailyNotificationData:
    def test_empty_data_is_empty(self):
        data = DailyNotificationData(fecha=date(2026, 5, 15))
        assert data.is_empty()
        assert data.format_message() == "No hay miembros registrados\n"

    def test_totals(self):
        data = DailyNotificationData(
            fecha=date(2026, 5, 15),
            activos=["A", "B"],
            hoy_vencen=["C"],
            gracia=[("D", 2)],
            vencidos=[("E", 5), ("F", 10)],
        )
        assert data.total_activos == 2
        assert data.total_hoy_vencen == 1
        assert data.total_gracia == 1
        assert data.total_vencidos == 2
        assert not data.is_empty()

    def test_format_active_only(self):
        data = DailyNotificationData(fecha=date(2026, 5, 15), activos=["Juan"])
        msg = data.format_message()
        assert "ACTIVOS: 1" in msg
        assert "VENCIDOS" not in msg
        assert "GRACIA" not in msg

    def test_format_hoy_vencen(self):
        data = DailyNotificationData(fecha=date(2026, 5, 15), hoy_vencen=["Ana"])
        msg = data.format_message()
        assert "VENCEN HOY" in msg
        assert "Ana" in msg

    def test_format_gracia(self):
        data = DailyNotificationData(fecha=date(2026, 5, 15), gracia=[("Pedro", 3)])
        msg = data.format_message()
        assert "EN GRACIA" in msg
        assert "Pedro" in msg
        assert "3 dias" in msg

    def test_format_vencidos(self):
        data = DailyNotificationData(fecha=date(2026, 5, 15), vencidos=[("Luis", 7)])
        msg = data.format_message()
        assert "VENCIDOS" in msg
        assert "Luis" in msg
        assert "7 dias" in msg

    def test_format_includes_date(self):
        data = DailyNotificationData(fecha=date(2026, 5, 15), activos=["A"])
        msg = data.format_message()
        assert "2026-05-15" in msg
        assert "RECORDATORIO MATUTINO" in msg

    def test_format_mixed(self):
        data = DailyNotificationData(
            fecha=date(2026, 5, 15),
            activos=["A"],
            hoy_vencen=["B"],
            gracia=[("C", 2)],
            vencidos=[("D", 8)],
        )
        msg = data.format_message()
        assert "ACTIVOS: 1" in msg
        assert "VENCEN HOY" in msg
        assert "EN GRACIA" in msg
        assert "VENCIDOS" in msg


class TestNotificationService:
    @pytest.fixture
    def member_repo(self):
        return make_async_mock_repo(get_all_active=[])

    @pytest.fixture
    def payment_repo(self):
        return make_async_mock_repo(get_last_by_member=None)

    @pytest.fixture
    def svc(self, member_repo, payment_repo):
        return NotificationService(member_repo, payment_repo)

    async def test_generate_empty(self, svc, member_repo):
        member_repo.get_all_active.return_value = []
        data = await svc.generate_daily_notification(reference_date=date(2026, 5, 15))
        assert data.is_empty()

    async def test_generate_active_member(self, svc, member_repo, payment_repo):
        member_repo.get_all_active.return_value = [{"_id": "m1", "name": "Juan"}]
        payment_repo.get_last_by_member.return_value = {
            "member_id": "m1",
            "due_date": "2026-06-01",
        }
        data = await svc.generate_daily_notification(reference_date=date(2026, 5, 15))
        assert data.total_activos == 1
        assert "Juan" in data.activos

    async def test_generate_expiring_today(self, svc, member_repo, payment_repo):
        hoy = date.today()
        member_repo.get_all_active.return_value = [{"_id": "m1", "name": "Hoy"}]
        payment_repo.get_last_by_member.return_value = {
            "member_id": "m1",
            "due_date": hoy.strftime("%Y-%m-%d"),
        }
        data = await svc.generate_daily_notification(reference_date=hoy)
        assert data.total_hoy_vencen == 1
        assert "Hoy" in data.hoy_vencen

    async def test_generate_grace(self, svc, member_repo, payment_repo):
        hoy = date.today()
        grace_date = hoy - timedelta(days=3)
        member_repo.get_all_active.return_value = [{"_id": "m1", "name": "Grace"}]
        payment_repo.get_last_by_member.return_value = {
            "member_id": "m1",
            "due_date": grace_date.strftime("%Y-%m-%d"),
        }
        data = await svc.generate_daily_notification(reference_date=hoy)
        assert data.total_gracia == 1

    async def test_generate_overdue(self, svc, member_repo, payment_repo):
        hoy = date.today()
        overdue_date = hoy - timedelta(days=10)
        member_repo.get_all_active.return_value = [{"_id": "m1", "name": "Late"}]
        payment_repo.get_last_by_member.return_value = {
            "member_id": "m1",
            "due_date": overdue_date.strftime("%Y-%m-%d"),
        }
        data = await svc.generate_daily_notification(reference_date=hoy)
        assert data.total_vencidos == 1

    async def test_generate_no_payment_vencido(self, svc, member_repo, payment_repo):
        hoy = date.today()
        member_repo.get_all_active.return_value = [{"_id": "m1", "name": "SinPago"}]
        payment_repo.get_last_by_member.return_value = None
        data = await svc.generate_daily_notification(reference_date=hoy)
        assert data.total_vencidos == 1
        names = [name for name, _ in data.vencidos]
        assert "SinPago" in names


# ── ExpirationStats (from stats_service) ────────────────────────────────


class TestExpirationStats:
    def test_empty(self):
        stats = ExpirationStats(hoy=[], esta_semana=[], este_mes=[])
        assert stats.hoy == []
        assert stats.esta_semana == []
        assert stats.este_mes == []

    def test_with_data(self):
        stats = ExpirationStats(
            hoy=["Alice"],
            esta_semana=[("Bob", "2026-05-18")],
            este_mes=[("Charlie", "2026-05-25"), ("Diana", "2026-06-01")],
        )
        assert len(stats.hoy) == 1
        assert len(stats.esta_semana) == 1
        assert len(stats.este_mes) == 2
        assert stats.esta_semana[0][0] == "Bob"
