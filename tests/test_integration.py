from datetime import date

import pytest

from config import PLANS
from utils.cache import get_plans, invalidate_plans_cache
from utils.dates import calcular_dias_vencido, calcular_proximo_vencimiento, format_fecha


@pytest.mark.integration
class TestPaymentFlowLogic:
    def test_new_member_due_date_same_day(self):
        input_date = date(2026, 3, 15)
        due = calcular_proximo_vencimiento(input_date)
        assert due == date(2026, 4, 15)

    def test_new_member_due_date_31st_to_30day_month(self):
        input_date = date(2026, 3, 31)
        due = calcular_proximo_vencimiento(input_date)
        assert due == date(2026, 4, 30)

    def test_new_member_due_date_jan_31_to_feb(self):
        input_date = date(2026, 1, 31)
        due = calcular_proximo_vencimiento(input_date)
        assert due == date(2026, 2, 28)

    def test_renewal_within_grace(self):
        last_due = date(2026, 3, 15)
        dias = calcular_dias_vencido(last_due)
        assert isinstance(dias, int)

    def test_plan_consistency(self):
        invalidate_plans_cache()
        plans = get_plans()
        for key, plan in plans.items():
            assert isinstance(plan["price"], int)
            assert isinstance(plan["months"], int)
            assert plan["price"] > 0

    def test_plan_months_match_price_ratio(self):
        price_per_month = PLANS["1"]["price"]
        for key, plan in PLANS.items():
            if key == "1":
                continue
            expected = price_per_month * plan["months"]
            assert plan["price"] <= expected, f"Plan {key} should not cost more than monthly * months"

    def test_format_parse_roundtrip(self):
        from utils.dates import parse_fecha
        d = date(2026, 12, 31)
        formatted = format_fecha(d)
        parsed = parse_fecha(formatted)
        assert parsed == d

    def test_invalid_date_returns_none(self):
        from utils.dates import parse_fecha
        assert parse_fecha("not-a-date") is None
        assert parse_fecha("31-02-2026") is None


class TestGraceLogic:
    def test_gracia_late_boundary(self):
        from utils.dates import es_gracia, es_tardio
        hoy = date.today()
        vence_hoy = hoy
        assert not es_gracia(vence_hoy)
        assert not es_tardio(vence_hoy)

    def test_vencimiento_con_gracia_dentro(self):
        from utils.dates import calcular_vencimiento_con_gracia
        fecha_pago = date(2026, 3, 15)
        nuevo, grace = calcular_vencimiento_con_gracia(fecha_pago, 3)
        assert grace is True
        assert nuevo.month == fecha_pago.month + 1 or (fecha_pago.month == 12 and nuevo.month == 1)

    def test_vencimiento_con_gracia_fuera(self):
        from utils.dates import calcular_vencimiento_con_gracia
        fecha_pago = date(2026, 3, 15)
        nuevo, grace = calcular_vencimiento_con_gracia(fecha_pago, 10)
        assert grace is False
