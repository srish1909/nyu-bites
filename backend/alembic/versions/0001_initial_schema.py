"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nyu_email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("dietary_restrictions", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("budget", sa.Integer(), nullable=True),
        sa.Column("preferred_cuisines", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_nyu_email", "users", ["nyu_email"])

    # ── restaurants ────────────────────────────────────────────────────────
    op.create_table(
        "restaurants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("cuisine_type", sa.String(100), nullable=True),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("google_place_id", sa.String(255), nullable=True, unique=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("discount_details", sa.Text(), nullable=True),
        sa.Column("discount_conditions", sa.Text(), nullable=True),
        sa.Column("discount_type", sa.String(50), nullable=True),
        sa.Column("discount_value", sa.Float(), nullable=True),
        sa.Column("price_range", sa.Integer(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_restaurants_name", "restaurants", ["name"])
    op.create_index("ix_restaurants_cuisine_type", "restaurants", ["cuisine_type"])
    op.create_index("ix_restaurants_discount_type", "restaurants", ["discount_type"])
    op.create_index("ix_restaurants_price_range", "restaurants", ["price_range"])
    op.create_index("ix_restaurants_is_verified", "restaurants", ["is_verified"])

    # ── operating_hours ────────────────────────────────────────────────────
    op.create_table(
        "operating_hours",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("restaurant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("open_time", sa.Time(), nullable=True),
        sa.Column("close_time", sa.Time(), nullable=True),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_operating_hours_restaurant_id", "operating_hours", ["restaurant_id"])

    # ── reviews ────────────────────────────────────────────────────────────
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("restaurant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tip_text", sa.Text(), nullable=False),
        sa.Column("upvotes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_verified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_reviews_restaurant_id", "reviews", ["restaurant_id"])
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"])

    # ── saved_restaurants ──────────────────────────────────────────────────
    op.create_table(
        "saved_restaurants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("restaurant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "restaurant_id", name="uq_user_restaurant"),
    )
    op.create_index("ix_saved_restaurants_user_id", "saved_restaurants", ["user_id"])
    op.create_index("ix_saved_restaurants_restaurant_id", "saved_restaurants", ["restaurant_id"])


def downgrade() -> None:
    op.drop_table("saved_restaurants")
    op.drop_table("reviews")
    op.drop_table("operating_hours")
    op.drop_table("restaurants")
    op.drop_table("users")
