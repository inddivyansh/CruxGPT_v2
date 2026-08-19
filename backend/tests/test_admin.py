import pytest
from sqlalchemy import select

from app.database import AsyncSessionLocal
from models.user import User


@pytest.mark.asyncio
async def test_normal_user_denied_admin_stats(client, registration_payload_factory):
    reg = await client.post(
        "/api/auth/register", json=registration_payload_factory(name="User", email="normal@example.com")
    )
    token = reg.json()["access_token"]
    resp = await client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_admin_user_can_access_stats(client, registration_payload_factory):
    reg = await client.post(
        "/api/auth/register", json=registration_payload_factory(name="Admin", email="admin@example.com")
    )
    token = reg.json()["access_token"]

    # Promote to admin directly in DB - there is intentionally no self-service
    # "become admin" API endpoint.
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@example.com"))
        user = result.scalar_one()
        user.role = "admin"
        await db.commit()

    resp = await client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert "overall_accuracy" in body
    assert "total_users" in body


@pytest.mark.asyncio
async def test_admin_stats_honest_when_no_feedback_data(client, registration_payload_factory):
    reg = await client.post(
        "/api/auth/register", json=registration_payload_factory(name="Admin2", email="admin2@example.com")
    )
    token = reg.json()["access_token"]
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin2@example.com"))
        user = result.scalar_one()
        user.role = "admin"
        await db.commit()

    resp = await client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["overall_accuracy"] == "Not enough evaluation data"
