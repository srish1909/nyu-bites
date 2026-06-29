import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_verified_user
from app.database import get_db
from app.models.restaurant import Restaurant
from app.models.saved_restaurant import SavedRestaurant
from app.models.user import User
from app.schemas.restaurant import RestaurantOut
from app.schemas.user import UserOut, UserPreferencesUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_verified_user)):
    return current_user


@router.patch("/me/preferences", response_model=UserOut)
async def update_preferences(
    payload: UserPreferencesUpdate,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.flush()
    await db.refresh(current_user)
    return current_user


@router.get("/me/saved", response_model=list[RestaurantOut])
async def get_saved_restaurants(
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedRestaurant)
        .where(SavedRestaurant.user_id == current_user.id)
        .options(selectinload(SavedRestaurant.restaurant).selectinload(Restaurant.operating_hours))
        .order_by(SavedRestaurant.saved_at.desc())
    )
    saved = result.scalars().all()
    return [s.restaurant for s in saved]


@router.post("/me/saved/{restaurant_id}", status_code=status.HTTP_201_CREATED)
async def save_restaurant(
    restaurant_id: uuid.UUID,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Restaurant not found")

    existing = await db.execute(
        select(SavedRestaurant).where(
            SavedRestaurant.user_id == current_user.id,
            SavedRestaurant.restaurant_id == restaurant_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already saved")

    db.add(SavedRestaurant(user_id=current_user.id, restaurant_id=restaurant_id))
    return {"message": "Saved"}


@router.delete("/me/saved/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_restaurant(
    restaurant_id: uuid.UUID,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedRestaurant).where(
            SavedRestaurant.user_id == current_user.id,
            SavedRestaurant.restaurant_id == restaurant_id,
        )
    )
    saved = result.scalar_one_or_none()
    if not saved:
        raise HTTPException(status_code=404, detail="Not saved")
    await db.delete(saved)
