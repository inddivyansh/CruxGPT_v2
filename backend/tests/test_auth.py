import pytest
from sqlalchemy import select

from app.database import AsyncSessionLocal
from models.user import User


@pytest.mark.asyncio
async def test_register_and_login(client, registration_payload_factory):
    resp = await client.post(
        "/api/auth/register",
        json=registration_payload_factory(name="Alice", email="alice@example.com"),
    )
    assert resp.status_code == 201
    tokens = resp.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    login_resp = await client.post(
        "/api/auth/login", json={"email": "alice@example.com", "password": "password123"}
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_register_minimal_required_fields_only(client):
    """User can register with only name, email, and password."""
    resp = await client.post(
        "/api/auth/register",
        json={"name": "Fast Signup", "email": "fast@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    tokens = resp.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    login_resp = await client.post(
        "/api/auth/login", json={"email": "fast@example.com", "password": "password123"}
    )
    assert login_resp.status_code == 200

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == "fast@example.com"))).scalar_one()
        assert user.name == "Fast Signup"
        assert user.phone is None
        assert user.age is None


@pytest.mark.asyncio
async def test_register_partial_optional_profile_persisted(client):
    """User registering with partial profile fields persists them correctly."""
    resp = await client.post(
        "/api/auth/register",
        json={
            "name": "Partial Profile",
            "email": "partial@example.com",
            "password": "password123",
            "age": 28,
            "phone": "9876543210",
            "city": "San Francisco",
            "organization": "Acme Health",
        },
    )
    assert resp.status_code == 201

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == "partial@example.com"))).scalar_one()
        assert user.age == 28
        assert user.phone == "9876543210"
        assert user.city == "San Francisco"
        assert user.organization == "Acme Health"
        assert user.nominee_name is None


@pytest.mark.asyncio
async def test_register_invalid_optional_values_rejected(client):
    """Invalid optional profile constraints are rejected when provided."""
    # Age > 150
    resp_age = await client.post(
        "/api/auth/register",
        json={"name": "Invalid Age", "email": "inv_age@example.com", "password": "password123", "age": 250},
    )
    assert resp_age.status_code == 422

    # Phone too short (< 7 chars)
    resp_phone = await client.post(
        "/api/auth/register",
        json={"name": "Invalid Phone", "email": "inv_phone@example.com", "password": "password123", "phone": "123"},
    )
    assert resp_phone.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_email_rejected(client, registration_payload_factory):
    payload = registration_payload_factory(name="Alice", email="dup@example.com")
    r1 = await client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/api/auth/register", json=payload)
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "DUPLICATE_EMAIL"


@pytest.mark.asyncio
async def test_invalid_password_rejected(client, registration_payload_factory):
    await client.post(
        "/api/auth/register", json=registration_payload_factory(name="Bob", email="bob@example.com")
    )
    resp = await client.post("/api/auth/login", json={"email": "bob@example.com", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_authenticated_user(client, registration_payload_factory):
    reg = await client.post(
        "/api/auth/register", json=registration_payload_factory(name="Carol", email="carol@example.com")
    )
    token = reg.json()["access_token"]
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "carol@example.com"
    assert resp.json()["role"] == "user"
