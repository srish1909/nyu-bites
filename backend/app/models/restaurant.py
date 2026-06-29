import uuid
from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cuisine_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Google Places
    google_place_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Discount info
    discount_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    discount_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    # discount_type: "percentage", "fixed", "free_item", "special_menu"
    discount_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    discount_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # price_range: 1=$, 2=$$, 3=$$$, 4=$$$$
    price_range: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    operating_hours: Mapped[list["OperatingHours"]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        back_populates="restaurant", cascade="all, delete-orphan"
    )
    saved_by: Mapped[list["SavedRestaurant"]] = relationship(  # noqa: F821
        back_populates="restaurant", cascade="all, delete-orphan"
    )


class OperatingHours(Base):
    __tablename__ = "operating_hours"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 0=Monday … 6=Sunday
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    open_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    close_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationship
    restaurant: Mapped["Restaurant"] = relationship(back_populates="operating_hours")
