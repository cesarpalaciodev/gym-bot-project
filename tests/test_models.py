from datetime import datetime

from models.admin import Admin
from models.member import Member
from models.payment import Payment


class TestMember:
    def test_create_member(self):
        m = Member(name="Test User", phone="3101234567")
        assert m.name == "Test User"
        assert m.phone == "3101234567"
        assert m.active is True

    def test_to_dict(self):
        m = Member(name="Test", phone="3100000000")
        d = m.to_dict()
        assert d["name"] == "Test"
        assert d["phone"] == "3100000000"
        assert d["active"] is True
        assert "_id" not in d
        assert "created_at" in d

    def test_to_dict_with_id(self):
        m = Member(name="Test", phone="3100000000", _id="abc123")
        d = m.to_dict()
        assert d["_id"] == "abc123"

    def test_from_dict(self):
        now = datetime.utcnow()
        d = {"name": "Test", "phone": "3100000000", "active": True, "created_at": now, "updated_at": now}
        m = Member.from_dict(d)
        assert m.name == "Test"
        assert m.phone == "3100000000"
        assert m.active is True

    def test_from_dict_empty(self):
        m = Member.from_dict({})
        assert m.name == ""
        assert m.phone is None
        assert m.active is True

    def test_default_phone_none(self):
        m = Member(name="No Phone")
        assert m.phone is None


class TestPayment:
    def test_create_payment(self):
        p = Payment(
            member_id="abc123",
            member_name="Test",
            payment_date="2026-01-15",
            amount=500,
            plan="Mensual",
            due_date="2026-02-15",
        )
        assert p.member_id == "abc123"
        assert p.member_name == "Test"
        assert p.amount == 500
        assert p.grace_period is False

    def test_to_dict(self):
        p = Payment(
            member_id="abc",
            member_name="Test",
            payment_date="2026-01-15",
            amount=500,
            plan="Mensual",
            due_date="2026-02-15",
        )
        d = p.to_dict()
        assert d["amount"] == 500
        assert d["plan"] == "Mensual"
        assert d["grace_period"] is False
        assert d["months"] == 1

    def test_from_dict(self):
        d = {
            "member_id": "abc",
            "member_name": "Test",
            "payment_date": "2026-01-15",
            "amount": 500,
            "plan": "Mensual",
            "due_date": "2026-02-15",
        }
        p = Payment.from_dict(d)
        assert p.member_id == "abc"
        assert p.amount == 500
        assert p.plan == "Mensual"

    def test_from_dict_defaults(self):
        p = Payment.from_dict({})
        assert p.amount == 0
        assert p.plan == ""
        assert p.grace_period is False
        assert p.months == 1


class TestAdmin:
    def test_create_admin(self):
        a = Admin(telegram_id=12345, name="Admin User")
        assert a.telegram_id == 12345
        assert a.name == "Admin User"
        assert a.role == "admin"

    def test_to_dict(self):
        a = Admin(telegram_id=12345, name="Admin", role="super_admin")
        d = a.to_dict()
        assert d["telegram_id"] == 12345
        assert d["role"] == "super_admin"

    def test_from_dict(self):
        d = {"telegram_id": 67890, "name": "Test", "role": "viewer"}
        a = Admin.from_dict(d)
        assert a.telegram_id == 67890
        assert a.role == "viewer"

    def test_from_dict_defaults(self):
        d = {"telegram_id": 111, "name": "Test"}
        a = Admin.from_dict(d)
        assert a.telegram_id == 111
        assert a.role == "admin"
