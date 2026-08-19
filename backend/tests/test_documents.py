import pytest


async def _register(client, email="doc-user@example.com", registration_payload_factory=None):
    payload_factory = registration_payload_factory or (lambda **overrides: {
        "name": "Doc User",
        "email": email,
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
        **overrides,
    })
    resp = await client.post(
        "/api/auth/register", json=payload_factory(name="Doc User", email=email)
    )
    return resp.json()["access_token"]


async def _create_conversation(client, token, title="Test conversation"):
    resp = await client.post(
        "/api/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": title},
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_upload_txt_document(client, registration_payload_factory):
    token = await _register(client, registration_payload_factory=registration_payload_factory)
    conv_id = await _create_conversation(client, token)
    resp = await client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"conversation_id": conv_id},
        files={"file": ("policy.txt", b"This is a test policy document.", "text/plain")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["original_filename"] == "policy.txt"
    assert body["status"] == "uploaded"


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_type(client, registration_payload_factory):
    token = await _register(client, registration_payload_factory=registration_payload_factory)
    conv_id = await _create_conversation(client, token)
    resp = await client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"conversation_id": conv_id},
        files={"file": ("virus.exe", b"MZ...", "application/x-msdownload")},
    )
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


@pytest.mark.asyncio
async def test_upload_rejects_oversized_file(client, registration_payload_factory):
    token = await _register(client, registration_payload_factory=registration_payload_factory)
    conv_id = await _create_conversation(client, token)
    big_content = b"x" * (11 * 1024 * 1024)  # 11MB > 10MB default limit
    resp = await client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"conversation_id": conv_id},
        files={"file": ("big.txt", big_content, "text/plain")},
    )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "FILE_TOO_LARGE"


@pytest.mark.asyncio
async def test_upload_requires_auth(client):
    resp = await client.post(
        "/api/documents/upload",
        data={"conversation_id": "any-id"},
        files={"file": ("policy.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_user_cannot_access_other_users_document(client, registration_payload_factory):
    token_a = await _register(client, "doc-a@example.com", registration_payload_factory)
    token_b = await _register(client, "doc-b@example.com", registration_payload_factory)
    conv_id = await _create_conversation(client, token_a)

    upload = await client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        data={"conversation_id": conv_id},
        files={"file": ("policy.txt", b"secret content", "text/plain")},
    )
    doc_id = upload.json()["id"]

    resp = await client.get(f"/api/documents/{doc_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_list_documents_scoped_to_user(client, registration_payload_factory):
    token_a = await _register(client, "list-a@example.com", registration_payload_factory)
    token_b = await _register(client, "list-b@example.com", registration_payload_factory)
    conv_a = await _create_conversation(client, token_a)

    await client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        data={"conversation_id": conv_a},
        files={"file": ("a.txt", b"content a", "text/plain")},
    )

    resp_a = await client.get("/api/documents", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = await client.get("/api/documents", headers={"Authorization": f"Bearer {token_b}"})

    assert len(resp_a.json()) == 1
    assert len(resp_b.json()) == 0


@pytest.mark.asyncio
async def test_storage_usage_reporting_and_deletion_refresh(client, registration_payload_factory):
    """GET /api/documents/storage accurately reflects used and remaining bytes."""
    token = await _register(client, "storage-test@example.com", registration_payload_factory)
    conv_id = await _create_conversation(client, token)

    # Initial storage usage is 0
    resp = await client.get(
        f"/api/documents/storage?conversation_id={conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    usage = resp.json()
    assert usage["used_bytes"] == 0
    assert usage["max_bytes"] == 100 * 1024 * 1024
    assert usage["remaining_bytes"] == 100 * 1024 * 1024
    assert usage["document_count"] == 0

    # Upload document
    doc_content = b"A" * 1024  # 1 KB
    upload_resp = await client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"conversation_id": conv_id},
        files={"file": ("doc.txt", doc_content, "text/plain")},
    )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]

    # Storage usage increases
    resp_after = await client.get(
        f"/api/documents/storage?conversation_id={conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_after.status_code == 200
    usage_after = resp_after.json()
    assert usage_after["used_bytes"] == 1024
    assert usage_after["remaining_bytes"] == (100 * 1024 * 1024) - 1024
    assert usage_after["document_count"] == 1

    # Delete document -> storage usage returns to 0
    del_resp = await client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 204

    resp_after_del = await client.get(
        f"/api/documents/storage?conversation_id={conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_after_del.status_code == 200
    usage_after_del = resp_after_del.json()
    assert usage_after_del["used_bytes"] == 0
    assert usage_after_del["remaining_bytes"] == 100 * 1024 * 1024
    assert usage_after_del["document_count"] == 0
