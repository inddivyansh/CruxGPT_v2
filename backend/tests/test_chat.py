import hashlib

import pytest

from rag import embeddings as emb_mod
from rag import generator as gen_mod


class _FakeEmbeddingService:
    async def embed_documents(self, texts):
        return [[b / 255.0 for b in hashlib.md5(t.encode()).digest()] for t in texts]

    async def embed_query(self, text):
        return (await self.embed_documents([text]))[0]


class _FakeGenerationResult:
    def __init__(self, has_context: bool):
        if has_context:
            self.answer = "Yes, this appears to be covered, subject to the stated waiting periods."
            self.decision = "Likely Covered"
            self.conditions = ["Waiting period applies"]
            self.exclusions = ["Pre-existing conditions excluded"]
            self.confidence = 0.85
            self.insufficient_context = False
        else:
            self.answer = "I could not find relevant information in your uploaded documents."
            self.decision = None
            self.conditions = []
            self.exclusions = []
            self.confidence = 0.0
            self.insufficient_context = True


class _FakeGenerator:
    async def generate(self, query, action, context, history):
        has_context = "No relevant document context" not in context
        return _FakeGenerationResult(has_context)


@pytest.fixture(autouse=True)
def _patch_gemini():
    emb_mod._embedding_service = _FakeEmbeddingService()
    gen_mod._generator = _FakeGenerator()
    yield
    emb_mod._embedding_service = None
    gen_mod._generator = None


async def _register(client, email, registration_payload_factory):
    resp = await client.post("/api/auth/register", json=registration_payload_factory(name="Test", email=email))
    return resp.json()["access_token"]


async def _upload_and_index(client, token, filename="policy.txt", content=b"Knee surgery is covered under Surgical Coverage, subject to a 90-day waiting period."):
    resp = await client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, content, "text/plain")},
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_chat_requires_auth(client):
    resp = await client.post("/api/chat", json={"message": "hello"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_chat_answers_from_indexed_document(client, registration_payload_factory):
    token = await _register(client, "chat-user@example.com", registration_payload_factory)
    doc_id = await _upload_and_index(client, token)

    resp = await client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Does this policy cover knee surgery?", "action": "search_policy"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "Likely Covered"
    assert len(body["sources"]) >= 1
    assert body["sources"][0]["document_id"] == doc_id
    assert "conversation_id" in body and "message_id" in body


@pytest.mark.asyncio
async def test_chat_never_returns_another_users_documents(client, registration_payload_factory):
    token_a = await _register(client, "iso-a@example.com", registration_payload_factory)
    token_b = await _register(client, "iso-b@example.com", registration_payload_factory)
    await _upload_and_index(client, token_a)

    resp = await client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"message": "Does this policy cover knee surgery?", "action": "search_policy"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["sources"] == [], "SECURITY REGRESSION: user B retrieved user A's document chunks"


@pytest.mark.asyncio
async def test_conversation_persists_and_is_retrievable(client, registration_payload_factory):
    token = await _register(client, "conv-user@example.com", registration_payload_factory)
    await _upload_and_index(client, token)

    chat_resp = await client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Does this policy cover knee surgery?"},
    )
    conversation_id = chat_resp.json()["conversation_id"]

    list_resp = await client.get("/api/conversations", headers={"Authorization": f"Bearer {token}"})
    assert any(c["id"] == conversation_id for c in list_resp.json())

    detail_resp = await client.get(
        f"/api/conversations/{conversation_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert detail_resp.status_code == 200
    messages = detail_resp.json()["messages"]
    assert len(messages) == 2  # user + assistant
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_feedback_submission(client, registration_payload_factory):
    token = await _register(client, "fb-user@example.com", registration_payload_factory)
    await _upload_and_index(client, token)
    chat_resp = await client.post(
        "/api/chat", headers={"Authorization": f"Bearer {token}"}, json={"message": "Coverage?"}
    )
    message_id = chat_resp.json()["message_id"]

    fb_resp = await client.post(
        f"/api/messages/{message_id}/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={"feedback": "positive"},
    )
    assert fb_resp.status_code == 201


@pytest.mark.asyncio
async def test_conversation_isolation(client, registration_payload_factory):
    token_a = await _register(client, "convsio-a@example.com", registration_payload_factory)
    token_b = await _register(client, "convsio-b@example.com", registration_payload_factory)

    chat_resp = await client.post(
        "/api/chat", headers={"Authorization": f"Bearer {token_a}"}, json={"message": "hello"}
    )
    conversation_id = chat_resp.json()["conversation_id"]

    resp = await client.get(f"/api/conversations/{conversation_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"
