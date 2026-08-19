import hashlib
import json
from types import SimpleNamespace
import uuid

import pytest
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.errors import DocumentNotFoundError
from models.chunk import DocumentChunk
from models.conversation import Conversation
from models.document import Document
from models.user import User
from rag import embeddings as embeddings_module
from rag.embeddings import GeminiEmbeddingService
from rag.gemini import GeminiProviderPool
from rag.prompt import MAX_CONTEXT_CHARS, ContextChunk, format_context, select_context_chunks
from schemas.chat import ChatRequest
from services.chat_service import answer_query
from services.document_service import process_document, save_upload


class _RateLimitError(Exception):
    code = 429


@pytest.mark.asyncio
async def test_primary_provider_works_without_secondary():
    pool = GeminiProviderPool("primary-key", retry_base_seconds=0)
    slots = []

    result = await pool.run("embedding", "model", lambda provider: slots.append(provider.slot) or "ok")

    assert result == "ok"
    assert slots == ["primary"]


@pytest.mark.asyncio
async def test_rate_limited_primary_retries_then_falls_back_to_secondary():
    pool = GeminiProviderPool("primary-key", "secondary-key", retry_base_seconds=0)
    slots = []

    def call(provider):
        slots.append(provider.slot)
        if provider.slot == "primary":
            raise _RateLimitError()
        return "secondary-result"

    result = await pool.run("embedding", "model", call)

    assert result == "secondary-result"
    assert slots == ["primary", "primary", "primary", "secondary"]


class _PassthroughPool:
    async def run(self, operation, model, call):
        return call(SimpleNamespace(client=object()))


@pytest.mark.asyncio
async def test_document_embeddings_batch_and_reuse_duplicate_text(monkeypatch):
    requests = []

    def fake_embed_content(**kwargs):
        requests.append(kwargs["content"])
        return {"embedding": [[1.0], [2.0]]}

    monkeypatch.setattr(embeddings_module.genai, "embed_content", fake_embed_content)
    service = GeminiEmbeddingService(provider_pool=_PassthroughPool())

    embeddings = await service.embed_documents(["first", "second", "first"])

    assert requests == [["first", "second"]]
    assert embeddings == [[1.0], [2.0], [1.0]]


@pytest.mark.asyncio
async def test_document_embeddings_batches_over_100_unique_texts(monkeypatch):
    batches = []

    def fake_embed_content(**kwargs):
        content = kwargs["content"]
        batches.append(content)
        return {"embedding": [[float(i)] for i in range(len(content))]}

    monkeypatch.setattr(embeddings_module.genai, "embed_content", fake_embed_content)
    service = GeminiEmbeddingService(provider_pool=_PassthroughPool())

    # 150 unique texts -> must split into batch of 100 + batch of 50 (ceil(150/100) = 2)
    texts = [f"unique_text_{i}" for i in range(150)]
    embeddings = await service.embed_documents(texts)

    assert len(batches) == 2
    assert len(batches[0]) == 100
    assert len(batches[1]) == 50
    assert len(embeddings) == 150


@pytest.mark.asyncio
async def test_embed_documents_empty_returns_empty():
    service = GeminiEmbeddingService(provider_pool=_PassthroughPool())
    assert await service.embed_documents([]) == []


def test_context_selection_deduplicates_chunks_and_preserves_source_metadata():
    first = SimpleNamespace(document_id="doc-1", text="covered surgery", page_number=3, section="Benefits")
    duplicate = SimpleNamespace(document_id="doc-2", text="covered   surgery", page_number=7, section="Other")
    second = SimpleNamespace(document_id="doc-2", text="waiting period", page_number=4, section="Limits")

    selected = select_context_chunks(
        [(first, 0.9), (duplicate, 0.8), (second, 0.7)],
        {"doc-1": "Policy A", "doc-2": "Policy B"},
    )
    context = format_context(selected, {"doc-1": "Policy A", "doc-2": "Policy B"})

    assert [(chunk.document_id, score) for chunk, score in selected] == [("doc-1", 0.9), ("doc-2", 0.7)]
    assert "Policy A" in context and "page 3" in context
    assert "Policy B" in context and "page 4" in context


