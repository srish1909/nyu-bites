from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent import run_agent
from app.api.deps import get_verified_user
from app.database import get_db
from app.core.limiter import limiter
from app.models.user import User

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentQuery(BaseModel):
    query: str
    lat: float | None = None
    lng: float | None = None


class AgentResponse(BaseModel):
    answer: str


@router.post("/query", response_model=AgentResponse)
@limiter.limit("20/minute")
async def agent_query(
    request: Request,
    payload: AgentQuery,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    query = payload.query
    if payload.lat and payload.lng:
        query += f" [User location: lat={payload.lat}, lng={payload.lng}]"

    answer = await run_agent(query, db)
    return AgentResponse(answer=answer)
