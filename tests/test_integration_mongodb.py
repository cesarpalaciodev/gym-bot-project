from datetime import date

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from testcontainers.mongodb import MongoDbContainer

from models.admin import Admin
from models.member import Member
from models.payment import Payment
from utils.dates import calcular_dias_vencido, calcular_proximo_vencimiento


@pytest.fixture(scope="module")
def mongo_container():
    with MongoDbContainer("mongo:7") as mongo:
        yield mongo


@pytest.fixture
async def mongo_client(mongo_container):
    uri = mongo_container.get_connection_url()
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
    yield client
    client.close()


@pytest.fixture
async def db(mongo_client):
    database = mongo_client["gym_test"]
    yield database
    # Clean all collections after each test
    await database.members.delete_many({})
    await database.payments.delete_many({})
    await database.admins.delete_many({})


# =====================================================
# MEMBER CRUD (5 tests)
# =====================================================


@pytest.mark.integration
class TestMemberCRUD:
    async def test_insert_member_and_find(self, db):
        member = Member(name="Juan Perez", phone="555-0101")
        result = await db.members.insert_one(member.to_dict())
        found = await db.members.find_one({"_id": result.inserted_id})
        assert found is not None
        assert found["name"] == "Juan Perez"
        assert found["phone"] == "555-0101"

    async def test_insert_multiple_members_and_count(self, db):
        members = [
            Member(name="Ana").to_dict(),
            Member(name="Luis").to_dict(),
            Member(name="Sofia").to_dict(),
        ]
        await db.members.insert_many(members)
        count = await db.members.count_documents({})
        assert count == 3

    async def test_find_member_by_name(self, db):
        await db.members.insert_one(Member(name="Carlos Gomez").to_dict())
        found = await db.members.find_one({"name": "Carlos Gomez"})
        assert found is not None
        assert found["name"] == "Carlos Gomez"

    async def test_delete_member(self, db):
        result = await db.members.insert_one(Member(name="ToDelete").to_dict())
        member_id = result.inserted_id
        del_result = await db.members.delete_one({"_id": member_id})
        assert del_result.deleted_count == 1
        found = await db.members.find_one({"_id": member_id})
        assert found is None

    async def test_update_member_set_inactive(self, db):
        result = await db.members.insert_one(Member(name="Maria").to_dict())
        member_id = result.inserted_id
        await db.members.update_one({"_id": member_id}, {"$set": {"active": False}})
        updated = await db.members.find_one({"_id": member_id})
        assert updated is not None
        assert updated["active"] is False


# =====================================================
# PAYMENT CRUD (5 tests)
# =====================================================


@pytest.mark.integration
class TestPaymentCRUD:
    async def test_insert_payment_and_verify(self, db):
        payment = Payment(
            member_id="m1",
            member_name="Juan",
            payment_date="2026-01-15",
            amount=500,
            plan="Mensual",
            due_date="2026-02-15",
        )
        result = await db.payments.insert_one(payment.to_dict())
        found = await db.payments.find_one({"_id": result.inserted_id})
        assert found is not None
        assert found["amount"] == 500
        assert found["plan"] == "Mensual"

    async def test_get_last_payment_for_member(self, db):
        payments = [
            Payment(
                member_id="m2",
                member_name="Ana",
                payment_date="2026-01-01",
                amount=500,
                plan="Mensual",
                due_date="2026-02-01",
            ),
            Payment(
                member_id="m2",
                member_name="Ana",
                payment_date="2026-02-01",
                amount=500,
                plan="Mensual",
                due_date="2026-03-01",
            ),
            Payment(
                member_id="m2",
                member_name="Ana",
                payment_date="2026-03-01",
                amount=500,
                plan="Mensual",
                due_date="2026-04-01",
            ),
        ]
        await db.payments.insert_many([p.to_dict() for p in payments])

        cursor = db.payments.find({"member_id": "m2"}).sort("payment_date", -1).limit(1)
        last = await cursor.to_list(length=1)
        assert len(last) == 1
        assert last[0]["payment_date"] == "2026-03-01"

    async def test_count_payments_by_member(self, db):
        payments = [
            Payment(
                member_id="m3",
                member_name="Luis",
                payment_date="2026-01-10",
                amount=500,
                plan="Mensual",
                due_date="2026-02-10",
            ),
            Payment(
                member_id="m3",
                member_name="Luis",
                payment_date="2026-02-10",
                amount=500,
                plan="Mensual",
                due_date="2026-03-10",
            ),
        ]
        await db.payments.insert_many([p.to_dict() for p in payments])
        count = await db.payments.count_documents({"member_id": "m3"})
        assert count == 2

    async def test_delete_payments_by_member_id(self, db):
        payments = [
            Payment(
                member_id="m4",
                member_name="Sofia",
                payment_date="2026-01-20",
                amount=500,
                plan="Mensual",
                due_date="2026-02-20",
            ),
            Payment(
                member_id="m4",
                member_name="Sofia",
                payment_date="2026-02-20",
                amount=500,
                plan="Mensual",
                due_date="2026-03-20",
            ),
        ]
        await db.payments.insert_many([p.to_dict() for p in payments])
        del_result = await db.payments.delete_many({"member_id": "m4"})
        assert del_result.deleted_count == 2
        remaining = await db.payments.count_documents({"member_id": "m4"})
        assert remaining == 0

    async def test_payment_with_grace_period_flag(self, db):
        payment = Payment(
            member_id="m5",
            member_name="Grace",
            payment_date="2026-04-01",
            amount=500,
            plan="Mensual",
            due_date="2026-05-01",
            grace_period=True,
        )
        result = await db.payments.insert_one(payment.to_dict())
        found = await db.payments.find_one({"_id": result.inserted_id})
        assert found is not None
        assert found["grace_period"] is True


