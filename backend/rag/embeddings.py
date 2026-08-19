"""
Embedding service.

Kept behind a small abstract interface so the provider is swappable (per
spec section 15) - today it's Gemini, but a HuggingFace or local-model
implementation could be dropped in without touching any caller.
"""
from abc import ABC, abstractmethod

import google.generativeai as genai

from app.errors import EmbeddingFailedError
from rag.gemini import GeminiProviderPool, GeminiProviderUnavailableError, get_gemini_provider_pool


class EmbeddingService(ABC):
    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of chunk texts (task type: retrieval document)."""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Embed a single search query (task type: retrieval query)."""


class GeminiEmbeddingService(EmbeddingService):
    def __init__(self, provider_pool: GeminiProviderPool | None = None):
        from app.config import settings

        self.model = settings.gemini_embedding_model
        self.provider_pool = provider_pool or get_gemini_provider_pool()

    async def _embed(self, text: str, task_type: str) -> list[float]:
        try:
            result = await self.provider_pool.run(
                operation="embedding",
                model=self.model,
                call=lambda provider: genai.embed_content(
                    model=self.model,
                    content=text,
                    task_type=task_type,
                    client=provider.client,
                ),
            )
            return result["embedding"]
        except GeminiProviderUnavailableError as exc:
            raise EmbeddingFailedError("Gemini embedding service is temporarily unavailable. Please try again.") from exc
        except Exception as exc:
            raise EmbeddingFailedError(f"Gemini embedding call failed: {exc}") from exc

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        # The installed SDK batches up to 100 requests per API call. Reuse an
        # embedding for duplicate chunk text while preserving caller ordering.
        unique_texts = list(dict.fromkeys(texts))
        try:
            result = await self.provider_pool.run(
                operation="embedding",
                model=self.model,
                call=lambda provider: genai.embed_content(
                    model=self.model,
                    content=unique_texts,
                    task_type="retrieval_document",
                    client=provider.client,
                ),
            )
            unique_embeddings = result["embedding"]
        except GeminiProviderUnavailableError as exc:
            raise EmbeddingFailedError("Gemini embedding service is temporarily unavailable. Please try again.") from exc
        except Exception as exc:
            raise EmbeddingFailedError(f"Gemini embedding call failed: {exc}") from exc

        if len(unique_embeddings) != len(unique_texts):
            raise EmbeddingFailedError("Gemini returned an unexpected number of document embeddings.")

        embedding_by_text = dict(zip(unique_texts, unique_embeddings))
        return [embedding_by_text[text] for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        return await self._embed(text, task_type="retrieval_query")


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = GeminiEmbeddingService()
    return _embedding_service
