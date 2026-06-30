"""Add more restaurants to the DB without wiping existing data."""
import asyncio, uuid, os
from datetime import time
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://nyubites:changeme@db:5432/nyubites")
engine = create_async_engine(DATABASE_URL, echo=False)
Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

NEW_RESTAURANTS = [
    {
        "name": "Think Coffee",
        "cuisine_type": "Cafe",
        "address": "248 Mercer St, New York, NY 10012",
        "latitude": 40.7291, "longitude": -73.9965,
        "discount_details": "10% off any drink with NYU ID — all day, every day",
        "discount_conditions": "Show valid NYU ID. Applies to all beverages.",
        "discount_type": "percentage", "discount_value": 10.0,
        "price_range": 1, "is_verified": True,
        "phone": "+1 (212) 228-6226", "website": "https://thinkcoffee.com",
        "hours": [(d, time(7,0), time(22,0)) for d in range(7)],
    },
    {
        "name": "Saigon Shack",
        "cuisine_type": "Vietnamese",
        "address": "114 Macdougal St, New York, NY 10012",
        "latitude": 40.7298, "longitude": -74.0006,
        "discount_details": "Free spring roll with any bowl — show NYU ID",
        "discount_conditions": "One free spring roll per student per visit. Dine-in only.",
        "discount_type": "free_item", "discount_value": None,
        "price_range": 1, "is_verified": True,
        "phone": "+1 (212) 228-0588", "website": None,
        "hours": [(d, time(11,0), time(23,0)) for d in range(7)],
    },
    {
        "name": "Bleecker Street Pizza",
        "cuisine_type": "Pizza",
        "address": "69 7th Ave S, New York, NY 10014",
        "latitude": 40.7325, "longitude": -74.0033,
        "discount_details": "$1.50 off any slice with NYU ID",
        "discount_conditions": "Show NYU ID at the counter. Limit 2 slices per visit.",
        "discount_type": "fixed", "discount_value": 1.5,
        "price_range": 1, "is_verified": True,
        "phone": "+1 (212) 924-4466", "website": "https://bleeckerstreetpizza.com",
        "hours": [
            (0, time(11,0), time(23,0)), (1, time(11,0), time(23,0)),
            (2, time(11,0), time(23,0)), (3, time(11,0), time(23,0)),
            (4, time(11,0), time(0,0)),  (5, time(11,0), time(0,0)),
            (6, time(11,0), time(23,0)),
        ],
    },
    {
        "name": "The Grey Dog",
        "cuisine_type": "Cafe",
        "address": "90 University Pl, New York, NY 10003",
        "latitude": 40.7340, "longitude": -73.9953,
        "discount_details": "15% off food orders Monday–Friday with NYU ID",
        "discount_conditions": "Valid Mon–Fri, 8am–4pm. Dine-in only. Show NYU ID.",
        "discount_type": "percentage", "discount_value": 15.0,
        "price_range": 2, "is_verified": True,
        "phone": "+1 (212) 414-4739", "website": "https://thegreydog.com",
        "hours": [(d, time(8,0), time(22,0)) for d in range(7)],
    },
    {
        "name": "Tacombi",
        "cuisine_type": "Mexican",
        "address": "255 Bleecker St, New York, NY 10014",
        "latitude": 40.7316, "longitude": -74.0028,
        "discount_details": "Student taco combo — 3 tacos + agua fresca for $16 (save $5)",
        "discount_conditions": "Show NYU ID at register. Dine-in only. Not valid on weekends.",
        "discount_type": "special_menu", "discount_value": 5.0,
        "price_range": 2, "is_verified": True,
        "phone": "+1 (917) 727-0179", "website": "https://tacombi.com",
        "hours": [
            (0, time(11,0), time(22,0)), (1, time(11,0), time(22,0)),
            (2, time(11,0), time(22,0)), (3, time(11,0), time(22,0)),
            (4, time(11,0), time(23,0)), (5, time(10,0), time(23,0)),
            (6, time(10,0), time(22,0)),
        ],
    },
    {
        "name": "Num Pang Kitchen",
        "cuisine_type": "Cambodian",
        "address": "140 E 41st St, New York, NY 10017",
        "latitude": 40.7509, "longitude": -73.9789,
        "discount_details": "10% off all sandwiches with NYU ID",
        "discount_conditions": "Show valid NYU ID. Valid on all sandwich orders.",
        "discount_type": "percentage", "discount_value": 10.0,
        "price_range": 1, "is_verified": False,
        "phone": "+1 (212) 867-8889", "website": "https://numpang.com",
        "hours": [(d, time(10,30), time(20,0)) for d in range(0,5)] + [(5, time(11,0), time(17,0))],
    },
    {
        "name": "Mighty Quinn's Barbeque",
        "cuisine_type": "BBQ",
        "address": "103 2nd Ave, New York, NY 10003",
        "latitude": 40.7265, "longitude": -73.9877,
        "discount_details": "Free side dish with any BBQ plate — NYU ID required",
        "discount_conditions": "One free side per student. Show NYU ID at counter. Dine-in or takeout.",
        "discount_type": "free_item", "discount_value": None,
        "price_range": 2, "is_verified": True,
        "phone": "+1 (212) 677-3733", "website": "https://mightyquinnsbbq.com",
        "hours": [
            (0, time(11,30), time(22,0)), (1, time(11,30), time(22,0)),
            (2, time(11,30), time(22,0)), (3, time(11,30), time(22,0)),
            (4, time(11,30), time(23,0)), (5, time(11,30), time(23,0)),
            (6, time(11,30), time(22,0)),
        ],
    },
    {
        "name": "Shake Shack",
        "cuisine_type": "American",
        "address": "225 Varick St, New York, NY 10014",
        "latitude": 40.7282, "longitude": -74.0065,
        "discount_details": "10% off your order with NYU ID",
        "discount_conditions": "Show valid NYU ID at kiosk or register. Valid at this location only.",
        "discount_type": "percentage", "discount_value": 10.0,
        "price_range": 2, "is_verified": True,
        "phone": None, "website": "https://shakeshack.com",
        "hours": [(d, time(10,30), time(22,0)) for d in range(7)],
    },
    {
        "name": "Insomnia Cookies",
        "cuisine_type": "Desserts",
        "address": "36 W 8th St, New York, NY 10011",
        "latitude": 40.7320, "longitude": -73.9976,
        "discount_details": "Buy 2 cookies get 1 free with NYU ID",
        "discount_conditions": "Show NYU ID. Valid on warm cookies only.",
        "discount_type": "free_item", "discount_value": None,
        "price_range": 1, "is_verified": True,
        "phone": "+1 (877) 632-6654", "website": "https://insomniacookies.com",
        "hours": [
            (0, time(10,0), time(1,0)),  (1, time(10,0), time(1,0)),
            (2, time(10,0), time(1,0)),  (3, time(10,0), time(1,0)),
            (4, time(10,0), time(3,0)),  (5, time(10,0), time(3,0)),
            (6, time(10,0), time(1,0)),
        ],
    },
    {
        "name": "Woorijip",
        "cuisine_type": "Korean",
        "address": "12 W 32nd St, New York, NY 10001",
        "latitude": 40.7487, "longitude": -73.9877,
        "discount_details": "15% off prepared food with NYU ID",
        "discount_conditions": "Show valid NYU ID. Not valid on hot food station items during peak hours.",
        "discount_type": "percentage", "discount_value": 15.0,
        "price_range": 1, "is_verified": False,
        "phone": "+1 (212) 244-1115", "website": None,
        "hours": [(d, time(8,0), time(23,0)) for d in range(7)],
    },
    {
        "name": "Pita Express",
        "cuisine_type": "Middle Eastern",
        "address": "46 W 8th St, New York, NY 10011",
        "latitude": 40.7322, "longitude": -73.9983,
        "discount_details": "Free pita bread and hummus with any combo plate — NYU ID",
        "discount_conditions": "One free pita + hummus per student per visit. Show NYU ID.",
        "discount_type": "free_item", "discount_value": None,
        "price_range": 1, "is_verified": True,
        "phone": None, "website": None,
        "hours": [(d, time(10,0), time(22,0)) for d in range(7)],
    },
    {
        "name": "Oliva",
        "cuisine_type": "Spanish",
        "address": "161 E Houston St, New York, NY 10002",
        "latitude": 40.7225, "longitude": -73.9878,
        "discount_details": "20% off tapas Monday & Tuesday with NYU ID",
        "discount_conditions": "Mon & Tue only. Dine-in only. Show NYU ID to server.",
        "discount_type": "percentage", "discount_value": 20.0,
        "price_range": 2, "is_verified": False,
        "phone": "+1 (212) 228-4143", "website": None,
        "hours": [
            (0, time(12,0), time(22,0)), (1, time(12,0), time(22,0)),
            (2, time(12,0), time(22,0)), (3, time(12,0), time(22,0)),
            (4, time(12,0), time(23,0)), (5, time(12,0), time(23,0)),
            (6, time(12,0), time(22,0)),
        ],
    },
]


async def main():
    from app.models.restaurant import OperatingHours, Restaurant

    async with Session() as db:
        existing = (await db.execute(select(Restaurant.name))).scalars().all()
        print(f"Existing restaurants: {len(existing)}")

        added = 0
        for data in NEW_RESTAURANTS:
            if data["name"] in existing:
                print(f"  SKIP (already exists): {data['name']}")
                continue
            hours = data.pop("hours")
            r = Restaurant(id=uuid.uuid4(), is_active=True, **data)
            db.add(r)
            await db.flush()
            for day, open_t, close_t in hours:
                db.add(OperatingHours(
                    restaurant_id=r.id, day_of_week=day,
                    open_time=open_t, close_time=close_t, is_closed=False,
                ))
            print(f"  + {r.name}")
            added += 1

        await db.commit()
        print(f"\nDone! Added {added} new restaurants. Total: {len(existing) + added}")


if __name__ == "__main__":
    asyncio.run(main())