# =====================================================
# INDEXES (3 tests)
# =====================================================


@pytest.mark.integration
class TestIndexes:
    async def test_members_name_index_exists(self, db):
        await db.members.create_index("name", background=True)
        indexes = await db.members.index_information()
        index_names = [info["key"][0][0] for info in indexes.values()]
        assert "name" in index_names

    async def test_admins_telegram_id_unique_index(self, db):
        await db.admins.create_index("telegram_id", unique=True, background=True)
        await db.admins.insert_one(Admin(telegram_id=100, name="Admin1").to_dict())
        with pytest.raises(DuplicateKeyError):
            await db.admins.insert_one(Admin(telegram_id=100, name="Admin2").to_dict())

    async def test_payments_member_id_index_exists(self, db):
        await db.payments.create_index("member_id", background=True)
        indexes = await db.payments.index_information()
        index_keys = [info["key"] for info in indexes.values()]
        assert any(k == [("member_id", 1)] for k in index_keys)


# =====================================================
# AGGREGATION (3 tests)
# =====================================================


@pytest.mark.integration
class TestAggregation:
    async def test_sum_payments_by_month(self, db):
        payments = [
            Payment(
                member_id="m1",
                member_name="A",
                payment_date="2026-01-15",
                amount=500,
                plan="Mensual",
                due_date="2026-02-15",
            ),
            Payment(
                member_id="m2",
                member_name="B",
                payment_date="2026-01-20",
                amount=1350,
                plan="Trimestral",
                due_date="2026-04-20",
            ),
            Payment(
                member_id="m3",
                member_name="C",
                payment_date="2026-02-10",
                amount=500,
                plan="Mensual",
                due_date="2026-03-10",
            ),
        ]
        await db.payments.insert_many([p.to_dict() for p in payments])

        pipeline = [
            {"$group": {"_id": {"$substr": ["$payment_date", 0, 7]}, "total": {"$sum": "$amount"}}},
            {"$sort": {"_id": 1}},
        ]
        results = await db.payments.aggregate(pipeline).to_list(length=10)
        assert len(results) == 2
        assert results[0]["_id"] == "2026-01"
        assert results[0]["total"] == 1850
        assert results[1]["_id"] == "2026-02"
        assert results[1]["total"] == 500

    async def test_group_payments_by_plan_type(self, db):
        payments = [
            Payment(
                member_id="m1",
                member_name="A",
                payment_date="2026-01-01",
                amount=500,
                plan="Mensual",
                due_date="2026-02-01",
            ),
            Payment(
                member_id="m2",
                member_name="B",
                payment_date="2026-01-01",
                amount=500,
                plan="Mensual",
                due_date="2026-02-01",
            ),
            Payment(
                member_id="m3",
                member_name="C",
                payment_date="2026-01-01",
                amount=1350,
                plan="Trimestral",
                due_date="2026-04-01",
            ),
            Payment(
                member_id="m4",
                member_name="D",
                payment_date="2026-01-01",
                amount=2500,
                plan="Semestral",
                due_date="2026-07-01",
            ),
        ]
        await db.payments.insert_many([p.to_dict() for p in payments])

        pipeline = [
            {"$group": {"_id": "$plan", "count": {"$sum": 1}, "total": {"$sum": "$amount"}}},
            {"$sort": {"_id": 1}},
        ]
        results = await db.payments.aggregate(pipeline).to_list(length=10)
        plan_counts = {r["_id"]: r["count"] for r in results}
        assert plan_counts["Mensual"] == 2
        assert plan_counts["Trimestral"] == 1
        assert plan_counts["Semestral"] == 1
        total_mensual = next(r["total"] for r in results if r["_id"] == "Mensual")
        assert total_mensual == 1000

    async def test_find_members_without_payments(self, db):
        await db.members.insert_many(
            [
                Member(name="ConPago").to_dict(),
                Member(name="SinPago").to_dict(),
                Member(name="OtroSinPago").to_dict(),
            ]
        )
        members_with_payments = await db.members.find({"name": "ConPago"}).to_list(length=10)
        con_pago = members_with_payments[0]

        await db.payments.insert_one(
            Payment(
                member_id=str(con_pago["_id"]),
                member_name="ConPago",
                payment_date="2026-01-01",
                amount=500,
                plan="Mensual",
                due_date="2026-02-01",
            ).to_dict(),
        )

        pipeline = [
            {"$lookup": {"from": "payments", "localField": "_id", "foreignField": "member_id", "as": "pagos"}},
            {"$match": {"pagos": {"$size": 0}}},
            {"$project": {"name": 1}},
        ]
        results = await db.members.aggregate(pipeline).to_list(length=10)
        names = {r["name"] for r in results}
        assert "SinPago" in names
        assert "OtroSinPago" in names
        assert "ConPago" not in names


