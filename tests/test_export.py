from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from handlers import export
from services import reset_services


@pytest.fixture(autouse=True)
def _reset_services():
    reset_services()
    yield


@pytest.fixture(autouse=True)
def _patch_export_collection(mock_collection):
    with patch("services.factory.get_collection", AsyncMock(return_value=mock_collection)):
        yield


@pytest.fixture(autouse=True)
def _patch_os_makedirs():
    with patch("handlers.export.os.makedirs"):
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
    with patch("openpyxl.Workbook", return_value=mock_wb) as m:
        yield m, mock_wb, mock_ws


@pytest.fixture(autouse=True)
def _patch_sort_chain(mock_collection):
    mock_collection.find.return_value.sort.return_value = mock_collection.find.return_value
    yield


class TestMenuExports:
    async def test_menu_exports(self, mock_update, mock_context):
        await export.menu_exports(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        args = mock_update.message.reply_text.call_args[0][0]
        assert "Menu exportar" in args


class TestExportarExcelMiembros:
    async def test_empty(self, mock_update, mock_context, mock_collection, _patch_workbook):
        mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _, mock_wb, mock_ws = _patch_workbook
        await export.exportar_excel_miembros(mock_update, mock_context)
        mock_ws.append.assert_called_once_with(
            ["Nombre", "Fecha Registro", "Telefono", "Estado", "Ultimo Pago", "Vence", "Plan"]
        )
        mock_wb.save.assert_called_once()
        mock_update.message.reply_document.assert_called_once()

    async def test_with_active_member(self, mock_update, mock_context, mock_collection, _patch_workbook):
        member_data = [
            {
                "_id": "1",
                "name": "Juan Perez",
                "created_at": datetime(2026, 3, 1),
                "phone": "555-0100",
                "active": True,
            }
        ]
        payment_data = {
            "payment_date": "2026-05-01",
            "due_date": "2026-06-01",
            "plan": "Mensual",
        }
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = payment_data
        _, mock_wb, mock_ws = _patch_workbook
        await export.exportar_excel_miembros(mock_update, mock_context)
        mock_ws.append.assert_any_call(
            ["Juan Perez", "2026-03-01", "555-0100", "Activo", "2026-05-01", "2026-06-01", "Mensual"]
        )

    async def test_with_overdue_member(self, mock_update, mock_context, mock_collection, _patch_workbook):
        member_data = [
            {
                "_id": "2",
                "name": "Pedro Vencido",
                "created_at": datetime(2019, 12, 1),
                "phone": "",
                "active": True,
            }
        ]
        payment_data = {
            "payment_date": "2019-12-01",
            "due_date": "2020-01-01",
            "plan": "Mensual",
        }
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = payment_data
        _, mock_wb, mock_ws = _patch_workbook
        await export.exportar_excel_miembros(mock_update, mock_context)
        mock_ws.append.assert_any_call(
            ["Pedro Vencido", "2019-12-01", "", "Vencido", "2019-12-01", "2020-01-01", "Mensual"]
        )

    async def test_member_without_payment(self, mock_update, mock_context, mock_collection, _patch_workbook):
        member_data = [
            {
                "_id": "3",
                "name": "Sin Pago",
                "created_at": datetime(2026, 5, 1),
                "phone": "555-0200",
                "active": True,
            }
        ]
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = None
        _, mock_wb, mock_ws = _patch_workbook
        await export.exportar_excel_miembros(mock_update, mock_context)
        mock_ws.append.assert_any_call(["Sin Pago", "2026-05-01", "555-0200", "Activo", "", "", ""])


class TestExportarExcelPagos:
    async def test_empty(self, mock_update, mock_context, mock_collection, _patch_workbook):
        mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
        mock_collection.find.return_value.sort.return_value.to_list = AsyncMock(return_value=[])
        _, mock_wb, mock_ws = _patch_workbook
        await export.exportar_excel_pagos(mock_update, mock_context)
        mock_ws.append.assert_called_once_with(["Miembro", "Fecha Pago", "Monto", "Plan", "Vence", "Gracia"])
        mock_wb.save.assert_called_once()
        mock_update.message.reply_document.assert_called_once()

    async def test_with_payments(self, mock_update, mock_context, mock_collection, _patch_workbook):
        payments_data = [
            {
                "member_name": "Alice",
                "payment_date": "2026-04-01",
                "amount": 500,
                "plan": "Mensual",
                "due_date": "2026-05-01",
                "grace_period": False,
            },
            {
                "member_name": "Bob",
                "payment_date": "2026-04-10",
                "amount": 1350,
                "plan": "Trimestral",
                "due_date": "2026-07-10",
                "grace_period": True,
            },
        ]
        mock_collection.find.return_value.sort.return_value.to_list = AsyncMock(return_value=payments_data)
        _, mock_wb, mock_ws = _patch_workbook
        await export.exportar_excel_pagos(mock_update, mock_context)
        mock_ws.append.assert_any_call(["Alice", "2026-04-01", 500, "Mensual", "2026-05-01", "No"])
        mock_ws.append.assert_any_call(["Bob", "2026-04-10", 1350, "Trimestral", "2026-07-10", "Si"])

    async def test_with_grace_period_flag(self, mock_update, mock_context, mock_collection, _patch_workbook):
        payments_data = [
            {
                "member_name": "Charlie",
                "payment_date": "2026-03-20",
                "amount": 500,
                "plan": "Mensual",
                "due_date": "2026-04-20",
                "grace_period": True,
            },
        ]
        mock_collection.find.return_value.sort.return_value.to_list = AsyncMock(return_value=payments_data)
        _, mock_wb, mock_ws = _patch_workbook
        await export.exportar_excel_pagos(mock_update, mock_context)
        mock_ws.append.assert_any_call(["Charlie", "2026-03-20", 500, "Mensual", "2026-04-20", "Si"])


class TestExportarTxtResumen:
    async def test_empty(self, mock_update, mock_context, mock_collection):
        hoy = date.today()
        mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
        await export.exportar_txt_resumen(mock_update, mock_context)
        expected_filename = f"resumen_{hoy.strftime('%Y%m%d')}.txt"
        mock_update.message.reply_document.assert_called_once()
        assert mock_update.message.reply_document.call_args[1]["filename"] == expected_filename

    async def test_with_data(self, mock_update, mock_context, mock_collection):
        member_id = "abc123"
        member_data = [
            {"_id": member_id, "name": "Diana", "active": True},
        ]
        payment_data = [
            {"member_name": "Diana", "amount": 500, "payment_date": "2026-04-01"},
        ]
        mock_collection.find.return_value.to_list = AsyncMock(
            side_effect=[
                member_data,
                payment_data,
            ]
        )
        mock_collection.find_one.return_value = {
            "member_id": member_id,
            "due_date": "2026-04-01",
        }
        await export.exportar_txt_resumen(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()
        assert mock_update.message.reply_document.call_args[1]["filename"].startswith("resumen_")

    async def test_multiple_members_in_resumen(self, mock_update, mock_context, mock_collection):
        member_data = [
            {"_id": "m1", "name": "Eve", "active": True},
            {"_id": "m2", "name": "Frank", "active": True},
        ]
        payment_data = [
            {"member_name": "Eve", "amount": 500, "payment_date": "2026-04-15"},
            {"member_name": "Frank", "amount": 1350, "payment_date": "2026-04-10"},
        ]
        mock_collection.find.return_value.to_list = AsyncMock(
            side_effect=[
                member_data,
                payment_data,
            ]
        )
        mock_collection.find_one.return_value = {
            "due_date": "2026-04-15",
        }
        await export.exportar_txt_resumen(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()

    async def test_no_vencen_hoy(self, mock_update, mock_context, mock_collection):
        hoy = date.today()
        member_data = [
            {"_id": "m1", "name": "Grace", "active": True},
        ]
        payment_data = [
            {"member_name": "Grace", "amount": 500, "payment_date": hoy.strftime("%Y-%m-%d")},
        ]
        mock_collection.find.return_value.to_list = AsyncMock(
            side_effect=[
                member_data,
                payment_data,
            ]
        )
        mock_collection.find_one.return_value = {
            "due_date": hoy.strftime("%Y-%m-%d"),
        }
        await export.exportar_txt_resumen(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()

    async def test_member_no_payment_skipped(self, mock_update, mock_context, mock_collection):
        member_data = [
            {"_id": "m1", "name": "Hank", "active": True},
        ]
        payment_data = [
            {"member_name": "Hank", "amount": 500, "payment_date": "2026-04-01"},
        ]
        mock_collection.find.return_value.to_list = AsyncMock(
            side_effect=[
                member_data,
                payment_data,
            ]
        )
        mock_collection.find_one.return_value = None
        await export.exportar_txt_resumen(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()


class TestExportarCsvMiembros:
    async def test_empty(self, mock_update, mock_context, mock_collection):
        mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
        await export.exportar_csv_miembros(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()
        assert mock_update.message.reply_document.call_args[1]["filename"] == "miembros.csv"

    async def test_with_members(self, mock_update, mock_context, mock_collection):
        member_data = [
            {
                "_id": "1",
                "name": "Ivan",
                "created_at": datetime(2026, 2, 15),
                "phone": "555-0300",
                "active": True,
            },
        ]
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = {
            "payment_date": "2026-03-15",
            "due_date": "2026-04-15",
        }
        await export.exportar_csv_miembros(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()

    async def test_with_overdue_csv(self, mock_update, mock_context, mock_collection):
        member_data = [
            {
                "_id": "2",
                "name": "Julia Vencida",
                "created_at": datetime(2020, 1, 1),
                "phone": "",
                "active": True,
            },
        ]
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = {
            "payment_date": "2020-01-01",
            "due_date": "2020-01-01",
        }
        await export.exportar_csv_miembros(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()

    async def test_member_without_phone(self, mock_update, mock_context, mock_collection):
        member_data = [
            {
                "_id": "3",
                "name": "No Phone",
                "created_at": datetime(2026, 4, 10),
                "active": True,
            },
        ]
        mock_collection.find.return_value.to_list = AsyncMock(return_value=member_data)
        mock_collection.find_one.return_value = None
        await export.exportar_csv_miembros(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()