def test_context_selection_enforces_hard_12k_limit_and_truncates_oversized_chunk():
    huge_text_1 = "Alpha clause. " * 600  # ~8400 chars
    huge_text_2 = "Beta exclusion. " * 600  # ~9600 chars

    first = SimpleNamespace(document_id="doc-1", text=huge_text_1, page_number=1, section="Section 1")
    second = SimpleNamespace(document_id="doc-2", text=huge_text_2, page_number=2, section="Section 2")

    selected = select_context_chunks(
        [(first, 0.95), (second, 0.85)],
        {"doc-1": "Policy A", "doc-2": "Policy B"},
        max_chars=MAX_CONTEXT_CHARS,
    )
    context = format_context(selected, {"doc-1": "Policy A", "doc-2": "Policy B"})

    assert len(context) <= MAX_CONTEXT_CHARS
    # Both chunks are represented; the second one is truncated with an ellipsis
    assert len(selected) == 2
    assert selected[0][0].document_id == "doc-1"
    assert selected[1][0].document_id == "doc-2"
    assert selected[1][0].text.endswith("…")


# ---------------------------------------------------------------------------
# Database & Service Layer Tests: Retrieval Isolation, Dedup, Idempotency
# ---------------------------------------------------------------------------

async def _create_test_user(db, email="user@test.com"):
    user = User(
        email=email,
        name="Test User",
        password_hash="hash",
        organization="Org",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_test_conversation(db, user_id, title="Test Conv"):
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def _create_indexed_document(db, user_id, conversation_id, content: str, filename="doc.txt"):
    doc = Document(
        user_id=user_id,
        conversation_id=conversation_id,
        filename=f"{uuid.uuid4()}.txt",
        original_filename=filename,
        mime_type="text/plain",
        file_size=len(content.encode()),
        content_sha256=hashlib.sha256(content.encode()).hexdigest(),
        embedding_model=settings.gemini_embedding_model,
        status="indexed",
        storage_path=f"{user_id}/{conversation_id}/{uuid.uuid4()}/doc.txt",
        page_count=1,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    embedding_vector = [0.1] * settings.gemini_embedding_dimensions
    chunk = DocumentChunk(
        document_id=doc.id,
        user_id=user_id,
        chunk_index=0,
        text=content,
        page_number=1,
        section="Main",
        embedding_json=json.dumps(embedding_vector),
        embedding_dim=len(embedding_vector),
    )
    db.add(chunk)
    await db.commit()
    return doc


@pytest.mark.asyncio
async def test_retrieval_isolation_same_user_different_conversations(monkeypatch):
    """Chunks in Conversation 1 must never be returned when chatting in Conversation 2."""
    async with AsyncSessionLocal() as db:
        user = await _create_test_user(db, "isolation_same_user@test.com")
        conv1 = await _create_test_conversation(db, user.id, "Conv 1")
        conv2 = await _create_test_conversation(db, user.id, "Conv 2")

        await _create_indexed_document(db, user.id, conv1.id, "Surgery covered under Conv 1 policy", "doc1.txt")
        await _create_indexed_document(db, user.id, conv2.id, "Dentistry covered under Conv 2 policy", "doc2.txt")

    # Mock embedding and generation
    dummy_vec = [0.1] * settings.gemini_embedding_dimensions

    class _MockEmbedService:
        async def embed_query(self, text):
            return dummy_vec

        async def embed_documents(self, texts):
            return [dummy_vec for _ in texts]

    class _MockGenerator:
        async def generate(self, query, action, context, history):
            return SimpleNamespace(
                answer="Generated answer",
                decision="Covered",
                conditions=[],
                exclusions=[],
                confidence=0.9,
            )

    monkeypatch.setattr("services.chat_service.get_generator", lambda: _MockGenerator())
    monkeypatch.setattr("rag.retriever.get_embedding_service", lambda: _MockEmbedService())

    async with AsyncSessionLocal() as db:
        # Chat in Conv 1
        resp_conv1 = await answer_query(
            db,
            user.id,
            ChatRequest(conversation_id=conv1.id, message="Tell me about surgery"),
        )
        assert len(resp_conv1.sources) == 1
        assert "doc1.txt" in resp_conv1.sources[0].document_name

        # Chat in Conv 2
        resp_conv2 = await answer_query(
            db,
            user.id,
            ChatRequest(conversation_id=conv2.id, message="Tell me about surgery"),
        )
        assert len(resp_conv2.sources) == 1
        assert "doc2.txt" in resp_conv2.sources[0].document_name


@pytest.mark.asyncio
async def test_retrieval_isolation_different_users(monkeypatch):
    """User B chatting must never retrieve User A's chunks."""
    async with AsyncSessionLocal() as db:
        user_a = await _create_test_user(db, "user_a@test.com")
        user_b = await _create_test_user(db, "user_b@test.com")

        conv_a = await _create_test_conversation(db, user_a.id, "Conv A")
        conv_b = await _create_test_conversation(db, user_b.id, "Conv B")

        await _create_indexed_document(db, user_a.id, conv_a.id, "Secret data of User A", "secret.txt")

    dummy_vec = [0.1] * settings.gemini_embedding_dimensions

    class _MockEmbedService:
        async def embed_query(self, text):
            return dummy_vec

    class _MockGenerator:
        async def generate(self, query, action, context, history):
            return SimpleNamespace(
                answer="No docs",
                decision=None,
                conditions=[],
                exclusions=[],
                confidence=0.0,
            )

    monkeypatch.setattr("services.chat_service.get_generator", lambda: _MockGenerator())
    monkeypatch.setattr("rag.retriever.get_embedding_service", lambda: _MockEmbedService())

    async with AsyncSessionLocal() as db:
        resp = await answer_query(
            db,
            user_b.id,
            ChatRequest(conversation_id=conv_b.id, message="Show me secret data"),
        )
        assert resp.sources == []


@pytest.mark.asyncio
async def test_retrieval_explicit_inaccessible_document_raises_404():
    """Passing a document_id from another conversation or user raises DocumentNotFoundError."""
    async with AsyncSessionLocal() as db:
        user_a = await _create_test_user(db, "inacc_a@test.com")
        user_b = await _create_test_user(db, "inacc_b@test.com")

        conv_a = await _create_test_conversation(db, user_a.id, "Conv A")
        conv_b = await _create_test_conversation(db, user_b.id, "Conv B")

        doc_a = await _create_indexed_document(db, user_a.id, conv_a.id, "Doc A text", "doc_a.txt")

        with pytest.raises(DocumentNotFoundError):
            await answer_query(
                db,
                user_b.id,
                ChatRequest(
                    conversation_id=conv_b.id,
                    message="Query",
                    document_ids=[doc_a.id],
                ),
            )


def _make_upload_file(filename: str, content: bytes, content_type: str = "text/plain"):
    class FakeUploadFile:
        def __init__(self):
            self.filename = filename
            self.content_type = content_type

        async def read(self):
            return content

    return FakeUploadFile()


@pytest.mark.asyncio
async def test_duplicate_document_upload_reuses_embeddings_without_gemini_calls(monkeypatch):
    """Uploading the exact same document by the same user reuses existing chunks with ZERO embedding calls."""
    embed_calls = []

    class _MockEmbedService:
        async def embed_documents(self, texts):
            embed_calls.append(texts)
            return [[0.5] * settings.gemini_embedding_dimensions for _ in texts]

    monkeypatch.setattr("services.document_service.get_embedding_service", lambda: _MockEmbedService())

    content = b"This is unique insurance policy text for SHA256 deduplication testing."

    async with AsyncSessionLocal() as db:
        user = await _create_test_user(db, "dedup_user@test.com")
        conv1 = await _create_test_conversation(db, user.id, "Conv 1")
        conv2 = await _create_test_conversation(db, user.id, "Conv 2")

        doc1 = await save_upload(db, user.id, _make_upload_file("policy_first.txt", content), conv1.id)
        await process_document(db, doc1.id)

        assert len(embed_calls) == 1, "First upload must call embedding service"

        # Now upload the exact same content to Conv 2
        doc2 = await save_upload(db, user.id, _make_upload_file("policy_second.txt", content), conv2.id)
        await process_document(db, doc2.id)

        # Embedding service must NOT be called again!
        assert len(embed_calls) == 1, "Duplicate upload must reuse embeddings (0 new embedding calls)"

        # Verify doc2 is indexed with its own chunk records referencing doc2.id
        doc2_reloaded = (await db.execute(select(Document).where(Document.id == doc2.id))).scalar_one()
        assert doc2_reloaded.status == "indexed"

        chunks_doc2 = (
            await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc2.id))
        ).scalars().all()
        assert len(chunks_doc2) >= 1
        assert all(c.document_id == doc2.id for c in chunks_doc2)
        assert all(c.user_id == user.id for c in chunks_doc2)


