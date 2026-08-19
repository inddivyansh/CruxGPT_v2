"""
Prompt construction.

Implements the anti-hallucination rules from spec section 19/43: answer only
from retrieved context, say clearly when context is insufficient, distinguish
fact from interpretation, never present interpretation as definitive
professional/legal/medical advice, and return structured JSON so the backend
can validate and shape the response rather than trusting free text.

Note: citations (document/page/section) are attached to the response by our
own code from the retrieved chunks, not invented by the model - the model
only needs to write the answer/decision/conditions/exclusions text.
"""
import json

from models.chunk import DocumentChunk

MAX_CONTEXT_CHARS = 12_000
MAX_HISTORY_CHARS = 6_000
MAX_HISTORY_MESSAGE_CHARS = 1_200

SYSTEM_PROMPT = """You are CRuX GPT, a document analysis assistant for insurance, legal, medical, HR, and compliance documents.

Use only the retrieved context. Do not invent facts, numbers, clauses, or policy terms. If context is insufficient, say so and set "insufficient_context" to true. Clearly label interpretations, do not present insurance/legal/medical interpretations as professional advice, and keep answers concise.

Respond only with one JSON object matching this shape:
{
  "answer": "string",
  "decision": "string or null",
  "conditions": ["string", "..."],
  "exclusions": ["string", "..."],
  "confidence": 0.0,
  "insufficient_context": false
}
"confidence" must be between 0 and 1.
"""

ACTION_HINTS = {
    "evaluate_claim": (
        "The user wants a claim evaluation. Populate 'decision', 'conditions', and 'exclusions' "
        "based on the retrieved policy context if possible."
    ),
    "search_policy": "The user wants specific policy information located and cited.",
    "check_compliance": (
        "The user wants a compliance check. Clearly separate 'the document states X' from your own "
        "interpretation, and do not claim legal certainty."
    ),
    "risk_assessment": "The user wants potential risks identified based on the document context.",
    "general": "Answer the general question about the user's documents.",
}


def select_context_chunks(
    chunks: list[tuple[DocumentChunk, float]], max_chars: int = MAX_CONTEXT_CHARS
) -> list[tuple[DocumentChunk, float]]:
    """Keep the highest-ranked non-duplicate chunks within a prompt budget."""
    selected: list[tuple[DocumentChunk, float]] = []
    seen_text: set[str] = set()
    used_chars = 0

    for chunk, score in chunks:
        normalized_text = " ".join(chunk.text.split())
        if not normalized_text or normalized_text in seen_text:
            continue
        if used_chars + len(chunk.text) > max_chars:
            continue
        selected.append((chunk, score))
        seen_text.add(normalized_text)
        used_chars += len(chunk.text)
    return selected


def format_context(chunks: list[tuple[DocumentChunk, float]], document_names: dict[str, str]) -> str:
    if not chunks:
        return "(No relevant document context was found for this query.)"

    parts = []
    for i, (chunk, score) in enumerate(chunks, start=1):
        doc_name = document_names.get(chunk.document_id, "Unknown document")
        location = []
        if chunk.page_number:
            location.append(f"page {chunk.page_number}")
        if chunk.section:
            location.append(f"section '{chunk.section}'")
        location_str = f" ({', '.join(location)})" if location else ""
        parts.append(f"[Source {i}: {doc_name}{location_str}, relevance={score:.2f}]\n{chunk.text}")
    return "\n\n".join(parts)


def format_history(history: list[dict], max_messages: int = 8) -> str:
    if not history:
        return "(No prior conversation.)"

    lines: list[str] = []
    used_chars = 0
    for message in reversed(history[-max_messages:]):
        content = message["content"].strip()
        if len(content) > MAX_HISTORY_MESSAGE_CHARS:
            content = f"{content[:MAX_HISTORY_MESSAGE_CHARS]}…"
        line = f"{message['role'].upper()}: {content}"
        if used_chars + len(line) > MAX_HISTORY_CHARS:
            break
        lines.append(line)
        used_chars += len(line)
    return "\n".join(reversed(lines)) or "(No prior conversation.)"


def build_user_prompt(query: str, action: str, context: str, history: str) -> str:
    action_hint = ACTION_HINTS.get(action, ACTION_HINTS["general"])
    return f"""Task type: {action}
{action_hint}

Recent conversation:
{history}

Retrieved document context:
{context}

Current user question:
{query}

Respond with the JSON object described in the system instructions, and nothing else."""
