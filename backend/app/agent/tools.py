"""
OpenAI tool schemas + implementation functions for the NYU Bites agent.

Each tool function receives validated arguments and returns a plain dict
that is serialised back to the model as a tool_result message.
"""
import math
import uuid as _uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.restaurant import OperatingHours, Restaurant

# NYC is UTC-5 (EST) / UTC-4 (EDT). Use a fixed offset; good enough for this use-case.
NYC_TZ = timezone(timedelta(hours=-4))  # EDT — flip to -5 in winter


# ── Tool schemas (passed to OpenAI) ──────────────────────────────────────────

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_restaurants",
            "description": (
                "Search the NYU Bites database for restaurants near campus that offer student discounts. "
                "Returns name, cuisine, address, discount details, price range, and today's hours. "
                "Use this first when a student asks for food recommendations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cuisine": {
                        "type": "string",
                        "description": "Cuisine type to search for, e.g. 'pizza', 'mexican', 'cafe'",
                    },
                    "max_price_range": {
                        "type": "integer",
                        "description": "Maximum price range: 1=$  2=$$  3=$$$  4=$$$$",
                        "minimum": 1,
                        "maximum": 4,
                    },
                    "discount_type": {
                        "type": "string",
                        "enum": ["percentage", "fixed", "free_item", "special_menu"],
                        "description": "Only return restaurants with this discount type",
                    },
                    "open_now": {
                        "type": "boolean",
                        "description": "If true, only return restaurants that are currently open",
                    },
                    "lat": {"type": "number", "description": "User latitude for distance filtering"},
                    "lng": {"type": "number", "description": "User longitude for distance filtering"},
                    "max_distance_km": {"type": "number", "description": "Max radius in km from user"},
                    "limit": {"type": "integer", "default": 6},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_by_discount",
            "description": "Filter restaurants by the type of student discount they offer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "discount_type": {
                        "type": "string",
                        "enum": ["percentage", "fixed", "free_item", "special_menu"],
                        "description": "percentage=% off total, fixed=$ off, free_item=free food/drink, special_menu=student pricing",
                    },
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["discount_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_hours",
            "description": (
                "Check whether a specific restaurant is currently open or closed. "
                "Uses the restaurant's stored hours. Call this when the student asks "
                "if a place is open right now or at a specific time."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_id": {
                        "type": "string",
                        "description": "UUID of the restaurant from a previous search result",
                    },
                },
                "required": ["restaurant_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rank_proximity",
            "description": "Re-rank a list of restaurants by walking distance from the user's current location. Use after search_restaurants when the student wants the closest options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of restaurant UUIDs to rank (from search results)",
                    },
                    "lat": {"type": "number"},
                    "lng": {"type": "number"},
                },
                "required": ["restaurant_ids", "lat", "lng"],
            },
        },
    },
]


# ── Shared helpers ────────────────────────────────────────────────────────────

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _nyc_now() -> datetime:
    return datetime.now(NYC_TZ)


def _is_open_now(hours_rows: list[OperatingHours]) -> bool | None:
    """
    Returns True/False/None (None = no hours data).
    Checks the current NYC weekday and time against stored OperatingHours rows.
    """
    if not hours_rows:
        return None

    now = _nyc_now()
    today = now.weekday()  # 0=Monday … 6=Sunday
    current_time = now.time().replace(tzinfo=None)

    for row in hours_rows:
        if row.day_of_week != today:
            continue
        if row.is_closed:
            return False
        if row.open_time and row.close_time:
            # Handle past-midnight close times (e.g. open 22:00, close 02:00)
            if row.close_time < row.open_time:
                return current_time >= row.open_time or current_time <= row.close_time
            return row.open_time <= current_time <= row.close_time
    return None


def _format_hours(hours_rows: list[OperatingHours]) -> dict:
    """Return today's hours as a human-readable string."""
    today = _nyc_now().weekday()
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    result = {}
    for row in hours_rows:
        label = days[row.day_of_week]
        if row.is_closed:
            result[label] = "Closed"
        elif row.open_time and row.close_time:
            result[label] = f"{row.open_time.strftime('%I:%M %p')} – {row.close_time.strftime('%I:%M %p')}"
        else:
            result[label] = "Hours unknown"
    return result


# ── Tool implementations ──────────────────────────────────────────────────────

