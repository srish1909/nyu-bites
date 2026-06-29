"""
Integration tests for /api/v1/restaurants/* endpoints.
"""

import pytest

# A minimal valid restaurant payload
RESTAURANT_PAYLOAD = {
    "name": "Test Ramen Co",
    "address": "123 Test St, New York, NY",
    "cuisine_type": "Japanese",
    "price_range": 2,
    "discount_type": "percentage",
    "discount_details": "15% off for NYU students",
}


# ── GET /restaurants/ ─────────────────────────────────────────────────────────

async def test_list_restaurants_returns_list(client):
    r = await client.get("/api/v1/restaurants/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


async def test_list_restaurants_respects_limit(client):
    r = await client.get("/api/v1/restaurants/?limit=5")
    assert r.status_code == 200
    assert len(r.json()) <= 5


async def test_list_restaurants_invalid_limit_rejected(client):
    r = await client.get("/api/v1/restaurants/?limit=999")
    assert r.status_code == 422  # limit max is 100


# ── GET /restaurants/{id} ─────────────────────────────────────────────────────

async def test_get_restaurant_not_found(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    r = await client.get(f"/api/v1/restaurants/{fake_id}")
    assert r.status_code == 404


async def test_get_restaurant_invalid_uuid(client):
    r = await client.get("/api/v1/restaurants/not-a-uuid")
    assert r.status_code == 422


# ── POST /restaurants/ ────────────────────────────────────────────────────────

async def test_create_restaurant_requires_auth(client):
    """Unauthenticated request should be rejected."""
    r = await client.post("/api/v1/restaurants/", json=RESTAURANT_PAYLOAD)
    assert r.status_code == 403


async def test_create_restaurant_success(auth_client):
    client, _ = auth_client
    r = await client.post("/api/v1/restaurants/", json=RESTAURANT_PAYLOAD)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == RESTAURANT_PAYLOAD["name"]
    assert body["cuisine_type"] == RESTAURANT_PAYLOAD["cuisine_type"]
    assert body["discount_type"] == RESTAURANT_PAYLOAD["discount_type"]
    assert "id" in body
    assert body["is_verified"] is False  # new submissions start unverified


async def test_created_restaurant_appears_in_list(auth_client):
    client, _ = auth_client

    # Create a restaurant with a unique name
    payload = {**RESTAURANT_PAYLOAD, "name": "Unique Pho Place XYZ"}
    create_r = await client.post("/api/v1/restaurants/", json=payload)
    assert create_r.status_code == 201
    new_id = create_r.json()["id"]

    # It should now be findable by ID
    get_r = await client.get(f"/api/v1/restaurants/{new_id}")
    assert get_r.status_code == 200
    assert get_r.json()["name"] == "Unique Pho Place XYZ"


async def test_create_restaurant_missing_required_field(auth_client):
    client, _ = auth_client
    # Missing "name"
    bad_payload = {k: v for k, v in RESTAURANT_PAYLOAD.items() if k != "name"}
    r = await client.post("/api/v1/restaurants/", json=bad_payload)
    assert r.status_code == 422


# ── PATCH /restaurants/{id}/verify ────────────────────────────────────────────

async def test_verify_nonexistent_restaurant_returns_404(auth_client):
    client, _ = auth_client
    fake_id = "00000000-0000-0000-0000-000000000001"
    r = await client.patch(f"/api/v1/restaurants/{fake_id}/verify")
    assert r.status_code == 404


async def test_verify_restaurant_sets_is_verified(auth_client):
    client, _ = auth_client

    # Create a restaurant (starts unverified)
    create_r = await client.post("/api/v1/restaurants/", json=RESTAURANT_PAYLOAD)
    assert create_r.status_code == 201
    restaurant_id = create_r.json()["id"]
    assert create_r.json()["is_verified"] is False

    # Verify it
    verify_r = await client.patch(f"/api/v1/restaurants/{restaurant_id}/verify")
    assert verify_r.status_code == 200
    assert verify_r.json()["is_verified"] is True
