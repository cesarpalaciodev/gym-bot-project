from __future__ import annotations

import time as time_module
from unittest.mock import AsyncMock, patch

import pytest

import handlers.button_handler as bh


@pytest.fixture(autouse=True)
def clear_rate_limit():
    bh.RATE_LIMIT.clear()


class TestBotonesRouting:
    async def test_member_menu_routing(self, mock_update, mock_context):
        mock_update.message.text = "👥 Miembros"
        with patch("handlers.button_handler.members.menu_members", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_payment_menu_routing(self, mock_update, mock_context):
        mock_update.message.text = "💰 Pagos"
        with patch("handlers.button_handler.payments.menu_payments", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_reports_menu_routing(self, mock_update, mock_context):
        mock_update.message.text = "📊 Reportes"
        with patch("handlers.button_handler.reports.menu_reports", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_stats_menu_routing(self, mock_update, mock_context):
        mock_update.message.text = "📈 Estadísticas"
        with patch("handlers.button_handler.stats.menu_stats", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_export_menu_routing(self, mock_update, mock_context):
        mock_update.message.text = "💾 Exportar"
        with patch("handlers.button_handler.export.menu_exports", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_active_members_routing(self, mock_update, mock_context):
        mock_update.message.text = "👥 Miembros activos"
        with patch("handlers.button_handler.stats.miembros_activos", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_monthly_income_routing(self, mock_update, mock_context):
        mock_update.message.text = "💰 Ingresos del mes"
        with patch("handlers.button_handler.stats.ingresos_mes", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_expirations_routing(self, mock_update, mock_context):
        mock_update.message.text = "📅 Vencimientos"
        with patch("handlers.button_handler.stats.vencimientos_stats", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_back_button_routing(self, mock_update, mock_context):
        mock_update.message.text = "⬅️ Volver"
        await bh.botones(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once()

    async def test_unknown_text_calls_processors(self, mock_update, mock_context):
        mock_update.message.text = "some random text"
        with (
            patch("handlers.button_handler.members.procesar_miembro", new_callable=AsyncMock) as mock_mem,
            patch("handlers.button_handler.payments.procesar_pago", new_callable=AsyncMock) as mock_pay,
        ):
            await bh.botones(mock_update, mock_context)
        mock_mem.assert_awaited_once_with(mock_update, mock_context)
        mock_pay.assert_awaited_once_with(mock_update, mock_context)


class TestBotonesNoMessageOrText:
    async def test_no_message_returns_early(self, mock_update, mock_context):
        mock_update.message = None
        with (
            patch("handlers.button_handler.members.menu_members", new_callable=AsyncMock) as mock_fn,
        ):
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_not_called()

    async def test_empty_text_returns_early(self, mock_update, mock_context):
        mock_update.message.text = ""
        with (
            patch("handlers.button_handler.members.menu_members", new_callable=AsyncMock) as mock_fn,
        ):
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_not_called()


class TestBotonesRateLimit:
    async def test_rate_limit_blocks_after_ten_requests(self, mock_update, mock_context):
        mock_update.message.text = "👥 Miembros"
        for _ in range(10):
            bh.RATE_LIMIT[12345].append(time_module.time())

        with patch("handlers.button_handler.members.menu_members", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_not_called()

    async def test_rate_limit_allows_after_window_expires(self, mock_update, mock_context):
        mock_update.message.text = "👥 Miembros"
        old_time = time_module.time() - 10
        bh.RATE_LIMIT[12345] = [old_time] * 10

        with patch("handlers.button_handler.members.menu_members", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_rate_limit_tracks_per_user(self, mock_update, mock_context):
        mock_update.message.text = "👥 Miembros"
        other_user_id = 99999
        bh.RATE_LIMIT[other_user_id] = [time_module.time()] * 10

        with patch("handlers.button_handler.members.menu_members", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_rate_limit_exact_boundary_allows_nine(self, mock_update, mock_context):
        mock_update.message.text = "👥 Miembros"
        for _ in range(9):
            bh.RATE_LIMIT[12345].append(time_module.time())

        with patch("handlers.button_handler.members.menu_members", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)


class TestBotonesGroupAdmin:
    async def test_group_non_admin_ignores_message(self, mock_update, mock_context):
        mock_update.effective_chat.type = "group"
        mock_update.message.text = "👥 Miembros"
        with (
            patch("handlers.button_handler.es_admin_grupo", AsyncMock(return_value=False)) as mock_admin_check,
            patch("handlers.button_handler.members.menu_members", new_callable=AsyncMock) as mock_fn,
        ):
            await bh.botones(mock_update, mock_context)
        mock_admin_check.assert_awaited_once()
        mock_fn.assert_not_called()

    async def test_group_admin_allows_message(self, mock_update, mock_context):
        mock_update.effective_chat.type = "group"
        mock_update.message.text = "👥 Miembros"
        with (
            patch("handlers.button_handler.es_admin_grupo", AsyncMock(return_value=True)),
            patch("handlers.button_handler.members.menu_members", new_callable=AsyncMock) as mock_fn,
        ):
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_group_private_chat_skips_admin_check(self, mock_update, mock_context):
        mock_update.effective_chat.type = "private"
        mock_update.message.text = "👥 Miembros"
        with (
            patch("handlers.button_handler.es_admin_grupo", AsyncMock(return_value=False)) as mock_admin_check,
            patch("handlers.button_handler.members.menu_members", new_callable=AsyncMock) as mock_fn,
        ):
            await bh.botones(mock_update, mock_context)
        mock_admin_check.assert_not_called()
        mock_fn.assert_awaited_once_with(mock_update, mock_context)


class TestBotonesAdminMenu:
    @pytest.fixture
    def patch_admin_db(self, mock_collection):
        async def side_effect(name: str):
            return mock_collection

        with patch("handlers.button_handler.get_collection", side_effect=side_effect):
            yield mock_collection

    async def test_super_admin_can_access_admin_menu(self, mock_update, mock_context, patch_admin_db):
        mock_update.message.text = "⚙️ Administración"
        mock_db = patch_admin_db
        mock_db.find_one = AsyncMock(return_value={"telegram_id": 12345, "role": "super_admin"})
        with patch("handlers.button_handler.admins.menu_admins", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_non_super_admin_blocked_from_admin_menu(self, mock_update, mock_context, patch_admin_db):
        mock_update.message.text = "⚙️ Administración"
        mock_db = patch_admin_db
        mock_db.find_one = AsyncMock(return_value={"telegram_id": 12345, "role": "admin"})
        with patch("handlers.button_handler.admins.menu_admins", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_not_called()
        mock_update.message.reply_text.assert_awaited_once_with("Solo Super Admin puede acceder")

    async def test_no_admin_record_blocked_from_admin_menu(self, mock_update, mock_context, patch_admin_db):
        mock_update.message.text = "⚙️ Administración"
        mock_db = patch_admin_db
        mock_db.find_one = AsyncMock(return_value=None)
        with patch("handlers.button_handler.admins.menu_admins", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_not_called()
        mock_update.message.reply_text.assert_awaited_once_with("Solo Super Admin puede acceder")


class TestBotonesSubMenus:
    async def test_add_member_routing(self, mock_update, mock_context):
        mock_update.message.text = "➕ Agregar miembro"
        with patch("handlers.button_handler.members.agregar_miembro_start", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_bulk_add_routing(self, mock_update, mock_context):
        mock_update.message.text = "👥 Agregar varios"
        with patch("handlers.button_handler.members.agregar_varios_start", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_search_member_routing(self, mock_update, mock_context):
        mock_update.message.text = "🔍 Buscar miembro"
        with patch("handlers.button_handler.members.buscar_miembro_start", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_list_members_routing(self, mock_update, mock_context):
        mock_update.message.text = "📋 Lista miembros"
        with patch("handlers.button_handler.members.lista_miembros", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_delete_member_routing(self, mock_update, mock_context):
        mock_update.message.text = "🗑 Eliminar miembro"
        with patch("handlers.button_handler.members.eliminar_miembro_start", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_bulk_delete_routing(self, mock_update, mock_context):
        mock_update.message.text = "🗑 Eliminar varios"
        with patch("handlers.button_handler.members.eliminar_varios_start", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_register_payment_routing(self, mock_update, mock_context):
        mock_update.message.text = "💰 Registrar pago"
        with patch("handlers.button_handler.payments.registrar_pago_start", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_payment_history_routing(self, mock_update, mock_context):
        mock_update.message.text = "📜 Historial"
        with patch("handlers.button_handler.payments.historial_pagos", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_debtors_routing(self, mock_update, mock_context):
        mock_update.message.text = "⚠️ Deudores"
        with patch("handlers.button_handler.reports.deudores", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_excel_report_routing(self, mock_update, mock_context):
        mock_update.message.text = "📊 Excel"
        with patch("handlers.button_handler.reports.excel_reporte", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_export_excel_members_routing(self, mock_update, mock_context):
        mock_update.message.text = "📊 Excel miembros"
        with patch("handlers.button_handler.export.exportar_excel_miembros", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_export_excel_payments_routing(self, mock_update, mock_context):
        mock_update.message.text = "📊 Excel pagos"
        with patch("handlers.button_handler.export.exportar_excel_pagos", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)

    async def test_export_txt_routing(self, mock_update, mock_context):
        mock_update.message.text = "📄 TXT resumen"
        with patch("handlers.button_handler.export.exportar_txt_resumen", new_callable=AsyncMock) as mock_fn:
            await bh.botones(mock_update, mock_context)
        mock_fn.assert_awaited_once_with(mock_update, mock_context)
