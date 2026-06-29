import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_verified_user
from app.database import get_db
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewOut

router = APIRouter(prefix="/restaurants/{restaurant_id}/reviews", tags=["reviews"])


@router.get("/", response_model=list[ReviewOut])
async def list_reviews(restaurant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review)
        .where(Review.restaurant_id == restaurant_id)
        .order_by(Review.upvotes.desc(), Review.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    restaurant_id: uuid.UUID,
    payload: ReviewCreate,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Restaurant not found")

    review = Review(
        restaurant_id=restaurant_id,
        user_id=current_user.id,
        tip_text=payload.tip_text,
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)
    return review


@router.post("/{review_id}/upvote")
async def upvote_review(
    restaurant_id: uuid.UUID,
    review_id: uuid.UUID,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.restaurant_id == restaurant_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.upvotes += 1
    return {"upvotes": review.upvotes}
