from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from handlers import reports


@pytest.fixture(autouse=True)
def _patch_reports_collection(mock_collection):
    with patch("handlers.reports.get_collection", return_value=mock_collection):
        yield


@pytest.fixture(autouse=True)
def _patch_os_makedirs():
    with patch("os.makedirs"):
        yield


@pytest.fixture(autouse=True)
def _patch_open():
    m = mock_open(read_data=b"fake content")
    with patch("builtins.open", m):
        yield m


@pytest.fixture(autouse=True)
def _patch_workbook():
    mock_wb = MagicMock()
    mock_ws = MagicMock()
    mock_wb.active = mock_ws
    mock_wb.max_row = 1
    with patch("openpyxl.Workbook", return_value=mock_wb) as m:
        yield m, mock_wb, mock_ws


@pytest.fixture(autouse=True)
def _patch_pattern_fill():
    with patch("openpyxl.styles.PatternFill") as m:
        yield m


class TestMenuReports:
    async def test_menu_reports(self, mock_update, mock_context):
        await reports.menu_reports(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        args = mock_update.message.reply_text.call_args[0][0]
        assert "Menu reportes" in args


class TestDeudores:
    async def test_no_members(self, mock_update, mock_context, mock_collection):
        mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
        await reports.deudores(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("No hay miembros registrados")

    async def test_all_up_to_date(self, mock_update, mock_context, mock_collection):
        member_data = [
            {"_id": "1", "name": "Alice", "active": True},
        ]
        payment_data = {
            "payment_date": "2026-04-01",
            "due_date": "2026-05-01",
        }
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = payment_data
        with patch("handlers.reports.calcular_dias_vencido", return_value=0):
            await reports.deudores(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("\u2705 Todos los miembros estan al dia")

    async def test_due_today(self, mock_update, mock_context, mock_collection):
        member_data = [
            {"_id": "1", "name": "Bob", "active": True},
        ]
        payment_data = {
            "payment_date": "2026-05-15",
            "due_date": "2026-05-15",
        }
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = payment_data
        with patch("handlers.reports.calcular_dias_vencido", return_value=0):
            await reports.deudores(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Vence hoy" in text
        assert "Bob" in text

    async def test_in_grace_period(self, mock_update, mock_context, mock_collection):
        member_data = [
            {"_id": "2", "name": "Charlie", "active": True},
        ]
        payment_data = {
            "payment_date": "2026-05-10",
            "due_date": "2026-05-10",
        }
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = payment_data
        with patch("handlers.reports.calcular_dias_vencido", return_value=3):
            await reports.deudores(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "En gracia" in text
        assert "Charlie" in text

    async def test_overdue(self, mock_update, mock_context, mock_collection):
        member_data = [
            {"_id": "3", "name": "Diana", "active": True},
        ]
        payment_data = {
            "payment_date": "2026-04-01",
            "due_date": "2026-04-01",
        }
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = payment_data
        with patch("handlers.reports.calcular_dias_vencido", return_value=15):
            await reports.deudores(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Diana" in text
        assert "15" in text

    async def test_mixed_categories(self, mock_update, mock_context, mock_collection):
        member_data = [
            {"_id": "1", "name": "Eve", "active": True},
            {"_id": "2", "name": "Frank", "active": True},
            {"_id": "3", "name": "Grace", "active": True},
        ]
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.side_effect = [
            {"payment_date": "2026-04-15", "due_date": "2026-06-15"},
            {"payment_date": "2026-04-10", "due_date": "2026-04-10"},
            {"payment_date": "2026-03-01", "due_date": "2026-03-01"},
        ]
        with patch("handlers.reports.calcular_dias_vencido", side_effect=[0, 2, 15]):
            await reports.deudores(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Frank" in text
        assert "Grace" in text
        assert "Eve" not in text

    async def test_member_without_payment_skipped(self, mock_update, mock_context, mock_collection):
        member_data = [
            {"_id": "4", "name": "Heidi", "active": True},
        ]
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = None
        await reports.deudores(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("\u2705 Todos los miembros estan al dia")


class TestExcelReporte:
    async def test_empty(self, mock_update, mock_context, mock_collection, _patch_workbook, _patch_pattern_fill):
        mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _, mock_wb, mock_ws = _patch_workbook
        await reports.excel_reporte(mock_update, mock_context)
        mock_ws.append.assert_called_once_with(
            ["Nombre", "Fecha Registro", "Ultimo Pago", "Vence", "Plan", "Dias Vencido", "Estado"]
        )
        mock_wb.save.assert_called_once()
        mock_update.message.reply_document.assert_called_once()

    async def test_up_to_date_member(
        self, mock_update, mock_context, mock_collection, _patch_workbook, _patch_pattern_fill
    ):
        future_date = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
        member_data = [
            {
                "_id": "1",
                "name": "Ivan",
                "created_at": datetime(2026, 1, 15),
                "active": True,
            },
        ]
        payment_data = {
            "payment_date": future_date,
            "due_date": future_date,
            "plan": "Mensual",
        }
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = payment_data
        _, mock_wb, mock_ws = _patch_workbook
        await reports.excel_reporte(mock_update, mock_context)
        mock_ws.append.assert_any_call(["Ivan", "2026-01-15", future_date, future_date, "Mensual", 0, "Al dia"])

    async def test_due_today_excel(
        self, mock_update, mock_context, mock_collection, _patch_workbook, _patch_pattern_fill
    ):
        hoy = date.today()
        hoy_str = hoy.strftime("%Y-%m-%d")
        member_data = [
            {
                "_id": "2",
                "name": "Judy",
                "created_at": datetime(2026, 3, 1),
                "active": True,
            },
        ]
        payment_data = {
            "payment_date": hoy_str,
            "due_date": hoy_str,
            "plan": "Mensual",
        }
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = payment_data
        _, mock_wb, mock_ws = _patch_workbook
        await reports.excel_reporte(mock_update, mock_context)
        mock_ws.append.assert_any_call(["Judy", "2026-03-01", hoy_str, hoy_str, "Mensual", 0, "Vence hoy"])

    async def test_in_grace_excel(
        self, mock_update, mock_context, mock_collection, _patch_workbook, _patch_pattern_fill
    ):
        grace_date = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
        member_data = [
            {
                "_id": "3",
                "name": "Karl",
                "created_at": datetime(2026, 2, 20),
                "active": True,
            },
        ]
        payment_data = {
            "payment_date": grace_date,
            "due_date": grace_date,
            "plan": "Mensual",
        }
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = payment_data
        _, mock_wb, mock_ws = _patch_workbook
        await reports.excel_reporte(mock_update, mock_context)
        mock_ws.append.assert_any_call(["Karl", "2026-02-20", grace_date, grace_date, "Mensual", 3, "En gracia"])

    async def test_overdue_excel(
        self, mock_update, mock_context, mock_collection, _patch_workbook, _patch_pattern_fill
    ):
        overdue_date = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        member_data = [
            {
                "_id": "4",
                "name": "Leo",
                "created_at": datetime(2025, 12, 1),
                "active": True,
            },
        ]
        payment_data = {
            "payment_date": overdue_date,
            "due_date": overdue_date,
            "plan": "Mensual",
        }
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = payment_data
        _, mock_wb, mock_ws = _patch_workbook
        await reports.excel_reporte(mock_update, mock_context)
        mock_ws.append.assert_any_call(["Leo", "2025-12-01", overdue_date, overdue_date, "Mensual", 10, "Vencido"])

    async def test_multiple_members_excel(
        self, mock_update, mock_context, mock_collection, _patch_workbook, _patch_pattern_fill
    ):
        hoy = date.today()
        future_date = (hoy + timedelta(days=15)).strftime("%Y-%m-%d")
        overdue_date = (hoy - timedelta(days=20)).strftime("%Y-%m-%d")
        member_data = [
            {
                "_id": "5",
                "name": "Maria",
                "created_at": datetime(2026, 4, 5),
                "active": True,
            },
            {
                "_id": "6",
                "name": "Nate",
                "created_at": datetime(2026, 4, 10),
                "active": True,
            },
        ]
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.side_effect = [
            {"payment_date": future_date, "due_date": future_date, "plan": "Mensual"},
            {"payment_date": overdue_date, "due_date": overdue_date, "plan": "Trimestral"},
        ]
        _, mock_wb, mock_ws = _patch_workbook
        await reports.excel_reporte(mock_update, mock_context)
        assert mock_ws.append.call_count == 3

    async def test_member_no_payment_skipped_excel(
        self, mock_update, mock_context, mock_collection, _patch_workbook, _patch_pattern_fill
    ):
        member_data = [
            {
                "_id": "7",
                "name": "Olive",
                "created_at": datetime(2026, 5, 1),
                "active": True,
            },
        ]
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = None
        _, mock_wb, mock_ws = _patch_workbook
        await reports.excel_reporte(mock_update, mock_context)
        assert mock_ws.append.call_count == 1
        mock_wb.save.assert_called_once()
