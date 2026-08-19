from types import SimpleNamespace

import pytest

from rag import embeddings as embeddings_module
from rag.embeddings import GeminiEmbeddingService
from rag.gemini import GeminiProviderPool
from rag.prompt import format_context, select_context_chunks


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


def test_context_selection_deduplicates_chunks_and_preserves_source_metadata():
    first = SimpleNamespace(document_id="doc-1", text="covered surgery", page_number=3, section="Benefits")
    duplicate = SimpleNamespace(document_id="doc-2", text="covered   surgery", page_number=7, section="Other")
    second = SimpleNamespace(document_id="doc-2", text="waiting period", page_number=4, section="Limits")

    selected = select_context_chunks([(first, 0.9), (duplicate, 0.8), (second, 0.7)])
    context = format_context(selected, {"doc-1": "Policy A", "doc-2": "Policy B"})

    assert selected == [(first, 0.9), (second, 0.7)]
    assert "Policy A" in context and "page 3" in context
    assert "Policy B" in context and "page 4" in context
