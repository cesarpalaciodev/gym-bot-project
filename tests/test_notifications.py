from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from services import reset_services
from services.notification_service import DailyNotificationData


@pytest.fixture(autouse=True)
def _reset_services():
    reset_services()
    yield


@pytest.fixture
def _patch_notification_service():
    mock_svc = AsyncMock()
    with patch("handlers.notifications.get_notification_service", return_value=mock_svc):
        yield mock_svc


@pytest.fixture
def patch_group_id():
    with patch("handlers.notifications.GROUP_ID", "-100123"):
        yield


@pytest.fixture
def mock_send_message(mock_context):
    mock_context.bot.send_message = AsyncMock()
    yield mock_context.bot.send_message


class TestNotificacion5am:
    async def test_skips_when_group_id_not_set(self, mock_context, _patch_notification_service, caplog):
        with patch("handlers.notifications.GROUP_ID", ""):
            from handlers.notifications import notificacion_5am

            await notificacion_5am(mock_context)
        mock_context.bot.send_message.assert_not_called()

    async def test_sends_empty_message_when_no_active_members(
        self, mock_context, _patch_notification_service, patch_group_id, mock_send_message
    ):
        mock_svc = _patch_notification_service
        today = date(2026, 5, 15)
        data = DailyNotificationData(fecha=today)
        mock_svc.generate_daily_notification.return_value = data

        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        mock_send_message.assert_awaited_once()
        text = mock_send_message.call_args[1]["text"]
        assert "No hay miembros registrados" in text

    async def test_all_members_active(
        self, mock_context, _patch_notification_service, patch_group_id, mock_send_message
    ):
        mock_svc = _patch_notification_service
        today = date(2026, 5, 15)
        data = DailyNotificationData(fecha=today, activos=["Juan"])
        mock_svc.generate_daily_notification.return_value = data

        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_send_message.call_args[1]["text"]
        assert "ACTIVOS: 1" in text
        assert "VENCIDOS" not in text
        assert "GRACIA" not in text

    async def test_members_expiring_today(self, mock_context, _patch_notification_service, patch_group_id):
        mock_svc = _patch_notification_service
        today = date(2026, 5, 15)
        data = DailyNotificationData(fecha=today, hoy_vencen=["Ana"])
        mock_svc.generate_daily_notification.return_value = data

        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_context.bot.send_message.call_args[1]["text"]
        assert "VENCEN HOY" in text
        assert "Ana" in text
        assert "ACTIVOS: 0" in text

    async def test_members_in_grace_period(self, mock_context, _patch_notification_service, patch_group_id):
        mock_svc = _patch_notification_service
        today = date(2026, 5, 15)
        data = DailyNotificationData(fecha=today, gracia=[("Pedro", 3)])
        mock_svc.generate_daily_notification.return_value = data

        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_context.bot.send_message.call_args[1]["text"]
        assert "EN GRACIA" in text
        assert "Pedro" in text
        assert "3 dias" in text

    async def test_overdue_members(self, mock_context, _patch_notification_service, patch_group_id):
        mock_svc = _patch_notification_service
        today = date(2026, 5, 15)
        data = DailyNotificationData(fecha=today, vencidos=[("Luis", 7)])
        mock_svc.generate_daily_notification.return_value = data

        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_context.bot.send_message.call_args[1]["text"]
        assert "VENCIDOS" in text
        assert "Luis" in text
        assert "7 dias" in text

    async def test_member_without_payment_recorded_as_overdue(
        self, mock_context, _patch_notification_service, patch_group_id
    ):
        mock_svc = _patch_notification_service
        today = date(2026, 5, 15)
        data = DailyNotificationData(fecha=today, vencidos=[("Carlos", 0)])
        mock_svc.generate_daily_notification.return_value = data

        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_context.bot.send_message.call_args[1]["text"]
        assert "VENCIDOS" in text
        assert "Carlos" in text
        assert "0 dias" in text

    async def test_mixed_members_status(
        self, mock_context, _patch_notification_service, patch_group_id, mock_send_message
    ):
        mock_svc = _patch_notification_service
        today = date(2026, 5, 15)
        data = DailyNotificationData(
            fecha=today,
            activos=["Ana"],
            hoy_vencen=["Beto"],
            gracia=[("Carla", 3)],
            vencidos=[("Dave", 7), ("Eva", 0)],
        )
        mock_svc.generate_daily_notification.return_value = data

        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_send_message.call_args[1]["text"]
        assert "ACTIVOS: 1" in text
        assert "VENCEN HOY" in text and "Beto" in text
        assert "EN GRACIA" in text and "Carla" in text
        assert "VENCIDOS" in text and "Dave" in text and "Eva" in text

    async def test_sends_to_correct_group_id(self, mock_context, _patch_notification_service, mock_send_message):
        mock_svc = _patch_notification_service
        today = date(2026, 5, 15)
        data = DailyNotificationData(fecha=today)
        mock_svc.generate_daily_notification.return_value = data

        with patch("handlers.notifications.GROUP_ID", "-100999"):
            from handlers.notifications import notificacion_5am

            await notificacion_5am(mock_context)
        mock_send_message.assert_awaited_once()
        assert mock_send_message.call_args[1]["chat_id"] == "-100999"

    async def test_logs_error_when_send_fails(self, mock_context, _patch_notification_service, patch_group_id, caplog):
        mock_svc = _patch_notification_service
        today = date(2026, 5, 15)
        data = DailyNotificationData(fecha=today)
        mock_svc.generate_daily_notification.return_value = data
        mock_context.bot.send_message = AsyncMock(side_effect=Exception("Network error"))

        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        assert any("Error" in rec.message for rec in caplog.records)

    async def test_notificacion_includes_date_header(
        self, mock_context, _patch_notification_service, patch_group_id, mock_send_message
    ):
        mock_svc = _patch_notification_service
        today = date(2026, 5, 15)
        data = DailyNotificationData(fecha=today, activos=["Juan"])
        mock_svc.generate_daily_notification.return_value = data

        from handlers.notifications import notificacion_5am

        await notificacion_5am(mock_context)
        text = mock_send_message.call_args[1]["text"]
        assert "RECORDATORIO MATUTINO" in text
        assert "2026-05-15" in text
