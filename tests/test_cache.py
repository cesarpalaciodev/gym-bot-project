from config import PLANS
from utils.cache import get_plan_by_key, get_plans, invalidate_plans_cache


class TestCache:
    def setup_method(self):
        invalidate_plans_cache()

    def test_get_plans(self):
        plans = get_plans()
        assert plans == PLANS
        assert len(plans) >= 4

    def test_get_plan_by_key_valid(self):
        plan = get_plan_by_key("1")
        assert plan is not None
        assert plan["name"] == "Mensual"

    def test_get_plan_by_key_invalid(self):
        plan = get_plan_by_key("999")
        assert plan is None

    def test_get_plan_by_key_empty(self):
        plan = get_plan_by_key("")
        assert plan is None

    def test_cache_hits(self):
        invalidate_plans_cache()
        get_plans()
        get_plans()
        info = get_plans.cache_info()
        assert info.hits >= 0
        assert info.misses > 0

    def test_invalidate(self):
        get_plans()
        invalidate_plans_cache()
        info = get_plans.cache_info()
        assert info.currsize == 0

    def test_plan_prices_match_config(self):
        invalidate_plans_cache()
        for key in PLANS:
            cached = get_plan_by_key(key)
            assert cached["price"] == PLANS[key]["price"]