@pytest.mark.asyncio
async def test_duplicate_document_different_user_does_not_reuse_embeddings(monkeypatch):
    """Uploading the same file by a DIFFERENT user must NEVER reuse chunks across users."""
    embed_calls = []

    class _MockEmbedService:
        async def embed_documents(self, texts):
            embed_calls.append(texts)
            return [[0.5] * settings.gemini_embedding_dimensions for _ in texts]

    monkeypatch.setattr("services.document_service.get_embedding_service", lambda: _MockEmbedService())

    content = b"Cross user isolation test file content."

    async with AsyncSessionLocal() as db:
        user_a = await _create_test_user(db, "user_alpha@test.com")
        user_b = await _create_test_user(db, "user_beta@test.com")

        conv_a = await _create_test_conversation(db, user_a.id, "Conv A")
        conv_b = await _create_test_conversation(db, user_b.id, "Conv B")

        doc_a = await save_upload(
            db, user_a.id, _make_upload_file("a.txt", content), conv_a.id
        )
        await process_document(db, doc_a.id)

        assert len(embed_calls) == 1

        # User B uploads the same file
        doc_b = await save_upload(
            db, user_b.id, _make_upload_file("b.txt", content), conv_b.id
        )
        await process_document(db, doc_b.id)

        assert len(embed_calls) == 2, "Different user must not reuse another user's embeddings"


