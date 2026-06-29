import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    tip_text: str = Field(min_length=10, max_length=1000)


class ReviewOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    restaurant_id: uuid.UUID
    user_id: uuid.UUID
    tip_text: str
    upvotes: int
    last_verified: datetime | None
    created_at: datetime
