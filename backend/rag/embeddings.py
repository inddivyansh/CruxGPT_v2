"""
Embedding service.

Kept behind a small abstract interface so the provider is swappable (per
spec section 15) - today it's Gemini, but a HuggingFace or local-model
implementation could be dropped in without touching any caller.
"""
from abc import ABC, abstractmethod

import google.generativeai as genai

from app.config import settings
from app.errors import EmbeddingFailedError


class EmbeddingService(ABC):
    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of chunk texts (task type: retrieval document)."""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Embed a single search query (task type: retrieval query)."""


class GeminiEmbeddingService(EmbeddingService):
    def __init__(self):
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
        self.model = settings.gemini_embedding_model

    def _embed(self, text: str, task_type: str) -> list[float]:
        if not settings.gemini_api_key:
            raise EmbeddingFailedError(
                "GEMINI_API_KEY is not configured on the server. Set it in backend/.env."
            )
        try:
            result = genai.embed_content(model=self.model, content=text, task_type=task_type)
            return result["embedding"]
        except Exception as exc:
            raise EmbeddingFailedError(f"Gemini embedding call failed: {exc}") from exc

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # google-generativeai's embed_content is synchronous; batching is done
        # sequentially here for simplicity/reliability. This is the one spot
        # to parallelize (asyncio.gather + threadpool) if throughput becomes
        # a bottleneck at higher document volumes.
        return [self._embed(text, task_type="retrieval_document") for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._embed(text, task_type="retrieval_query")


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = GeminiEmbeddingService()
    return _embedding_service
