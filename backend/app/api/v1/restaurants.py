import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_verified_user
from app.core.cache import (
    bump_restaurant_version,
    get_cached_list,
    get_cached_restaurant,
    invalidate_restaurant,
    set_cached_list,
    set_cached_restaurant,
)
from app.core.redis import get_redis
from app.database import get_db
from app.models.restaurant import Restaurant
from app.models.user import User
from app.schemas.restaurant import RestaurantCreate, RestaurantOut

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


@router.get("/", response_model=list[RestaurantOut])
async def list_restaurants(
    cuisine: str | None = Query(None),
    discount_type: str | None = Query(None),
    price_range: int | None = Query(None, ge=1, le=4),
    verified_only: bool = Query(False),
    lat: float | None = Query(None),
    lng: float | None = Query(None),
    max_distance_km: float | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # Build a dict of the active params — becomes part of the cache key
    params = {
        "cuisine": cuisine,
        "discount_type": discount_type,
        "price_range": price_range,
        "verified_only": verified_only,
        "lat": lat,
        "lng": lng,
        "max_distance_km": max_distance_km,
        "limit": limit,
        "offset": offset,
    }

    # ── Cache read ──────────────────────────────────────────────────────────
    cached = await get_cached_list(params, redis)
    if cached is not None:
        return cached  # FastAPI validates this against RestaurantOut automatically

    # ── Cache miss → hit the database ───────────────────────────────────────
    filters = [Restaurant.is_active.is_(True)]
    if cuisine:
        filters.append(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    if discount_type:
        filters.append(Restaurant.discount_type == discount_type)
    if price_range:
        filters.append(Restaurant.price_range == price_range)
    if verified_only:
        filters.append(Restaurant.is_verified.is_(True))

    stmt = (
        select(Restaurant)
        .where(and_(*filters))
        .options(selectinload(Restaurant.operating_hours))
        .order_by(Restaurant.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    restaurants = list(result.scalars().all())

    if lat is not None and lng is not None and max_distance_km is not None:
        restaurants = [
            r for r in restaurants
            if r.latitude and r.longitude
            and _haversine_km(lat, lng, r.latitude, r.longitude) <= max_distance_km
        ]

    # Serialize via Pydantic so the cached shape matches RestaurantOut exactly
    data = [RestaurantOut.model_validate(r).model_dump(mode="json") for r in restaurants]

    # ── Cache write ─────────────────────────────────────────────────────────
    await set_cached_list(params, data, redis)

    return data


@router.get("/{restaurant_id}", response_model=RestaurantOut)
async def get_restaurant(
    restaurant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # ── Cache read ──────────────────────────────────────────────────────────
    cached = await get_cached_restaurant(str(restaurant_id), redis)
    if cached is not None:
        return cached

    # ── Cache miss → database ───────────────────────────────────────────────
    result = await db.execute(
        select(Restaurant)
        .where(Restaurant.id == restaurant_id)
        .options(selectinload(Restaurant.operating_hours))
    )
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    data = RestaurantOut.model_validate(restaurant).model_dump(mode="json")

    # ── Cache write ─────────────────────────────────────────────────────────
    await set_cached_restaurant(str(restaurant_id), data, redis)

    return data


@router.post("/", response_model=RestaurantOut, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    payload: RestaurantCreate,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    restaurant = Restaurant(**payload.model_dump(), submitted_by=current_user.id)
    db.add(restaurant)
    await db.flush()

    # Reload with operating_hours so the response serializer can access the relationship
    result = await db.execute(
        select(Restaurant)
        .where(Restaurant.id == restaurant.id)
        .options(selectinload(Restaurant.operating_hours))
    )
    restaurant = result.scalar_one()

    # Bump version → all existing list caches are now stale
    await bump_restaurant_version(redis)

    return restaurant


@router.patch("/{restaurant_id}/verify", response_model=RestaurantOut)
async def verify_restaurant(
    restaurant_id: uuid.UUID,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    restaurant.is_verified = True
    await db.flush()

    result = await db.execute(
        select(Restaurant)
        .where(Restaurant.id == restaurant_id)
        .options(selectinload(Restaurant.operating_hours))
    )
    restaurant = result.scalar_one()

    # Invalidate this restaurant's individual cache + bust all list caches
    await invalidate_restaurant(str(restaurant_id), redis)
    await bump_restaurant_version(redis)

    return restaurant
