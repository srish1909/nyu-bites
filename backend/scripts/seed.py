"""
Seed script — populates the database with real NYC restaurants near NYU.

All locations are within ~1.5 km of Washington Square Park (40.7308, -74.0003).
Run inside Docker:
  docker exec nyu-bites-api-1 python -m scripts.seed
Or locally (needs DATABASE_URL pointing to the container):
  python -m scripts.seed
"""
import asyncio
import uuid
from datetime import time

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── Connection ─────────────────────────────────────────────────────────────────
# Inside Docker the hostname is "db"; override with DATABASE_URL env var if needed
import os
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://nyubites:changeme@db:5432/nyubites"
)

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# ── Data ───────────────────────────────────────────────────────────────────────
# Each restaurant dict maps directly to the Restaurant ORM columns.
# operating_hours is a list of (day_of_week, open_time, close_time)
#   day_of_week: 0=Monday … 6=Sunday
#   None open/close_time with is_closed=True means closed that day.

RESTAURANTS = [
    {
        "name": "Joe's Pizza",
        "cuisine_type": "Pizza",
        "address": "7 Carmine St, New York, NY 10014",
        "latitude": 40.7305,
        "longitude": -74.0021,
        "discount_details": "10% off any slice with NYU ID",
        "discount_conditions": "Show valid NYU ID at counter. Dine-in and takeout. Not valid on combo deals.",
        "discount_type": "percentage",
        "discount_value": 10.0,
        "price_range": 1,
        "is_verified": True,
        "phone": "+1 (212) 366-1182",
        "website": "https://joespizzanyc.com",
        "hours": [
            (0, time(10, 0), time(23, 0)),
            (1, time(10, 0), time(23, 0)),
            (2, time(10, 0), time(23, 0)),
            (3, time(10, 0), time(23, 0)),
            (4, time(10, 0), time(0, 0)),
            (5, time(10, 0), time(0, 0)),
            (6, time(10, 0), time(23, 0)),
        ],
    },
    {
        "name": "Mamoun's Falafel",
        "cuisine_type": "Middle Eastern",
        "address": "119 Macdougal St, New York, NY 10012",
        "latitude": 40.7299,
        "longitude": -74.0003,
        "discount_details": "Free soda with any sandwich — just show your NYU ID",
        "discount_conditions": "One free fountain drink per visit. Valid NYU ID required.",
        "discount_type": "free_item",
        "discount_value": None,
        "price_range": 1,
        "is_verified": True,
        "phone": "+1 (212) 674-8685",
        "website": None,
        "hours": [
            (0, time(11, 0), time(1, 0)),
            (1, time(11, 0), time(1, 0)),
            (2, time(11, 0), time(1, 0)),
            (3, time(11, 0), time(1, 0)),
            (4, time(11, 0), time(2, 0)),
            (5, time(11, 0), time(2, 0)),
            (6, time(11, 0), time(1, 0)),
        ],
    },
    {
        "name": "Veselka",
        "cuisine_type": "Ukrainian / Diner",
        "address": "144 2nd Ave, New York, NY 10003",
        "latitude": 40.7285,
        "longitude": -73.9877,
        "discount_details": "15% off your total bill with NYU ID — any time, any day",
        "discount_conditions": "Valid NYU student ID required. Cannot be combined with other offers.",
        "discount_type": "percentage",
        "discount_value": 15.0,
        "price_range": 2,
        "is_verified": True,
        "phone": "+1 (212) 228-9682",
        "website": "https://veselka.com",
        "hours": [
            (0, time(0, 0), time(23, 59)),
            (1, time(0, 0), time(23, 59)),
            (2, time(0, 0), time(23, 59)),
            (3, time(0, 0), time(23, 59)),
            (4, time(0, 0), time(23, 59)),
            (5, time(0, 0), time(23, 59)),
            (6, time(0, 0), time(23, 59)),
        ],
    },
    {
        "name": "Artichoke Basille's Pizza",
        "cuisine_type": "Pizza",
        "address": "321 E 14th St, New York, NY 10003",
        "latitude": 40.7336,
        "longitude": -73.9851,
        "discount_details": "$1 off every slice with NYU ID",
        "discount_conditions": "Show NYU ID. Valid on all slice orders. Not valid on whole pies.",
        "discount_type": "fixed",
        "discount_value": 1.0,
        "price_range": 1,
        "is_verified": True,
        "phone": "+1 (212) 228-2004",
        "website": "https://artichokepizza.com",
        "hours": [
            (0, time(11, 0), time(2, 0)),
            (1, time(11, 0), time(2, 0)),
            (2, time(11, 0), time(2, 0)),
            (3, time(11, 0), time(2, 0)),
            (4, time(11, 0), time(4, 0)),
            (5, time(11, 0), time(5, 0)),
            (6, time(11, 0), time(4, 0)),
        ],
    },
    {
        "name": "Dos Toros Taqueria",
        "cuisine_type": "Mexican",
        "address": "137 4th Ave, New York, NY 10003",
        "latitude": 40.7315,
        "longitude": -73.9896,
        "discount_details": "Student meal deal — burrito + chips + drink for $12 (save ~$4)",
        "discount_conditions": "Show NYU ID at register. Lunch hours only (11am–3pm).",
        "discount_type": "special_menu",
        "discount_value": 4.0,
        "price_range": 2,
        "is_verified": True,
        "phone": "+1 (212) 677-7300",
        "website": "https://dostoros.com",
        "hours": [
            (0, time(11, 0), time(22, 0)),
            (1, time(11, 0), time(22, 0)),
            (2, time(11, 0), time(22, 0)),
            (3, time(11, 0), time(22, 0)),
            (4, time(11, 0), time(22, 0)),
            (5, time(11, 0), time(22, 0)),
            (6, time(11, 0), time(22, 0)),
        ],
    },
    {
        "name": "Taïm",
        "cuisine_type": "Israeli / Falafel",
        "address": "222 Waverly Pl, New York, NY 10014",
        "latitude": 40.7341,
        "longitude": -74.0003,
        "discount_details": "10% off your order with NYU ID",
        "discount_conditions": "Show valid NYU ID. Valid on all menu items.",
        "discount_type": "percentage",
        "discount_value": 10.0,
        "price_range": 1,
        "is_verified": True,
        "phone": "+1 (212) 691-1287",
        "website": "https://taimfalafel.com",
        "hours": [
            (0, time(11, 0), time(22, 0)),
            (1, time(11, 0), time(22, 0)),
            (2, time(11, 0), time(22, 0)),
            (3, time(11, 0), time(22, 0)),
            (4, time(11, 0), time(22, 0)),
            (5, time(11, 0), time(22, 0)),
            (6, time(11, 0), time(22, 0)),
        ],
    },
    {
        "name": "Xi'an Famous Foods",
        "cuisine_type": "Chinese",
        "address": "81 St Marks Pl, New York, NY 10003",
        "latitude": 40.7273,
        "longitude": -73.9858,
        "discount_details": "Free cold noodles (small) with any entree — NYU ID required",
        "discount_conditions": "One free small cold noodle per student per visit. Dine-in only.",
        "discount_type": "free_item",
        "discount_value": None,
        "price_range": 1,
        "is_verified": True,
        "phone": "+1 (212) 786-2068",
        "website": "https://xianfoods.com",
        "hours": [
            (0, time(11, 30), time(22, 0)),
            (1, time(11, 30), time(22, 0)),
            (2, time(11, 30), time(22, 0)),
            (3, time(11, 30), time(22, 0)),
            (4, time(11, 30), time(22, 30)),
            (5, time(11, 30), time(22, 30)),
            (6, time(11, 30), time(22, 0)),
        ],
    },
    {
        "name": "Murray's Bagels",
        "cuisine_type": "Bagels / Cafe",
        "address": "500 6th Ave, New York, NY 10011",
        "latitude": 40.7390,
        "longitude": -74.0002,
        "discount_details": "Buy 4 bagels, get 1 free with NYU ID",
        "discount_conditions": "Show valid NYU ID. Valid Monday–Friday only.",
        "discount_type": "free_item",
        "discount_value": None,
        "price_range": 1,
        "is_verified": False,
        "phone": "+1 (212) 462-2830",
        "website": "https://murraysbagels.com",
        "hours": [
            (0, time(6, 30), time(17, 0)),
            (1, time(6, 30), time(17, 0)),
            (2, time(6, 30), time(17, 0)),
            (3, time(6, 30), time(17, 0)),
            (4, time(6, 30), time(17, 0)),
            (5, time(7, 0), time(17, 0)),
            (6, time(7, 0), time(17, 0)),
        ],
    },
    {
        "name": "Pommes Frites",
        "cuisine_type": "Belgian / Snacks",
        "address": "128 Macdougal St, New York, NY 10012",
        "latitude": 40.7297,
        "longitude": -74.0004,
        "discount_details": "Large fries for the price of medium with NYU ID",
        "discount_conditions": "Show valid NYU ID at ordering window.",
        "discount_type": "special_menu",
        "discount_value": None,
        "price_range": 1,
        "is_verified": False,
        "phone": None,
        "website": None,
        "hours": [
            (0, time(11, 30), time(23, 0)),
            (1, time(11, 30), time(23, 0)),
            (2, time(11, 30), time(23, 0)),
            (3, time(11, 30), time(23, 0)),
            (4, time(11, 30), time(0, 0)),
            (5, time(11, 30), time(0, 0)),
            (6, time(11, 30), time(23, 0)),
        ],
    },
    {
        "name": "Westville West Village",
        "cuisine_type": "American / Healthy",
        "address": "210 W 10th St, New York, NY 10014",
        "latitude": 40.7331,
        "longitude": -74.0048,
        "discount_details": "10% off your total bill Monday–Wednesday with NYU ID",
        "discount_conditions": "Valid Mon–Wed only. Dine-in only. Show NYU ID to server.",
        "discount_type": "percentage",
        "discount_value": 10.0,
        "price_range": 2,
        "is_verified": True,
        "phone": "+1 (212) 741-7971",
        "website": "https://westvillenyc.com",
        "hours": [
            (0, time(11, 0), time(22, 0)),
            (1, time(11, 0), time(22, 0)),
            (2, time(11, 0), time(22, 0)),
            (3, time(11, 0), time(22, 0)),
            (4, time(11, 0), time(23, 0)),
            (5, time(10, 0), time(23, 0)),
            (6, time(10, 0), time(22, 0)),
        ],
    },
    {
        "name": "Caffe Reggio",
        "cuisine_type": "Cafe / Italian",
        "address": "119 Macdougal St, New York, NY 10012",
        "latitude": 40.7300,
        "longitude": -74.0003,
        "discount_details": "Free espresso shot upgrade with any coffee drink — NYU ID",
        "discount_conditions": "Ask barista for student upgrade. Show NYU ID.",
        "discount_type": "free_item",
        "discount_value": None,
        "price_range": 1,
        "is_verified": True,
        "phone": "+1 (212) 475-9557",
        "website": None,
        "hours": [
            (0, time(9, 0), time(2, 0)),
            (1, time(9, 0), time(2, 0)),
            (2, time(9, 0), time(2, 0)),
            (3, time(9, 0), time(2, 0)),
            (4, time(9, 0), time(3, 0)),
            (5, time(9, 0), time(3, 0)),
            (6, time(9, 0), time(3, 0)),
        ],
    },
    {
        "name": "John's of Bleecker Street",
        "cuisine_type": "Pizza",
        "address": "278 Bleecker St, New York, NY 10014",
        "latitude": 40.7319,
        "longitude": -74.0034,
        "discount_details": "15% off whole pie with NYU ID (groups of 2+ students)",
        "discount_conditions": "All members of the group must show NYU ID. Whole pies only, no slices.",
        "discount_type": "percentage",
        "discount_value": 15.0,
        "price_range": 2,
        "is_verified": False,
        "phone": "+1 (212) 243-1680",
        "website": "https://johnsbleecker.com",
        "hours": [
            (0, time(11, 30), time(23, 0)),
            (1, time(11, 30), time(23, 0)),
            (2, time(11, 30), time(23, 0)),
            (3, time(11, 30), time(23, 0)),
            (4, time(11, 30), time(23, 30)),
            (5, time(11, 30), time(23, 30)),
            (6, time(11, 30), time(23, 0)),
        ],
    },
]


