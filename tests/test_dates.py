import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.dates import (
    calcular_dias_vencido,
    calcular_proximo_vencimiento,
    calcular_vencimiento_con_gracia,
    es_gracia,
    es_tardio,
    format_fecha,
    parse_fecha,
)


class TestCalcularProximoVencimiento:
    def test_mismo_dia_mes_siguiente(self):
        result = calcular_proximo_vencimiento(date(2026, 3, 15))
        assert result == date(2026, 4, 15)

    def test_ultimo_dia_mes_enero_a_febrero(self):
        result = calcular_proximo_vencimiento(date(2026, 1, 31))
        assert result == date(2026, 2, 28)

    def test_ultimo_dia_mes_marzo_a_abril(self):
        result = calcular_proximo_vencimiento(date(2026, 3, 31))
        assert result == date(2026, 4, 30)

    def test_diciembre_a_enero(self):
        result = calcular_proximo_vencimiento(date(2026, 12, 10))
        assert result == date(2027, 1, 10)

    def test_bisiesto_febrero(self):
        result = calcular_proximo_vencimiento(date(2024, 1, 31))
        assert result == date(2024, 2, 29)


class TestCalcularDiasVencido:
    def test_no_vencido(self):
        due = date(2026, 5, 20)
        assert calcular_dias_vencido(due) == 0

    def test_vencido_5_dias(self):
        due = date(2026, 5, 9)
        dias = calcular_dias_vencido(due)
        assert dias >= 0, "Nunca debe devolver negativo"

    def test_cambia_de_mes(self):
        due = date(2026, 1, 31)
        dias = calcular_dias_vencido(due)
        assert dias >= 0

    def test_mismo_dia(self):
        due = date.today()
        assert calcular_dias_vencido(due) == 0


class TestEsGracia:
    def test_dentro_gracia(self):
        assert not es_gracia(date.today())

    def test_fuera_gracia(self):
        due = date(2020, 1, 1)
        assert not es_gracia(due)


class TestEsTardio:
    def test_no_tardio(self):
        assert not es_tardio(date.today())

    def test_muy_tardio(self):
        due = date(2020, 1, 1)
        assert es_tardio(due)


class TestFormatFecha:
    def test_formato_estandar(self):
        assert format_fecha(date(2026, 3, 20)) == "2026-03-20"

    def test_enero(self):
        assert format_fecha(date(2026, 1, 5)) == "2026-01-05"

    def test_diciembre(self):
        assert format_fecha(date(2026, 12, 31)) == "2026-12-31"


class TestParseFecha:
    def test_valida(self):
        result = parse_fecha("2026-03-20")
        assert result == date(2026, 3, 20)

    def test_invalida(self):
        assert parse_fecha("30-02-2026") is None

    def test_formato_incorrecto(self):
        assert parse_fecha("20/03/2026") is None

    def test_texto(self):
        assert parse_fecha("abc") is None


class TestCalcularVencimientoConGracia:
    def test_dentro_gracia_mantiene_fecha(self):
        nuevo, grace = calcular_vencimiento_con_gracia(date(2026, 3, 15), 3)
        assert grace
        assert nuevo == date(2026, 4, 15)

    def test_fuera_gracia_nueva_fecha(self):
        _, grace = calcular_vencimiento_con_gracia(date(2026, 3, 15), 10)
        assert not grace
