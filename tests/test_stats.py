from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import reset_services
from services.stats_service import ExpirationStats, IncomeStats, MemberStats


@pytest.fixture(autouse=True)
def _reset_services():
    reset_services()
    yield


@pytest.fixture
def _patch_stats_service():
    mock_svc = AsyncMock()
    with patch("handlers.stats.get_stats_service", return_value=mock_svc):
        yield mock_svc


def make_update(text: str = "") -> MagicMock:
    update = MagicMock()
    update.message = MagicMock()
    update.message.text = text
    update.message.reply_text = AsyncMock()
    update.effective_user.id = 12345
    update.effective_chat = MagicMock()
    update.effective_chat.type = "private"
    return update


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


class TestMiembrosActivos:
    async def test_active_members_stats(self, _patch_stats_service):
        mock_svc = _patch_stats_service
        mock_svc.get_member_stats.return_value = MemberStats(
            total=2,
            activos=1,
            en_gracia=1,
            vencidos=0,
        )

        from handlers.stats import miembros_activos

        update = make_update()
        context = MagicMock()
        await miembros_activos(update, context)
        update.message.reply_text.assert_awaited_once()
        msg = update.message.reply_text.call_args[0][0]
        assert "Total: 2" in msg
        assert "Activos: 1" in msg
        assert "En gracia: 1" in msg
        assert "Vencidos: 0" in msg

    async def test_no_message_returns(self, _patch_stats_service):
        from handlers.stats import miembros_activos

        update = MagicMock()
        update.message = None
        context = MagicMock()
        await miembros_activos(update, context)

    async def test_db_error_returns_error_message(self, _patch_stats_service):
        mock_svc = _patch_stats_service
        mock_svc.get_member_stats.side_effect = Exception("DB error")

        from handlers.stats import miembros_activos

        update = make_update()
        context = MagicMock()
        await miembros_activos(update, context)
        msg = update.message.reply_text.call_args[0][0]
        assert "Error" in msg


class TestIngresosMes:
    async def test_income_stats(self, _patch_stats_service):
        mock_svc = _patch_stats_service
        mock_svc.get_income_stats.return_value = IncomeStats(
            monto_actual=5000,
            monto_pasado=4000,
            registros=10,
        )

        from handlers.stats import ingresos_mes

        update = make_update()
        context = MagicMock()
        await ingresos_mes(update, context)
        update.message.reply_text.assert_awaited_once()
        msg = update.message.reply_text.call_args[0][0]
        assert "5,000" in msg
        assert "4,000" in msg
        assert "10" in msg

    async def test_no_message_returns(self, _patch_stats_service):
        from handlers.stats import ingresos_mes

        update = MagicMock()
        update.message = None
        context = MagicMock()
        await ingresos_mes(update, context)

    async def test_db_error_returns_error_message(self, _patch_stats_service):
        mock_svc = _patch_stats_service
        mock_svc.get_income_stats.side_effect = Exception("DB error")

        from handlers.stats import ingresos_mes

        update = make_update()
        context = MagicMock()
        await ingresos_mes(update, context)
        msg = update.message.reply_text.call_args[0][0]
        assert "Error" in msg


class TestVencimientosStats:
    async def test_expirations_stats(self, _patch_stats_service):
        mock_svc = _patch_stats_service
        mock_svc.get_expiration_stats.return_value = ExpirationStats(
            hoy=["Juan"],
            esta_semana=[],
            este_mes=[],
        )

        from handlers.stats import vencimientos_stats

        update = make_update()
        context = MagicMock()
        await vencimientos_stats(update, context)
        update.message.reply_text.assert_awaited_once()
        msg = update.message.reply_text.call_args[0][0]
        assert "VENCIMIENTOS" in msg
        assert "Juan" in msg

    async def test_no_message_returns(self, _patch_stats_service):
        from handlers.stats import vencimientos_stats

        update = MagicMock()
        update.message = None
        context = MagicMock()
        await vencimientos_stats(update, context)

    async def test_db_error_returns_error_message(self, _patch_stats_service):
        mock_svc = _patch_stats_service
        mock_svc.get_expiration_stats.side_effect = Exception("DB error")

        from handlers.stats import vencimientos_stats

        update = make_update()
        context = MagicMock()
        await vencimientos_stats(update, context)
        msg = update.message.reply_text.call_args[0][0]
        assert "Error" in msg
