import asyncio
import os
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("GEMINI_API_KEY", "")

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from models import chunk, conversation, document, feedback, message, suggestion, user  # noqa: E402,F401


@pytest_asyncio.fixture(autouse=True)
async def _fresh_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture(autouse=True)
def _mock_supabase_storage(monkeypatch):
    storage = {}

    async def fake_upload(storage_path: str, contents: bytes, mime_type: str) -> None:
        storage[storage_path] = contents

    async def fake_download(storage_path: str) -> bytes:
        if storage_path not in storage:
            raise RuntimeError(f"Storage path {storage_path} not found")
        return storage[storage_path]

    async def fake_delete(storage_path: str) -> None:
        storage.pop(storage_path, None)

    monkeypatch.setattr("services.document_service._upload_storage_object", fake_upload)
    monkeypatch.setattr("services.document_service._download_storage_object", fake_download)
    monkeypatch.setattr("services.document_service._delete_storage_object", fake_delete)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def registration_payload_factory():
    def factory(**overrides):
        payload = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "organization": "Acme Corp",
            "phone": "9876543210",
            "age": 30,
            "gender": "Male",
            "marital_status": "Single",
            "citizenship": "Indian",
            "occupation": "Engineer",
            "employment_status": "Employed",
            "annual_income": "750000",
            "address": "123 Main Street",
            "country": "India",
            "state": "Maharashtra",
            "city": "Mumbai",
            "pin_code": "400001",
            "smoker_status": "No",
            "existing_conditions": "No known conditions",
            "emergency_contact_name": "Emergency Contact",
            "emergency_contact_phone": "9999999999",
            "education_level": "Graduate",
            "family_status": "Nuclear family",
            "father_name": "Father Name",
            "mother_name": "Mother Name",
            "disability_status": "No",
            "critical_illness": "No",
            "employer": "Acme Corp",
            "date_of_birth": "1995-01-01",
            "dependents_count": 0,
            "alcohol_use": "No",
            "insurance_history": "None",
            "nominee_name": "Nominee Name",
            "nominee_relation": "Sibling",
        }
        payload.update(overrides)
        return payload

    return factory
