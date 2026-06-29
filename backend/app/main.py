from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1 import agent, auth, restaurants, reviews, users
from app.config import settings
from app.core.limiter import limiter
from app.core.redis import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()
    yield
    await close_redis()


app = FastAPI(
    title="NYU Bites API",
    description="Restaurant & cafe discount discovery for NYU students",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting middleware + error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(restaurants.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "NYU Bites API"}