@pytest.mark.asyncio
async def test_duplicate_document_different_model_does_not_reuse(monkeypatch):
    """Document indexed with a different model is not reused if model changes."""
    embed_calls = []

    class _MockEmbedService:
        async def embed_documents(self, texts):
            embed_calls.append(texts)
            return [[0.5] * settings.gemini_embedding_dimensions for _ in texts]

    monkeypatch.setattr("services.document_service.get_embedding_service", lambda: _MockEmbedService())

    content = b"Model mismatch test content."

    async with AsyncSessionLocal() as db:
        user = await _create_test_user(db, "model_mismatch@test.com")
        conv1 = await _create_test_conversation(db, user.id, "Conv 1")
        conv2 = await _create_test_conversation(db, user.id, "Conv 2")

        # Manually create doc1 with old model
        doc1 = await _create_indexed_document(db, user.id, conv1.id, content.decode(), "old_doc.txt")
        doc1.embedding_model = "old-embedding-model-v1"
        await db.commit()

        # Upload doc2 with current settings.gemini_embedding_model
        doc2 = await save_upload(
            db, user.id, _make_upload_file("new_doc.txt", content), conv2.id
        )
        await process_document(db, doc2.id)

        assert len(embed_calls) == 1, "Must embed anew because embedding model differs"