# ── Seed logic ─────────────────────────────────────────────────────────────────

async def seed():
    from app.models.restaurant import OperatingHours, Restaurant

    async with SessionLocal() as db:
        # Check if already seeded — avoid duplicates on re-run
        result = await db.execute(select(Restaurant).limit(1))
        if result.scalar_one_or_none():
            print("Database already has restaurants. Skipping seed.")
            print("To re-seed, run: docker exec nyu-bites-db-1 psql -U nyubites -d nyubites -c 'TRUNCATE restaurants CASCADE;'")
            return

        print(f"Seeding {len(RESTAURANTS)} restaurants...\n")

        for data in RESTAURANTS:
            hours_data = data.pop("hours")

            restaurant = Restaurant(
                id=uuid.uuid4(),
                **data,
            )
            db.add(restaurant)
            await db.flush()  # get the id assigned before adding hours

            for day, open_t, close_t in hours_data:
                db.add(OperatingHours(
                    restaurant_id=restaurant.id,
                    day_of_week=day,
                    open_time=open_t,
                    close_time=close_t,
                    is_closed=False,
                ))

            verified = "✓" if restaurant.is_verified else " "
            print(f"  [{verified}] {restaurant.name} — {restaurant.discount_details[:55]}...")

        await db.commit()
        print(f"\nDone! {len(RESTAURANTS)} restaurants seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
