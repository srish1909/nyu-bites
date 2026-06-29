import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings


# ── Passwords ─────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Access JWT ────────────────────────────────────────────────────────────────

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> tuple[str, str]:
    """
    Returns (encoded_jwt, jti).
    jti is stored in Redis on logout so the token can be revoked before expiry.
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    token = jwt.encode(
        {"sub": subject, "exp": expire, "jti": jti},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return token, jti


def decode_access_token(token: str) -> dict:
    """
    Decodes the JWT and returns the full payload dict.
    Raises JWTError on any failure.
    """
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    if not payload.get("sub") or not payload.get("jti"):
        raise JWTError("Missing required claims")
    return payload


# ── Opaque tokens (refresh / verify / reset) ──────────────────────────────────

def generate_opaque_token(nbytes: int = 32) -> str:
    """URL-safe random token — used for refresh, email verification, and password reset."""
    return secrets.token_urlsafe(nbytes)
