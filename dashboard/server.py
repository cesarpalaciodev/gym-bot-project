from __future__ import annotations

import logging
import os
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorCollection

from config import DASHBOARD_PORT
from dashboard.auth import (
    COOKIE_NAME,
    _verify_admin,
    create_session,
    generate_csrf_token,
    get_current_admin,
    verify_csrf_token,
)
from database import get_collection
from utils.dates import calcular_dias_vencido, format_fecha

logger = logging.getLogger(__name__)

app = FastAPI(title="Gym Bot Dashboard", version="2.0.0", docs_url="/docs", redoc_url="/redoc")

templates = Jinja2Templates(directory="dashboard/templates")
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

CSRF_EXEMPT_PATHS = {"/login"}


@app.middleware("http")
async def csrf_middleware(request: Request, call_next: Any) -> Any:
    if request.method in ("POST", "PUT", "DELETE") and request.url.path not in CSRF_EXEMPT_PATHS:
        csrf = request.headers.get("X-CSRF-Token")
        if not csrf or not verify_csrf_token(csrf):
            from fastapi.responses import JSONResponse

            return JSONResponse(status_code=403, content={"detail": "CSRF token invalido"})
    return await call_next(request)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next: Any) -> Any:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.get("/csrf-token", tags=["auth"])
async def csrf_token_endpoint(request: Request) -> dict[str, str]:
    return {"csrf_token": generate_csrf_token()}


async def _get_member_status(
    member: dict[str, Any],
    payments_col: AsyncIOMotorCollection[Any],
) -> dict[str, Any | None]:
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


@app.get("/login", response_class=HTMLResponse, tags=["auth"])
async def login_page(request: Request) -> Any:
    admin = await get_current_admin(request)
    if admin:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {})


@app.post("/login", tags=["auth"])
async def login_post(request: Request, chat_id: int = Form(...)) -> Any:
    admin = await _verify_admin(chat_id)
    if not admin:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Chat ID no autorizado"},
        )
    token = await create_session(chat_id)
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=86400 * 7,
        httponly=True,
        samesite="lax",
        secure=os.getenv("ENVIRONMENT") == "production",
    )
    return resp


@app.get("/logout", tags=["auth"])
async def logout() -> RedirectResponse:
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(COOKIE_NAME)
    return resp


async def _get_dashboard_data() -> dict[str, Any]:
    members_col = await get_collection("members")
    payments_col = await get_collection("payments")

    today = date.today()
    month_start = today.replace(day=1)
    month_start_str = format_fecha(month_start)

    total_active = await members_col.count_documents({"active": True})

    pipeline: Sequence[Mapping[str, Any]] = [
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

    return {
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
    }


@app.get("/")
async def index(request: Request) -> Any:
    admin = await get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/login", status_code=303)
    data = await _get_dashboard_data()
    return templates.TemplateResponse(request, "index.html", {"admin": admin, **data})


@app.get("/dashboard/stats")
async def stats_page(request: Request) -> Any:
    admin = await get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "stats.html", {"admin": admin})


@app.get("/dashboard/members")
async def members_page(request: Request) -> Any:
    admin = await get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/login", status_code=303)
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
    return templates.TemplateResponse(request, "members.html", {"admin": admin, "members": result})


@app.get("/dashboard/payments")
async def payments_page(request: Request, page: int = Query(1, ge=1)) -> Any:
    admin = await get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/login", status_code=303)
    payments_col = await get_collection("payments")
    limit = 20
    skip = (page - 1) * limit
    total = await payments_col.count_documents({})
    cur = payments_col.find().sort("payment_date", -1).skip(skip).limit(limit)
    payments = await cur.to_list(length=limit)
    return templates.TemplateResponse(
        request,
        "payments.html",
        {
            "admin": admin,
            "payments": [
                {
                    "member_name": p.get("member_name", ""),
                    "amount": p.get("amount", 0),
                    "payment_date": p.get("payment_date", ""),
                    "plan": p.get("plan", ""),
                    "due_date": p.get("due_date", ""),
                }
                for p in payments
            ],
            "page": page,
            "total": total,
            "pages": (total + limit - 1) // limit,
        },
    )


@app.get("/api/stats")
async def api_stats(request: Request) -> dict[str, Any]:
    admin = await get_current_admin(request)
    if not admin:
        return {"error": "Unauthorized"}
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

    pipe_cur: Sequence[Mapping[str, Any]] = [
        {"$match": {"payment_date": {"$gte": month_start_str}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    cur = payments_col.aggregate(pipe_cur)
    res = await cur.to_list(length=1)
    monthly_income = res[0]["total"] if res else 0

    pipe_prev: Sequence[Mapping[str, Any]] = [
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
async def api_members(request: Request) -> Any:
    admin = await get_current_admin(request)
    if not admin:
        return {"error": "Unauthorized"}
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
async def api_payments(
    request: Request, limit: int = Query(20, ge=1, le=100), page: int = Query(1, ge=1)
) -> dict[str, Any]:
    admin = await get_current_admin(request)
    if not admin:
        return {"error": "Unauthorized"}
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


@app.get("/dashboard/health")
async def health_page(request: Request) -> Any:
    admin = await get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/login", status_code=303)
    try:
        db = await get_collection("members")
        await db.find_one({}, {"_id": 1})
        db_status = "connected"
    except Exception:
        logger.exception("Health check failed for health page")
        db_status = "disconnected"
    return templates.TemplateResponse(
        request,
        "health.html",
        {"admin": admin, "db_status": db_status},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    try:
        db = await get_collection("members")
        await db.find_one({}, {"_id": 1})
        db_status = "connected"
    except Exception:
        logger.exception("Health check failed")
        db_status = "disconnected"
    return {"status": "ok", "db": db_status}


def start_dashboard() -> None:
    import uvicorn

    port = DASHBOARD_PORT
    logger.info("Iniciando dashboard en puerto %s", port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
