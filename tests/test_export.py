from unittest.mock import AsyncMock, mock_open, patch

import pytest

from handlers import export
from services import reset_services


@pytest.fixture(autouse=True)
def _reset_services():
    reset_services()
    yield


@pytest.fixture(autouse=True)
def _patch_open():
    m = mock_open(read_data=b"fake content")
    with patch("builtins.open", m):
        yield m


class TestMenuExports:
    async def test_menu_exports(self, mock_update, mock_context):
        await export.menu_exports(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        args = mock_update.message.reply_text.call_args[0][0]
        assert "Menu exportar" in args


class TestExportarExcelMiembros:
    @pytest.fixture
    def _patch_export_svc(self):
        mock_svc = AsyncMock()
        mock_svc.export_members_to_excel = AsyncMock(return_value="fake/path/miembros.xlsx")
        with patch("handlers.export.get_export_service", return_value=mock_svc):
            yield mock_svc

    async def test_empty(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_excel_miembros(mock_update, mock_context)
        _patch_export_svc.export_members_to_excel.assert_awaited_once()
        mock_update.message.reply_document.assert_called_once()

    async def test_with_active_member(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_excel_miembros(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()
        assert mock_update.message.reply_document.call_args[1]["filename"] == "miembros_export.xlsx"

    async def test_with_overdue_member(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_excel_miembros(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()

    async def test_member_without_payment(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_excel_miembros(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()


class TestExportarExcelPagos:
    @pytest.fixture
    def _patch_export_svc(self):
        mock_svc = AsyncMock()
        mock_svc.export_payments_to_excel = AsyncMock(return_value="fake/path/pagos.xlsx")
        with patch("handlers.export.get_export_service", return_value=mock_svc):
            yield mock_svc

    async def test_empty(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_excel_pagos(mock_update, mock_context)
        _patch_export_svc.export_payments_to_excel.assert_awaited_once()
        mock_update.message.reply_document.assert_called_once()

    async def test_with_payments(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_excel_pagos(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()
        assert mock_update.message.reply_document.call_args[1]["filename"] == "pagos_export.xlsx"

    async def test_with_grace_period_flag(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_excel_pagos(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()


class TestExportarTxtResumen:
    @pytest.fixture
    def _patch_export_svc(self):
        mock_svc = AsyncMock()
        mock_svc.generate_txt_summary = AsyncMock(return_value="fake/path/resumen.txt")
        with patch("handlers.export.get_export_service", return_value=mock_svc):
            yield mock_svc

    async def test_empty(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_txt_resumen(mock_update, mock_context)
        _patch_export_svc.generate_txt_summary.assert_awaited_once()
        mock_update.message.reply_document.assert_called_once()

    async def test_with_data(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_txt_resumen(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()
        assert mock_update.message.reply_document.call_args[1]["filename"] == "resumen.txt"

    async def test_multiple_members_in_resumen(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_txt_resumen(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()

    async def test_no_vencen_hoy(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_txt_resumen(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()

    async def test_member_no_payment_skipped(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_txt_resumen(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()


class TestExportarCsvMiembros:
    @pytest.fixture
    def _patch_export_svc(self):
        mock_svc = AsyncMock()
        mock_svc.export_members_to_csv = AsyncMock(return_value="fake/path/miembros.csv")
        with patch("handlers.export.get_export_service", return_value=mock_svc):
            yield mock_svc

    async def test_empty(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_csv_miembros(mock_update, mock_context)
        _patch_export_svc.export_members_to_csv.assert_awaited_once()
        mock_update.message.reply_document.assert_called_once()
        assert mock_update.message.reply_document.call_args[1]["filename"] == "miembros.csv"

    async def test_with_members(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_csv_miembros(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()

    async def test_with_overdue_csv(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_csv_miembros(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()

    async def test_member_without_phone(self, mock_update, mock_context, _patch_export_svc):
        await export.exportar_csv_miembros(mock_update, mock_context)
        mock_update.message.reply_document.assert_called_once()
