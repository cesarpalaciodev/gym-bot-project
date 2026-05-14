from utils.auth import ROLE_HIERARCHY


class TestRoleHierarchy:
    def test_super_admin_highest(self):
        assert ROLE_HIERARCHY["super_admin"] == 3

    def test_admin_middle(self):
        assert ROLE_HIERARCHY["admin"] == 2

    def test_viewer_lowest(self):
        assert ROLE_HIERARCHY["viewer"] == 1

    def test_unknown_role_is_zero(self):
        assert ROLE_HIERARCHY.get("fake_role", 0) == 0

    def test_all_expected_roles_present(self):
        for role in ["super_admin", "admin", "viewer"]:
            assert role in ROLE_HIERARCHY
