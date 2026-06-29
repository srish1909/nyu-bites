"""
Unit tests for app/core/security.py — no database or network required.
These run fast and test the core crypto logic in isolation.
"""

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ── Password hashing ──────────────────────────────────────────────────────────

def test_hash_password_produces_bcrypt_hash():
    hashed = hash_password("mypassword")
    assert hashed.startswith("$2b$")  # bcrypt format
    assert len(hashed) == 60


def test_verify_correct_password_returns_true():
    hashed = hash_password("correctpassword")
    assert verify_password("correctpassword", hashed) is True


def test_verify_wrong_password_returns_false():
    hashed = hash_password("correctpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_each_hash_is_unique_due_to_salt():
    """Same password → different hashes (bcrypt uses random salts)."""
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2
    # But both should verify correctly
    assert verify_password("same", h1)
    assert verify_password("same", h2)


# ── JWT access tokens ─────────────────────────────────────────────────────────

def test_create_access_token_returns_tuple():
    token, jti = create_access_token("user-123")
    assert isinstance(token, str)
    assert isinstance(jti, str)
    assert len(jti) == 36  # UUID4 string length


def test_decode_access_token_returns_correct_subject():
    token, _ = create_access_token("user-abc")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-abc"


def test_decoded_token_contains_jti():
    token, jti = create_access_token("user-abc")
    payload = decode_access_token(token)
    assert payload["jti"] == jti


def test_each_token_has_unique_jti():
    _, jti1 = create_access_token("user-1")
    _, jti2 = create_access_token("user-1")
    assert jti1 != jti2


def test_decode_tampered_token_raises():
    token, _ = create_access_token("user-1")
    # Flip the last character to invalidate the signature
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(JWTError):
        decode_access_token(tampered)


def test_decode_garbage_string_raises():
    with pytest.raises(JWTError):
        decode_access_token("not.a.token")
