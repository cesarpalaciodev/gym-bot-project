from config import ADMIN_ROLES, GRACE_DAYS, LATE_DAYS, PLANS


class TestPlans:
    def test_has_all_plans(self):
        assert len(PLANS) >= 4

    def test_mensual_price(self):
        assert PLANS["1"]["price"] == 500
        assert PLANS["1"]["name"] == "Mensual"
        assert PLANS["1"]["months"] == 1

    def test_trimestral(self):
        p = PLANS["2"]
        assert p["name"] == "Trimestral"
        assert p["months"] == 3
        assert p["price"] == 1350

    def test_semestral(self):
        p = PLANS["3"]
        assert p["name"] == "Semestral"
        assert p["months"] == 6
        assert p["price"] == 2500

    def test_anual(self):
        p = PLANS["4"]
        assert p["name"] == "Anual"
        assert p["months"] == 12
        assert p["price"] == 4500

    def test_all_prices_positive(self):
        for key, plan in PLANS.items():
            assert plan["price"] > 0, f"Plan {key} tiene precio 0"
            assert plan["months"] > 0, f"Plan {key} tiene months 0"

    def test_all_have_required_keys(self):
        for key, plan in PLANS.items():
            assert "name" in plan
            assert "months" in plan
            assert "price" in plan


class TestGraceDays:
    def test_grace_days(self):
        assert GRACE_DAYS == 4

    def test_late_days(self):
        assert LATE_DAYS == 5


class TestAdminRoles:
    def test_has_super_admin(self):
        assert "super_admin" in ADMIN_ROLES

    def test_has_admin(self):
        assert "admin" in ADMIN_ROLES

    def test_has_viewer(self):
        assert "viewer" in ADMIN_ROLES

    def test_super_admin_has_all(self):
        assert "all" in ADMIN_ROLES["super_admin"]

    def test_admin_permissions(self):
        perms = ADMIN_ROLES["admin"]
        assert "members" in perms
        assert "payments" in perms
        assert "reports" in perms
