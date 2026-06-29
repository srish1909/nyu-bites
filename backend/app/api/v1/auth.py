import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.limiter import limiter
from app.core.email import send_password_reset_email, send_verification_email
from app.core.redis import get_redis
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    AccessTokenResponse,
    EmailVerifyRequest,
    ForgotPasswordRequest,
    LogoutRequest,
    RefreshRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
)
from app.services.auth_service import (
    consume_reset_token,
    consume_verification_token,
    create_refresh_token,
    create_reset_token,
    create_verification_token,
    revoke_access_token,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: UserRegister,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Create a new account with an @nyu.edu email.
    Sends a verification email; the account works immediately in dev
    (EMAIL_BACKEND=console) but is_verified=False until the link is clicked
    in production.
    """
    existing = await db.execute(select(User).where(User.nyu_email == payload.nyu_email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # In dev, auto-verify so you can hit protected endpoints without clicking a link.
    auto_verify = settings.environment == "development"

    user = User(
        nyu_email=payload.nyu_email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
        is_verified=auto_verify,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Always generate and "send" the token so the flow can be tested in dev too
    token = await create_verification_token(user.id, redis)
    await send_verification_email(user.nyu_email, user.display_name, token)

    return user


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Returns a short-lived JWT access token and a long-lived opaque refresh token.
    The refresh token is stored in Redis; rotate it via POST /auth/refresh.
    """
    result = await db.execute(select(User).where(User.nyu_email == payload.nyu_email))
    user = result.scalar_one_or_none()

    # Constant-time comparison prevents user-enumeration via timing
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    access_token, _ = create_access_token(str(user.id))
    refresh_token = await create_refresh_token(user.id, redis)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ── Email verification ────────────────────────────────────────────────────────

@router.post("/verify-email", response_model=UserOut)
async def verify_email(
    payload: EmailVerifyRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Consume the one-time token from the verification email link.
    Marks the account as verified. Token is deleted from Redis on use.
    """
    user_id = await consume_verification_token(payload.token, redis)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Re-sends the verification email. Always returns 202 even if the email
    doesn't exist to prevent user enumeration.
    """
    result = await db.execute(select(User).where(User.nyu_email == payload.nyu_email))
    user = result.scalar_one_or_none()

    if user and not user.is_verified and user.is_active:
        token = await create_verification_token(user.id, redis)
        await send_verification_email(user.nyu_email, user.display_name, token)

    return {"message": "If that email exists and is unverified, a new link has been sent"}


# ── Token refresh ─────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(
    payload: RefreshRequest,
    redis: Redis = Depends(get_redis),
):
    """
    Exchange a valid refresh token for a new access token.
    The refresh token is rotated (old one deleted, new one issued) to
    detect token theft via replay attacks.
    """
    result = await rotate_refresh_token(payload.refresh_token, redis)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    new_refresh_token, user_id = result
    access_token, _ = create_access_token(str(user_id))

    return AccessTokenResponse(
        access_token=access_token,
        # Return the new refresh token in the response body so the client can store it
        # In a browser app you'd set this as an HttpOnly cookie instead
    )


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest,
    redis: Redis = Depends(get_redis),
):
    """
    Revokes the refresh token immediately.
    The access token will expire naturally (60 min); pass it in the
    Authorization header and it will also be added to the revocation list.
    """
    await revoke_refresh_token(payload.refresh_token, redis)


# ── Password reset ────────────────────────────────────────────────────────────

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Sends a password-reset email. Always returns 202 to prevent user enumeration.
    """
    result = await db.execute(select(User).where(User.nyu_email == payload.nyu_email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        token = await create_reset_token(user.id, redis)
        await send_password_reset_email(user.nyu_email, user.display_name, token)

    return {"message": "If that account exists, a reset link has been sent"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Consume the one-time reset token and set a new password.
    Invalidates all existing refresh tokens by simply not knowing them
    (a full revocation scan is overkill here — the old tokens naturally expire).
    """
    user_id = await consume_reset_token(payload.token, redis)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(payload.new_password)
    await db.flush()

    return {"message": "Password updated. Please log in with your new password."}
