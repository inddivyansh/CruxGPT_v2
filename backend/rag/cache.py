"""
Thread-safe response cache for CruxGPT.

Caches structured generation results scoped by user_id, conversation_id,
normalized query text, and composite document version/content hashes.
Invalidation occurs automatically when documents in the conversation change.
"""
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import threading
import time
from typing import Any


@dataclass
class _CacheEntry:
    value: dict[str, Any]
    expires_at: float


class ResponseCache:
    def __init__(self, max_size: int = 1000, default_ttl_seconds: int = 3600):
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._lock = threading.Lock()

    @staticmethod
    def normalize_query(query: str) -> str:
        return " ".join(query.strip().lower().split())

    @staticmethod
    def compute_cache_key(
        user_id: str,
        conversation_id: str,
        query: str,
        action: str,
        document_snapshots: list[tuple[str, str | None, str]],
    ) -> str:
        """
        Computes a deterministic key scoped to user, conversation, query, action,
        and the exact state of attached documents.
        """
        normalized_q = ResponseCache.normalize_query(query)
        # Sort document snapshots: (doc_id, content_sha256, updated_at)
        sorted_snapshots = sorted(document_snapshots, key=lambda s: s[0])
        doc_signature = ";".join(f"{doc_id}:{sha or 'none'}:{updated}" for doc_id, sha, updated in sorted_snapshots)
        composite = f"u={user_id}|c={conversation_id}|a={action}|q={normalized_q}|docs={doc_signature}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if time.time() > entry.expires_at:
                del self._cache[key]
                return None
            # Move to end for LRU behavior
            self._cache.move_to_end(key)
            return dict(entry.value)

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        expires_at = time.time() + ttl
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = _CacheEntry(value=dict(value), expires_at=expires_at)
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


_response_cache: ResponseCache | None = None


def get_response_cache() -> ResponseCache:
    global _response_cache
    if _response_cache is None:
        from app.config import settings

        _response_cache = ResponseCache(
            max_size=settings.response_cache_max_size,
            default_ttl_seconds=settings.response_cache_ttl_seconds,
        )
    return _response_cache