async def search_restaurants(args: dict, db: AsyncSession) -> dict:
    filters = [Restaurant.is_active.is_(True), Restaurant.is_verified.is_(True)]

    if cuisine := args.get("cuisine"):
        filters.append(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    if max_price := args.get("max_price_range"):
        filters.append(Restaurant.price_range <= max_price)
    if discount_type := args.get("discount_type"):
        filters.append(Restaurant.discount_type == discount_type)

    stmt = (
        select(Restaurant)
        .where(and_(*filters))
        .options(selectinload(Restaurant.operating_hours))
        .limit(args.get("limit", 6))
    )
    result = await db.execute(stmt)
    restaurants = list(result.scalars().all())

    # Distance filter
    lat, lng, max_dist = args.get("lat"), args.get("lng"), args.get("max_distance_km")
    if lat and lng and max_dist:
        restaurants = [
            r for r in restaurants
            if r.latitude and r.longitude
            and _haversine_km(lat, lng, r.latitude, r.longitude) <= max_dist
        ]

    # open_now filter
    if args.get("open_now"):
        restaurants = [r for r in restaurants if _is_open_now(r.operating_hours) is True]

    price_labels = {1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}

    return {
        "current_nyc_time": _nyc_now().strftime("%A %I:%M %p"),
        "count": len(restaurants),
        "restaurants": [
            {
                "id": str(r.id),
                "name": r.name,
                "cuisine_type": r.cuisine_type,
                "address": r.address,
                "price_range": price_labels.get(r.price_range, "?"),
                "discount_type": r.discount_type,
                "discount_details": r.discount_details,
                "discount_conditions": r.discount_conditions,
                "open_now": _is_open_now(r.operating_hours),
                "todays_hours": next(
                    (
                        f"{h.open_time.strftime('%I:%M %p')} – {h.close_time.strftime('%I:%M %p')}"
                        for h in r.operating_hours
                        if h.day_of_week == _nyc_now().weekday() and not h.is_closed
                    ),
                    "Hours not available",
                ),
                "distance_km": (
                    round(_haversine_km(lat, lng, r.latitude, r.longitude), 2)
                    if lat and lng and r.latitude and r.longitude
                    else None
                ),
            }
            for r in restaurants
        ],
    }


async def filter_by_discount(args: dict, db: AsyncSession) -> dict:
    result = await db.execute(
        select(Restaurant)
        .where(
            Restaurant.is_active.is_(True),
            Restaurant.discount_type == args["discount_type"],
        )
        .limit(args.get("limit", 10))
    )
    restaurants = result.scalars().all()

    type_descriptions = {
        "percentage": "% off your total bill",
        "fixed": "fixed $ amount off",
        "free_item": "free food or drink item",
        "special_menu": "special student pricing",
    }

    return {
        "discount_type": args["discount_type"],
        "description": type_descriptions.get(args["discount_type"], ""),
        "restaurants": [
            {
                "id": str(r.id),
                "name": r.name,
                "discount_details": r.discount_details,
                "discount_conditions": r.discount_conditions,
                "discount_value": r.discount_value,
            }
            for r in restaurants
        ],
    }


async def check_hours(args: dict, db: AsyncSession) -> dict:
    """
    Check if a restaurant is open now.
    Falls back to our local OperatingHours data if no Google Place ID is stored.
    """
    result = await db.execute(
        select(Restaurant)
        .where(Restaurant.id == _uuid.UUID(args["restaurant_id"]))
        .options(selectinload(Restaurant.operating_hours))
    )
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        return {"error": "Restaurant not found"}

    now = _nyc_now()

    # Try Google Places first if we have the credentials
    if restaurant.google_place_id and settings.google_places_api_key:
        url = (
            f"https://maps.googleapis.com/maps/api/place/details/json"
            f"?place_id={restaurant.google_place_id}"
            f"&fields=opening_hours"
            f"&key={settings.google_places_api_key}"
        )
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=5.0)
                data = resp.json()
            hours = data.get("result", {}).get("opening_hours", {})
            return {
                "restaurant": restaurant.name,
                "source": "google_places",
                "open_now": hours.get("open_now"),
                "current_nyc_time": now.strftime("%A %I:%M %p"),
            }
        except Exception:
            pass  # fall through to local hours

    # Local DB hours fallback
    open_status = _is_open_now(restaurant.operating_hours)
    hours_today = next(
        (
            f"{h.open_time.strftime('%I:%M %p')} – {h.close_time.strftime('%I:%M %p')}"
            for h in restaurant.operating_hours
            if h.day_of_week == now.weekday() and not h.is_closed
        ),
        "No hours listed for today",
    )

    return {
        "restaurant": restaurant.name,
        "source": "local_db",
        "open_now": open_status,
        "current_nyc_time": now.strftime("%A %I:%M %p"),
        "hours_today": hours_today,
    }


async def rank_proximity(args: dict, db: AsyncSession) -> dict:
    ids = [_uuid.UUID(rid) for rid in args["restaurant_ids"]]
    result = await db.execute(select(Restaurant).where(Restaurant.id.in_(ids)))
    restaurants = result.scalars().all()

    lat, lng = args["lat"], args["lng"]
    ranked = sorted(
        [r for r in restaurants if r.latitude and r.longitude],
        key=lambda r: _haversine_km(lat, lng, r.latitude, r.longitude),
    )

    return {
        "ranked_by": "walking distance from your location",
        "ranked": [
            {
                "id": str(r.id),
                "name": r.name,
                "address": r.address,
                "distance_km": round(_haversine_km(lat, lng, r.latitude, r.longitude), 2),
                "distance_min_walk": round(_haversine_km(lat, lng, r.latitude, r.longitude) * 12),
            }
            for r in ranked
        ],
    }


# Dispatch table
TOOL_HANDLERS: dict[str, Any] = {
    "search_restaurants": search_restaurants,
    "filter_by_discount": filter_by_discount,
    "check_hours": check_hours,
    "rank_proximity": rank_proximity,
}
