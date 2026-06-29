"""
Redis cache helpers for NYU Bites.

Key schema
──────────
  nyubites:restaurant:{id}              single restaurant, TTL 10 min
  nyubites:restaurants:v{ver}:{hash}    list results, TTL 5 min
  nyubites:restaurants:version          integer version counter

Why a version counter for lists?
  When any restaurant is created or updated we increment the version.
  All existing list cache keys were built with the old version so they
  are never hit again — they just expire naturally (no expensive SCAN+DEL).
"""
import hashlib
import json
from typing import Any

from redis.asyncio import Redis

RESTAURANT_TTL = 600       # 10 minutes — single restaurant
RESTAURANT_LIST_TTL = 300  # 5 minutes  — search results

_VERSION_KEY = "nyubites:restaurants:version"
_RESTAURANT_KEY = "nyubites:restaurant:{id}"
_LIST_KEY = "nyubites:restaurants:v{version}:{params_hash}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _params_hash(params: dict) -> str:
    """Stable hash of a query-params dict → short hex string for the cache key."""
    serialized = json.dumps(params, sort_keys=True, default=str)
    return hashlib.md5(serialized.encode()).hexdigest()[:16]


async def _get_version(redis: Redis) -> int:
    v = await redis.get(_VERSION_KEY)
    return int(v) if v else 0


async def bump_restaurant_version(redis: Redis) -> int:
    """Increment the version counter. Call after any write that changes restaurant data."""
    return await redis.incr(_VERSION_KEY)


# ── Single restaurant ─────────────────────────────────────────────────────────

async def get_cached_restaurant(restaurant_id: str, redis: Redis) -> dict | None:
    raw = await redis.get(_RESTAURANT_KEY.format(id=restaurant_id))
    return json.loads(raw) if raw else None


async def set_cached_restaurant(restaurant_id: str, data: dict, redis: Redis) -> None:
    await redis.set(
        _RESTAURANT_KEY.format(id=restaurant_id),
        json.dumps(data, default=str),
        ex=RESTAURANT_TTL,
    )


async def invalidate_restaurant(restaurant_id: str, redis: Redis) -> None:
    await redis.delete(_RESTAURANT_KEY.format(id=restaurant_id))


# ── Restaurant list ───────────────────────────────────────────────────────────

async def get_cached_list(params: dict, redis: Redis) -> list[dict] | None:
    version = await _get_version(redis)
    key = _LIST_KEY.format(version=version, params_hash=_params_hash(params))
    raw = await redis.get(key)
    return json.loads(raw) if raw else None


async def set_cached_list(params: dict, data: list[dict], redis: Redis) -> None:
    version = await _get_version(redis)
    key = _LIST_KEY.format(version=version, params_hash=_params_hash(params))
    await redis.set(key, json.dumps(data, default=str), ex=RESTAURANT_LIST_TTL)
