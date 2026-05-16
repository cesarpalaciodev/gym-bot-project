"""FastAPI dashboard for Gym Bot."""

from __future__ import annotations

import logging
from datetime import date, datetime

from fastapi import FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import DASHBOARD_PORT
from database import get_collection
from utils.dates import calcular_dias_vencido, format_fecha

logger = logging.getLogger(__name__)

app = FastAPI(title="Gym Bot Dashboard")

templates = Jinja2Templates(directory="dashboard/templates")
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")


async def _get_member_status(
    member: dict,
    payments_col,
) -> dict:
    latest = await payments_col.find_one(
        {"member_id": str(member["_id"])},
        sort=[("payment_date", -1)],
    )
    if not latest or not latest.get("due_date"):
        return {"status": "sin_pago", "due_date": None, "days_overdue": 0}

    due = datetime.strptime(latest["due_date"], "%Y-%m-%d").date()
    days = calcular_dias_vencido(due)

    if days == 0:
        s = "al_dia"
    elif days <= 4:
        s = "gracia"
    else:
        s = "vencido"

    return {"status": s, "due_date": latest["due_date"], "days_overdue": days}


@app.get("/")
async def index(request: Request):
    members_col = await get_collection("members")
    payments_col = await get_collection("payments")

    today = date.today()
    month_start = today.replace(day=1)
    month_start_str = format_fecha(month_start)

    total_active = await members_col.count_documents({"active": True})

    pipeline = [
        {"$match": {"payment_date": {"$gte": month_start_str}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    cur = payments_col.aggregate(pipeline)
    res = await cur.to_list(length=1)
    monthly_income = res[0]["total"] if res else 0

    active_members = await members_col.find({"active": True}).to_list(length=None)
    in_grace = 0
    overdue = 0
    for m in active_members:
        info = await _get_member_status(m, payments_col)
        if info["status"] == "gracia":
            in_grace += 1
        elif info["status"] == "vencido":
            overdue += 1

    recent = await payments_col.find().sort("payment_date", -1).limit(10).to_list(length=10)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "total_active": total_active,
            "in_grace": in_grace,
            "overdue": overdue,
            "monthly_income": monthly_income,
            "recent_payments": [
                {
                    "member_name": p.get("member_name", ""),
                    "amount": p.get("amount", 0),
                    "payment_date": p.get("payment_date", ""),
                    "plan": p.get("plan", ""),
                    "due_date": p.get("due_date", ""),
                }
                for p in recent
            ],
        },
    )


@app.get("/api/stats")
async def api_stats():
    members_col = await get_collection("members")
    payments_col = await get_collection("payments")

    today = date.today()
    month_start = today.replace(day=1)
    month_start_str = format_fecha(month_start)

    if today.month == 1:
        prev_start = today.replace(year=today.year - 1, month=12, day=1)
    else:
        prev_start = today.replace(month=today.month - 1, day=1)
    prev_start_str = format_fecha(prev_start)

    total_active = await members_col.count_documents({"active": True})

    pipe_cur = [
        {"$match": {"payment_date": {"$gte": month_start_str}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    cur = payments_col.aggregate(pipe_cur)
    res = await cur.to_list(length=1)
    monthly_income = res[0]["total"] if res else 0

    pipe_prev = [
        {
            "$match": {
                "payment_date": {"$gte": prev_start_str, "$lt": month_start_str},
            }
        },
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    cur2 = payments_col.aggregate(pipe_prev)
    res2 = await cur2.to_list(length=1)
    prev_income = res2[0]["total"] if res2 else 0

    active_members = await members_col.find({"active": True}).to_list(length=None)
    in_grace = 0
    overdue = 0
    for m in active_members:
        info = await _get_member_status(m, payments_col)
        if info["status"] == "gracia":
            in_grace += 1
        elif info["status"] == "vencido":
            overdue += 1

    if prev_income > 0:
        change = round(((monthly_income - prev_income) / prev_income) * 100, 1)
    else:
        change = 100.0 if monthly_income > 0 else 0.0

    return {
        "active_members": total_active,
        "in_grace": in_grace,
        "overdue": overdue,
        "monthly_income": monthly_income,
        "previous_month_income": prev_income,
        "income_change_pct": change,
    }


@app.get("/api/members")
async def api_members():
    members_col = await get_collection("members")
    payments_col = await get_collection("payments")

    active = await members_col.find({"active": True}).to_list(length=None)
    result = []
    for m in active:
        info = await _get_member_status(m, payments_col)
        result.append(
            {
                "id": str(m["_id"]),
                "name": m.get("name", ""),
                "phone": m.get("phone"),
                "status": info["status"],
                "due_date": info["due_date"],
                "days_overdue": info["days_overdue"],
            }
        )
    return result


@app.get("/api/payments")
async def api_payments(limit: int = Query(20, ge=1, le=100), page: int = Query(1, ge=1)):
    payments_col = await get_collection("payments")

    skip = (page - 1) * limit
    total = await payments_col.count_documents({})

    cur = payments_col.find().sort("payment_date", -1).skip(skip).limit(limit)
    payments = await cur.to_list(length=limit)

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "data": [
            {
                "id": str(p["_id"]),
                "member_name": p.get("member_name", ""),
                "amount": p.get("amount", 0),
                "payment_date": p.get("payment_date", ""),
                "plan": p.get("plan", ""),
                "due_date": p.get("due_date", ""),
                "grace_period": p.get("grace_period", False),
            }
            for p in payments
        ],
    }


@app.get("/health")
async def health():
    try:
        db = await get_collection("members")
        await db.find_one({}, {"_id": 1})
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {"status": "ok", "db": db_status}


def start_dashboard() -> None:
    import uvicorn

    port = DASHBOARD_PORT
    logger.info("Iniciando dashboard en puerto %s", port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