@pytest.mark.asyncio
async def test_idempotent_indexing_already_indexed_document_is_noop(monkeypatch):
    """Calling process_document on already indexed document does not re-embed or duplicate chunks."""
    embed_calls = []

    class _MockEmbedService:
        async def embed_documents(self, texts):
            embed_calls.append(texts)
            return [[0.5] * settings.gemini_embedding_dimensions for _ in texts]

    monkeypatch.setattr("services.document_service.get_embedding_service", lambda: _MockEmbedService())

    content = b"Idempotent processing test."

    async with AsyncSessionLocal() as db:
        user = await _create_test_user(db, "idempotent@test.com")
        conv = await _create_test_conversation(db, user.id, "Conv")

        doc = await save_upload(
            db, user.id, _make_upload_file("test.txt", content), conv.id
        )
        await process_document(db, doc.id)

        assert len(embed_calls) == 1
        initial_chunks = (
            await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
        ).scalars().all()
        assert len(initial_chunks) >= 1

        # Process a second time
        await process_document(db, doc.id)
        assert len(embed_calls) == 1, "Second processing must not invoke embedding"

        final_chunks = (
            await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
        ).scalars().all()
        assert len(final_chunks) == len(initial_chunks), "Chunk count must remain identical"


@pytest.mark.asyncio
async def test_failed_document_retries_and_cleans_up_incomplete_chunks(monkeypatch):
    """A failed document with leftover chunks cleans them up on retry and indexes cleanly."""
    embed_calls = []

    class _MockEmbedService:
        async def embed_documents(self, texts):
            embed_calls.append(texts)
            return [[0.5] * settings.gemini_embedding_dimensions for _ in texts]

    monkeypatch.setattr("services.document_service.get_embedding_service", lambda: _MockEmbedService())

    content = b"Retry cleanup test content."

    async with AsyncSessionLocal() as db:
        user = await _create_test_user(db, "retry_cleanup@test.com")
        conv = await _create_test_conversation(db, user.id, "Conv")

        doc = await save_upload(
            db, user.id, _make_upload_file("retry.txt", content), conv.id
        )
        # Mark as failed with leftover corrupt chunk
        doc.status = "failed"
        corrupt_chunk = DocumentChunk(
            document_id=doc.id,
            user_id=user.id,
            chunk_index=0,
            text="corrupt",
            embedding_json="invalid json",
            embedding_dim=10,
        )
        db.add(corrupt_chunk)
        await db.commit()

        # Retry processing
        await process_document(db, doc.id)

        reloaded = (await db.execute(select(Document).where(Document.id == doc.id))).scalar_one()
        assert reloaded.status == "indexed"
        assert reloaded.error_message is None

        chunks = (
            await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
        ).scalars().all()
        assert len(chunks) >= 1
        assert all(c.embedding_dim == settings.gemini_embedding_dimensions for c in chunks)


@pytest.mark.asyncio
async def test_chat_call_counts_exactly_one_query_embedding_and_one_generation(monkeypatch):
    """One normal chat question performs exactly 1 query embedding + 1 generation."""
    query_embed_calls = []
    generation_calls = []

    dummy_vec = [0.1] * settings.gemini_embedding_dimensions

    class _MockEmbedService:
        async def embed_query(self, text):
            query_embed_calls.append(text)
            return dummy_vec

    class _MockGenerator:
        async def generate(self, query, action, context, history):
            generation_calls.append(query)
            return SimpleNamespace(
                answer="Answer text",
                decision="Covered",
                conditions=[],
                exclusions=[],
                confidence=0.9,
            )

    monkeypatch.setattr("services.chat_service.get_generator", lambda: _MockGenerator())
    monkeypatch.setattr("rag.retriever.get_embedding_service", lambda: _MockEmbedService())

    async with AsyncSessionLocal() as db:
        user = await _create_test_user(db, "call_counts@test.com")
        conv = await _create_test_conversation(db, user.id, "Conv")
        await _create_indexed_document(db, user.id, conv.id, "Surgery covered under policy", "policy.txt")

        # First question
        await answer_query(
            db,
            user.id,
            ChatRequest(conversation_id=conv.id, message="Is surgery covered?"),
        )
        assert len(query_embed_calls) == 1
        assert len(generation_calls) == 1

        # Second question
        await answer_query(
            db,
            user.id,
            ChatRequest(conversation_id=conv.id, message="What about hospital stays?"),
        )
        assert len(query_embed_calls) == 2
        assert len(generation_calls) == 2
