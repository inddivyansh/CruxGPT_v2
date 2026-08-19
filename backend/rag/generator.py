"""
LLM generation via Gemini.

Parses the model's JSON response defensively (models occasionally wrap JSON
in code fences despite instructions not to) and falls back to a safe,
clearly-labeled response rather than crashing or silently fabricating
structure if parsing fails.
"""
from dataclasses import dataclass, field
import json
import re

import google.generativeai as genai

from app.errors import LLMError
from rag.gemini import GeminiProviderPool, GeminiProviderUnavailableError, get_gemini_provider_pool
from rag.prompt import SYSTEM_PROMPT, build_user_prompt


@dataclass
class GenerationResult:
    answer: str
    summary: str | None = None
    key_points: list[str] = field(default_factory=list)
    decision: str | None = None
    conditions: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)
    confidence: float | None = None
    insufficient_context: bool = False


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _extract_json(raw_text: str) -> dict:
    text = raw_text.strip()
    fence_match = _JSON_FENCE_RE.search(text)
    if fence_match:
        text = fence_match.group(1).strip()
    return json.loads(text)


class GeminiGenerator:
    def __init__(self, provider_pool: GeminiProviderPool | None = None):
        from app.config import settings

        self.model_name = settings.gemini_llm_model
        self.provider_pool = provider_pool or get_gemini_provider_pool()

    async def generate(self, query: str, action: str, context: str, history: str) -> GenerationResult:
        user_prompt = build_user_prompt(query=query, action=action, context=context, history=history)

        try:
            def generate(provider):
                model = genai.GenerativeModel(model_name=self.model_name, system_instruction=SYSTEM_PROMPT)
                model._client = provider.client
                return model.generate_content(
                    user_prompt,
                    generation_config={"response_mime_type": "application/json", "temperature": 0.2},
                )

            response = await self.provider_pool.run(
                operation="chat",
                model=self.model_name,
                call=generate,
            )
            raw_text = response.text
        except GeminiProviderUnavailableError as exc:
            raise LLMError("Gemini is temporarily unavailable. Please try again.") from exc
        except Exception as exc:
            raise LLMError(f"Gemini generation call failed: {exc}") from exc

        try:
            parsed = _extract_json(raw_text)
        except (json.JSONDecodeError, TypeError):
            # Model didn't return clean JSON - still surface something useful
            # rather than failing the whole request outright.
            return GenerationResult(
                answer=raw_text.strip() or "I wasn't able to generate a response. Please try again.",
                summary=None,
                key_points=[],
                insufficient_context=False,
                confidence=None,
            )

        confidence = parsed.get("confidence")
        try:
            confidence = float(confidence) if confidence is not None else None
        except (TypeError, ValueError):
            confidence = None

        summary = parsed.get("summary")
        if isinstance(summary, str):
            summary = summary.strip() or None
        else:
            summary = None

        raw_key_points = parsed.get("key_points")
        key_points = [str(kp).strip() for kp in raw_key_points if str(kp).strip()] if isinstance(raw_key_points, list) else []

        return GenerationResult(
            answer=parsed.get("answer", "").strip() or "No answer was generated.",
            summary=summary,
            key_points=key_points,
            decision=parsed.get("decision"),
            conditions=list(parsed.get("conditions") or []),
            exclusions=list(parsed.get("exclusions") or []),
            confidence=confidence,
            insufficient_context=bool(parsed.get("insufficient_context", False)),
        )


_generator: GeminiGenerator | None = None


def get_generator() -> GeminiGenerator:
    global _generator
    if _generator is None:
        _generator = GeminiGenerator()
    return _generator
