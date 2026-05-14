from __future__ import annotations

from functools import lru_cache
from typing import Any

from config import PLANS


@lru_cache(maxsize=1)
def get_plans() -> dict[str, Any]:
    return PLANS


@lru_cache(maxsize=128)
def get_plan_by_key(key: str) -> dict[str, Any] | None:
    return PLANS.get(key)


def invalidate_plans_cache() -> None:
    get_plans.cache_clear()
    get_plan_by_key.cache_clear()
