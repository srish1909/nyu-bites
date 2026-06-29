import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    nyu_email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None

    @field_validator("nyu_email")
    @classmethod
    def must_be_nyu_email(cls, v: str) -> str:
        if not v.endswith("@nyu.edu"):
            raise ValueError("Only @nyu.edu email addresses are allowed")
        return v.lower()


class UserLogin(BaseModel):
    nyu_email: EmailStr
    password: str


class UserPreferencesUpdate(BaseModel):
    display_name: str | None = None
    dietary_restrictions: list[str] | None = None
    budget: int | None = Field(None, ge=1, le=4)
    preferred_cuisines: list[str] | None = None


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    nyu_email: str
    display_name: str | None
    is_verified: bool
    dietary_restrictions: list[str] | None
    budget: int | None
    preferred_cuisines: list[str] | None
    created_at: datetime


# ── Token responses ────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """Returned by /auth/refresh — only a new access token, refresh token stays same."""
    access_token: str
    token_type: str = "bearer"


# ── Auth action payloads ───────────────────────────────────────────────────────

class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class EmailVerifyRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    nyu_email: EmailStr

    @field_validator("nyu_email")
    @classmethod
    def must_be_nyu_email(cls, v: str) -> str:
        if not v.endswith("@nyu.edu"):
            raise ValueError("Only @nyu.edu email addresses are allowed")
        return v.lower()


class ForgotPasswordRequest(BaseModel):
    nyu_email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)
