import pytest


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
