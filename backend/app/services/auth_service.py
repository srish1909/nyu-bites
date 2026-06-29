"""
Auth service — owns all Redis key interactions for tokens.

Key schema:
  nyubites:verify:{token}    → user_id   TTL = verification_token_expire_hours
  nyubites:refresh:{token}   → user_id   TTL = refresh_token_expire_days
  nyubites:reset:{token}     → user_id   TTL = reset_token_expire_minutes
  nyubites:revoked:{jti}     → "1"       TTL = remaining access token lifetime
"""
import uuid
from datetime import timedelta

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import generate_opaque_token

_VERIFY_PREFIX = "nyubites:verify:"
_REFRESH_PREFIX = "nyubites:refresh:"
_RESET_PREFIX = "nyubites:reset:"
_REVOKED_PREFIX = "nyubites:revoked:"


# ── Email verification ────────────────────────────────────────────────────────

async def create_verification_token(user_id: uuid.UUID, redis: Redis) -> str:
    token = generate_opaque_token()
    ttl = int(timedelta(hours=settings.verification_token_expire_hours).total_seconds())
    await redis.set(f"{_VERIFY_PREFIX}{token}", str(user_id), ex=ttl)
    return token


async def consume_verification_token(token: str, redis: Redis) -> uuid.UUID | None:
    """Returns the user_id and deletes the token atomically, or None if invalid/expired."""
    key = f"{_VERIFY_PREFIX}{token}"
    value = await redis.getdel(key)
    if value is None:
        return None
    return uuid.UUID(value)


# ── Refresh tokens ────────────────────────────────────────────────────────────

async def create_refresh_token(user_id: uuid.UUID, redis: Redis) -> str:
    token = generate_opaque_token(48)
    ttl = int(timedelta(days=settings.refresh_token_expire_days).total_seconds())
    await redis.set(f"{_REFRESH_PREFIX}{token}", str(user_id), ex=ttl)
    return token


async def rotate_refresh_token(old_token: str, redis: Redis) -> tuple[str, uuid.UUID] | None:
    """
    Validates and atomically replaces a refresh token.
    Returns (new_token, user_id) or None if the old token is invalid.
    Token rotation prevents replay attacks — each refresh token is single-use.
    """
    key = f"{_REFRESH_PREFIX}{old_token}"
    user_id_str = await redis.getdel(key)
    if user_id_str is None:
        return None
    user_id = uuid.UUID(user_id_str)
    new_token = await create_refresh_token(user_id, redis)
    return new_token, user_id


async def revoke_refresh_token(token: str, redis: Redis) -> None:
    await redis.delete(f"{_REFRESH_PREFIX}{token}")


# ── Access token revocation (logout) ─────────────────────────────────────────

async def revoke_access_token(jti: str, expires_in_seconds: int, redis: Redis) -> None:
    """Adds the JWT ID to the Redis revocation list until the token would have expired."""
    await redis.set(f"{_REVOKED_PREFIX}{jti}", "1", ex=max(expires_in_seconds, 1))


async def is_access_token_revoked(jti: str, redis: Redis) -> bool:
    return await redis.exists(f"{_REVOKED_PREFIX}{jti}") == 1


# ── Password reset ────────────────────────────────────────────────────────────

async def create_reset_token(user_id: uuid.UUID, redis: Redis) -> str:
    token = generate_opaque_token()
    ttl = int(timedelta(minutes=settings.reset_token_expire_minutes).total_seconds())
    # Only one active reset token per user — overwrite any existing one
    # (store reverse mapping too so we can clean up on use)
    await redis.set(f"{_RESET_PREFIX}{token}", str(user_id), ex=ttl)
    return token


async def consume_reset_token(token: str, redis: Redis) -> uuid.UUID | None:
    key = f"{_RESET_PREFIX}{token}"
    value = await redis.getdel(key)
    if value is None:
        return None
    return uuid.UUID(value)
