"""
Shared fixtures for the NYU Bites test suite.

Strategy:
- Each test gets its own asyncpg connection pool (function-scoped engine).
  This avoids event-loop conflicts where pytest-asyncio creates a fresh loop
  per test but asyncpg connections are tied to the loop that created them.
- Each test wraps its DB work in a transaction that rolls back at the end,
  so no test data ever persists to the real database.
- Redis is replaced by an in-memory FakeRedis — no Docker dependency, fully
  isolated, reset between tests.
"""

# Disable slowapi rate limiting before any app modules are imported.
# Slowapi reads RATELIMIT_ENABLED once during Limiter.__init__, so this must
# be set before the limiter module is first imported.
import os
os.environ["RATELIMIT_ENABLED"] = "false"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import fakeredis

from app.config import settings
from app.database import get_db
from app.core.redis import get_redis
from app.main import app


# ── Database session (fresh engine + rollback per test) ────────────────────

@pytest_asyncio.fixture
async def db_session():
    """
    Creates a brand-new connection pool for this test (avoids event-loop
    conflicts), opens a transaction, and rolls it back when the test ends.
    Nothing written during a test survives to the next test.
    """
    engine = create_async_engine(settings.database_url, echo=False)
    try:
        async with engine.connect() as conn:
            await conn.begin()
            session = AsyncSession(bind=conn, join_transaction_mode="create_savepoint")
            try:
                yield session
            finally:
                await session.close()
                await conn.rollback()
    finally:
        await engine.dispose()


# ── Fake Redis (in-memory, reset after every test) ─────────────────────────

@pytest_asyncio.fixture
async def fake_redis():
    """In-memory Redis — fast, isolated, no Docker dependency."""
    r = fakeredis.FakeAsyncRedis()
    yield r
    await r.flushall()
    await r.aclose()


# ── HTTP client with dependency overrides ──────────────────────────────────

@pytest_asyncio.fixture
async def client(db_session, fake_redis):
    """
    httpx AsyncClient that hits the real FastAPI app in-process.
    get_db and get_redis are overridden to use the test DB session
    (which rolls back) and fake Redis (which is empty).
    """
    async def _get_db():
        yield db_session

    async def _get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_redis] = _get_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Logged-in client helper ─────────────────────────────────────────────────

@pytest_asyncio.fixture
async def auth_client(client):
    """
    An AsyncClient already logged in as a verified NYU user.
    Returns (client, tokens) so tests can inspect access/refresh tokens.
    """
    reg = await client.post("/api/v1/auth/register", json={
        "nyu_email": "fixture@nyu.edu",
        "password": "testpass123",
        "display_name": "Test User",
    })
    assert reg.status_code == 201

    login = await client.post("/api/v1/auth/login", json={
        "nyu_email": "fixture@nyu.edu",
        "password": "testpass123",
    })
    assert login.status_code == 200
    tokens = login.json()
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    return client, tokens
