from telegram import ReplyKeyboardMarkup

from keyboards import (
    menu_admin,
    menu_confirmar,
    menu_estadisticas,
    menu_exportar,
    menu_miembros,
    menu_pagos,
    menu_planes,
    menu_principal,
    menu_reportes,
)


class TestMenuStructure:
    def _check_is_keyboard(self, menu):
        assert isinstance(menu, ReplyKeyboardMarkup)

    def _check_buttons_in_row(self, menu, texts):
        flat = [btn for row in menu.keyboard for btn in row]
        for t in texts:
            assert any(t in str(b) for b in flat), f"Button '{t}' not found"

    def test_menu_principal(self):
        self._check_is_keyboard(menu_principal)
        self._check_buttons_in_row(menu_principal, ["Miembros", "Pagos", "Reportes", "Estadísticas", "Exportar", "Administración", "Volver"])

    def test_menu_miembros(self):
        self._check_is_keyboard(menu_miembros)
        self._check_buttons_in_row(menu_miembros, ["Agregar miembro", "Agregar varios", "Buscar miembro", "Lista miembros", "Eliminar miembro", "Eliminar varios", "Volver"])

    def test_menu_pagos(self):
        self._check_is_keyboard(menu_pagos)
        self._check_buttons_in_row(menu_pagos, ["Registrar pago", "Historial", "Volver"])

    def test_menu_reportes(self):
        self._check_is_keyboard(menu_reportes)
        self._check_buttons_in_row(menu_reportes, ["Deudores", "Excel", "Volver"])

    def test_menu_estadisticas(self):
        self._check_is_keyboard(menu_estadisticas)
        self._check_buttons_in_row(menu_estadisticas, ["Miembros activos", "Ingresos del mes", "Vencimientos", "Volver"])

    def test_menu_exportar(self):
        self._check_is_keyboard(menu_exportar)
        self._check_buttons_in_row(menu_exportar, ["Excel miembros", "Excel pagos", "TXT resumen", "Volver"])

    def test_menu_admin(self):
        self._check_is_keyboard(menu_admin)
        self._check_buttons_in_row(menu_admin, ["Agregar admin", "Lista admins", "Quitar admin", "Cambiar rol", "Volver"])

    def test_menu_planes_has_all(self):
        self._check_is_keyboard(menu_planes)
        self._check_buttons_in_row(menu_planes, ["Mensual", "Trimestral", "Semestral", "Anual", "Cancelar"])

    def test_menu_confirmar(self):
        self._check_is_keyboard(menu_confirmar)
        self._check_buttons_in_row(menu_confirmar, ["Confirmar", "Cancelar"])

    def test_no_empty_rows(self):
        for menu in [menu_principal, menu_miembros, menu_pagos, menu_reportes, menu_estadisticas, menu_exportar, menu_admin, menu_planes, menu_confirmar]:
            assert all(len(row) > 0 for row in menu.keyboard), "Menu has empty row"
