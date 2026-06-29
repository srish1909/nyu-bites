"""
Integration tests for /api/v1/auth/* endpoints.

All HTTP calls go through the real FastAPI app (in-process via AsyncClient).
The database rolls back after each test; Redis is in-memory.
"""

import pytest


# ── /auth/register ────────────────────────────────────────────────────────────

async def test_register_success(client):
    r = await client.post("/api/v1/auth/register", json={
        "nyu_email": "alice@nyu.edu",
        "password": "securepass1",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["nyu_email"] == "alice@nyu.edu"
    assert "id" in body
    # In development mode the account is auto-verified
    assert body["is_verified"] is True


async def test_register_non_nyu_email_rejected(client):
    r = await client.post("/api/v1/auth/register", json={
        "nyu_email": "alice@gmail.com",
        "password": "securepass1",
    })
    assert r.status_code == 422  # Pydantic validation error


async def test_register_short_password_rejected(client):
    r = await client.post("/api/v1/auth/register", json={
        "nyu_email": "bob@nyu.edu",
        "password": "short",
    })
    assert r.status_code == 422


async def test_register_duplicate_email_rejected(client):
    payload = {"nyu_email": "dup@nyu.edu", "password": "password123"}
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"].lower()


# ── /auth/login ───────────────────────────────────────────────────────────────

async def test_login_success_returns_tokens(client):
    await client.post("/api/v1/auth/register", json={
        "nyu_email": "logintest@nyu.edu",
        "password": "mypassword1",
    })
    r = await client.post("/api/v1/auth/login", json={
        "nyu_email": "logintest@nyu.edu",
        "password": "mypassword1",
    })
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password_rejected(client):
    await client.post("/api/v1/auth/register", json={
        "nyu_email": "wrongpass@nyu.edu",
        "password": "realpassword1",
    })
    r = await client.post("/api/v1/auth/login", json={
        "nyu_email": "wrongpass@nyu.edu",
        "password": "WRONGPASSWORD",
    })
    assert r.status_code == 401


async def test_login_nonexistent_user_rejected(client):
    r = await client.post("/api/v1/auth/login", json={
        "nyu_email": "ghost@nyu.edu",
        "password": "doesntmatter",
    })
    assert r.status_code == 401


# ── Protected endpoints ───────────────────────────────────────────────────────

async def test_get_me_without_token_returns_403(client):
    r = await client.get("/api/v1/users/me")
    # HTTPBearer returns 403 when no Authorization header is present
    assert r.status_code == 403


async def test_get_me_with_invalid_token_returns_401(client):
    r = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer this.is.not.valid"},
    )
    assert r.status_code == 401


async def test_get_me_with_valid_token_returns_user(auth_client):
    client, _ = auth_client
    r = await client.get("/api/v1/users/me")
    assert r.status_code == 200
    body = r.json()
    assert body["nyu_email"] == "fixture@nyu.edu"


# ── /auth/logout ──────────────────────────────────────────────────────────────

async def test_logout_revokes_refresh_token(client):
    await client.post("/api/v1/auth/register", json={
        "nyu_email": "logouttest@nyu.edu",
        "password": "password123",
    })
    login = await client.post("/api/v1/auth/login", json={
        "nyu_email": "logouttest@nyu.edu",
        "password": "password123",
    })
    tokens = login.json()

    # Logout
    r = await client.post("/api/v1/auth/logout", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert r.status_code == 204

    # Trying to refresh with the now-revoked token should fail
    r2 = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert r2.status_code == 401


# ── /auth/resend-verification ─────────────────────────────────────────────────

async def test_resend_verification_always_returns_202(client):
    """Should return 202 even for non-existent emails (prevents enumeration)."""
    r = await client.post("/api/v1/auth/resend-verification", json={
        "nyu_email": "nobody@nyu.edu",
    })
    assert r.status_code == 202


# ── /auth/forgot-password ─────────────────────────────────────────────────────

async def test_forgot_password_always_returns_202(client):
    """Should return 202 even for non-existent emails (prevents enumeration)."""
    r = await client.post("/api/v1/auth/forgot-password", json={
        "nyu_email": "nobody@nyu.edu",
    })
    assert r.status_code == 202
