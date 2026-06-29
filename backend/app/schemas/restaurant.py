import uuid
from datetime import datetime, time

from pydantic import BaseModel, Field


class OperatingHoursOut(BaseModel):
    model_config = {"from_attributes": True}

    day_of_week: int
    open_time: time | None
    close_time: time | None
    is_closed: bool


class RestaurantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    cuisine_type: str | None = None
    address: str
    latitude: float | None = None
    longitude: float | None = None
    google_place_id: str | None = None
    phone: str | None = None
    website: str | None = None
    discount_details: str | None = None
    discount_conditions: str | None = None
    discount_type: str | None = None
    discount_value: float | None = None
    price_range: int | None = Field(None, ge=1, le=4)


class RestaurantOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    cuisine_type: str | None
    address: str
    latitude: float | None
    longitude: float | None
    discount_details: str | None
    discount_conditions: str | None
    discount_type: str | None
    discount_value: float | None
    price_range: int | None
    is_verified: bool
    phone: str | None
    website: str | None
    operating_hours: list[OperatingHoursOut] = []
    created_at: datetime


class RestaurantListParams(BaseModel):
    cuisine: str | None = None
    max_distance_km: float | None = None
    lat: float | None = None
    lng: float | None = None
    discount_type: str | None = None
    price_range: int | None = Field(None, ge=1, le=4)
    verified_only: bool = False
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