# =====================================================
# DATE LOGIC + REAL DATA (5 tests)
# =====================================================


@pytest.mark.integration
class TestDateLogicWithRealData:
    async def test_calcular_proximo_vencimiento_with_inserted_payment(self, db):
        payment = Payment(
            member_id="m1",
            member_name="Juan",
            payment_date="2026-03-15",
            amount=500,
            plan="Mensual",
            due_date="2026-04-15",
        )
        await db.payments.insert_one(payment.to_dict())

        fecha_pago = date(2026, 3, 15)
        expected_due = calcular_proximo_vencimiento(fecha_pago)
        assert expected_due == date(2026, 4, 15)

        found = await db.payments.find_one({"member_id": "m1"})
        assert found["due_date"] == "2026-04-15"

    async def test_payment_with_past_due_date_shows_overdue(self, db):
        due = date(2026, 1, 1)
        payment = Payment(
            member_id="m2",
            member_name="Vencido",
            payment_date="2025-12-01",
            amount=500,
            plan="Mensual",
            due_date=due.isoformat(),
        )
        await db.payments.insert_one(payment.to_dict())

        dias_vencido = calcular_dias_vencido(due)
        assert dias_vencido > 0

    async def test_grace_period_edge_case(self, db):
        from config import GRACE_DAYS
        from utils.dates import es_gracia, es_tardio

        hoy = date.today()
        payment = Payment(
            member_id="m3",
            member_name="Gracia",
            payment_date=hoy.isoformat(),
            amount=500,
            plan="Mensual",
            due_date=hoy.isoformat(),
            grace_period=True,
        )
        await db.payments.insert_one(payment.to_dict())

        assert not es_gracia(hoy)
        assert not es_tardio(hoy)

        uno_antes = date(2026, 1, 1)
        p = Payment(
            member_id="m4",
            member_name="Gracia2",
            payment_date="2025-12-15",
            amount=500,
            plan="Mensual",
            due_date=uno_antes.isoformat(),
        )
        await db.payments.insert_one(p.to_dict())

        dias = calcular_dias_vencido(uno_antes)
        if 0 < dias <= GRACE_DAYS:
            assert es_gracia(uno_antes)
        elif dias > GRACE_DAYS:
            assert es_tardio(uno_antes)

    async def test_e2e_member_payment_flow(self, db):
        member = Member(name="E2E User", phone="555-9999")
        member_result = await db.members.insert_one(member.to_dict())
        member_id = member_result.inserted_id

        payment = Payment(
            member_id=str(member_id),
            member_name="E2E User",
            payment_date="2026-05-01",
            amount=500,
            plan="Mensual",
            due_date="2026-06-01",
        )
        await db.payments.insert_one(payment.to_dict())

        found_member = await db.members.find_one({"_id": member_id})
        assert found_member is not None
        assert found_member["name"] == "E2E User"

        found_payment = await db.payments.find_one({"member_id": str(member_id)})
        assert found_payment is not None
        assert found_payment["amount"] == 500
        assert found_payment["plan"] == "Mensual"

    async def test_calcular_dias_vencido_with_stored_due_date(self, db):
        past_due = date(2025, 6, 1)
        payment = Payment(
            member_id="m5",
            member_name="MuyVencido",
            payment_date="2025-05-01",
            amount=500,
            plan="Mensual",
            due_date=past_due.isoformat(),
        )
        await db.payments.insert_one(payment.to_dict())

        found = await db.payments.find_one({"member_id": "m5"})
        assert found is not None
        stored_due = found["due_date"]
        parsed_due = date.fromisoformat(stored_due)
        dias = calcular_dias_vencido(parsed_due)
        assert dias > 30
