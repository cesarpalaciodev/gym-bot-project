import logging
import time
from collections import defaultdict
from typing import Any

from config import REDIS_URL

logger = logging.getLogger(__name__)

_redis: Any = None
_fallback_store: defaultdict[int, list[float]] = defaultdict(list)


async def _get_redis() -> Any:
    global _redis
    if _redis is None and REDIS_URL:
        try:
            import aioredis

            _redis = await aioredis.from_url(REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
        except ImportError:
            pass
    return _redis


async def check_rate_limit(user_id: int, max_per_window: int = 10, window_seconds: int = 5) -> bool:
    now = time.time()
    redis_conn = await _get_redis()

    if redis_conn:
        try:
            key = f"rate_limit:{user_id}"
            cutoff = now - window_seconds
            await redis_conn.zremrangebyscore(key, 0, cutoff)
            count = await redis_conn.zcard(key)
            if count >= max_per_window:
                return False
            await redis_conn.zadd(key, {str(now): now})
            await redis_conn.expire(key, window_seconds)
            return True
        except Exception as e:
            logger.warning(f"Redis rate limit error, falling back to memory: {e}")

    window_start = now - window_seconds
    _fallback_store[user_id] = [t for t in _fallback_store[user_id] if t > window_start]
    if len(_fallback_store[user_id]) >= max_per_window:
        return False
    _fallback_store[user_id].append(now)
    return True


def check_rate_limit_sync(user_id: int, max_per_window: int = 10, window_seconds: int = 5) -> bool:
    now = time.time()
    window_start = now - window_seconds
    _fallback_store[user_id] = [t for t in _fallback_store[user_id] if t > window_start]
    if len(_fallback_store[user_id]) >= max_per_window:
        return False
    _fallback_store[user_id].append(now)
    return True


async def close_rate_limiter() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
