"""Small, server-only Gemini provider pool with bounded retry and fallback."""
import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

import google.ai.generativelanguage as glm
from google.api_core import exceptions as google_exceptions

from app.config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES_PER_PROVIDER = 2
RETRY_BASE_SECONDS = 0.5
RATE_LIMIT_COOLDOWN_SECONDS = 30
DAILY_QUOTA_COOLDOWN_SECONDS = 300
AUTH_COOLDOWN_SECONDS = 300

Result = TypeVar("Result")


class GeminiProviderUnavailableError(RuntimeError):
    """Raised when no configured Gemini provider can accept a request."""


@dataclass
class GeminiProvider:
    slot: str
    api_key: str
    _client: glm.GenerativeServiceClient | None = None

    @property
    def client(self) -> glm.GenerativeServiceClient:
        if self._client is None:
            self._client = glm.GenerativeServiceClient(client_options={"api_key": self.api_key})
        return self._client


class GeminiProviderPool:
    """Uses primary credentials normally and secondary credentials only on failure."""

    def __init__(
        self,
        primary_key: str,
        secondary_key: str = "",
        retry_base_seconds: float = RETRY_BASE_SECONDS,
    ):
        self.providers = [GeminiProvider("primary", primary_key)] if primary_key else []
        if secondary_key:
            self.providers.append(GeminiProvider("secondary", secondary_key))
        self.retry_base_seconds = retry_base_seconds
        self._cooldowns: dict[str, float] = {}
        self._lock = threading.Lock()

    def _available_providers(self) -> list[GeminiProvider]:
        now = time.monotonic()
        with self._lock:
            return [
                provider
                for provider in self.providers
                if self._cooldowns.get(provider.slot, 0) <= now
            ]

    def _mark_unavailable(self, provider: GeminiProvider, seconds: int) -> None:
        with self._lock:
            self._cooldowns[provider.slot] = time.monotonic() + seconds

    @staticmethod
    def _status_code(exc: Exception) -> int | None:
        code = getattr(exc, "code", None)
        if callable(code):
            code = code()
        try:
            return int(code)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _failure_category(cls, exc: Exception) -> str:
        status_code = cls._status_code(exc)
        if isinstance(exc, google_exceptions.ResourceExhausted) or status_code == 429:
            return "rate_limit"
        if isinstance(exc, (google_exceptions.Unauthenticated, google_exceptions.PermissionDenied)) or status_code in (401, 403):
            return "authentication"
        if isinstance(exc, (google_exceptions.InvalidArgument, google_exceptions.NotFound)) or status_code == 400:
            return "invalid_request"
        if isinstance(
            exc,
            (
                google_exceptions.ServiceUnavailable,
                google_exceptions.DeadlineExceeded,
                google_exceptions.InternalServerError,
            ),
        ) or (status_code is not None and 500 <= status_code < 600):
            return "transient"
        return "unknown"

    @staticmethod
    def _is_daily_quota_error(exc: Exception) -> bool:
        message = str(exc).lower()
        return "daily" in message or "per day" in message or "daily quota" in message

    async def run(
        self,
        operation: str,
        model: str,
        call: Callable[[GeminiProvider], Result],
    ) -> Result:
        providers = self._available_providers()
        if not providers:
            logger.warning(
                "gemini_call operation=%s model=%s provider_slot=none retry_count=0 "
                "fallback_occurred=false failure_category=unavailable",
                operation,
                model,
            )
            raise GeminiProviderUnavailableError("No Gemini provider is currently available.")

        last_error: Exception | None = None
        for provider_index, provider in enumerate(providers):
            fallback_occurred = provider_index > 0
            for retry_count in range(MAX_RETRIES_PER_PROVIDER + 1):
                try:
                    result = await asyncio.to_thread(call, provider)
                    logger.info(
                        "gemini_call operation=%s model=%s provider_slot=%s retry_count=%d "
                        "fallback_occurred=%s failure_category=none",
                        operation,
                        model,
                        provider.slot,
                        retry_count,
                        str(fallback_occurred).lower(),
                    )
                    return result
                except Exception as exc:
                    last_error = exc
                    category = self._failure_category(exc)
                    daily_quota = category == "rate_limit" and self._is_daily_quota_error(exc)
                    can_retry = (
                        category in {"rate_limit", "transient"}
                        and not daily_quota
                        and retry_count < MAX_RETRIES_PER_PROVIDER
                    )
                    logger.warning(
                        "gemini_call operation=%s model=%s provider_slot=%s retry_count=%d "
                        "fallback_occurred=%s failure_category=%s",
                        operation,
                        model,
                        provider.slot,
                        retry_count,
                        str(fallback_occurred).lower(),
                        category,
                    )
                    if can_retry:
                        await asyncio.sleep(self.retry_base_seconds * (2**retry_count))
                        continue

                    if category == "invalid_request" or category == "unknown":
                        raise

                    cooldown = (
                        DAILY_QUOTA_COOLDOWN_SECONDS
                        if daily_quota
                        else AUTH_COOLDOWN_SECONDS
                        if category == "authentication"
                        else RATE_LIMIT_COOLDOWN_SECONDS
                    )
                    self._mark_unavailable(provider, cooldown)
                    break

        raise GeminiProviderUnavailableError("All configured Gemini providers are temporarily unavailable.") from last_error


_provider_pool: GeminiProviderPool | None = None


def get_gemini_provider_pool() -> GeminiProviderPool:
    global _provider_pool
    if _provider_pool is None:
        _provider_pool = GeminiProviderPool(
            primary_key=settings.gemini_api_key,
            secondary_key=settings.gemini_api_key_secondary,
        )
    return _provider_pool
