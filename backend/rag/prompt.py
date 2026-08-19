"""
Prompt construction.

Implements the anti-hallucination rules from spec section 19/43: answer only
from retrieved context, say clearly when context is insufficient, distinguish
fact from interpretation, never present interpretation as definitive
professional/legal/medical advice, and return structured JSON so the backend
can validate and shape the response rather than trusting free text.
"""
from dataclasses import dataclass
import re

from models.chunk import DocumentChunk

MAX_CONTEXT_CHARS = 12_000
MAX_HISTORY_CHARS = 6_000
MAX_HISTORY_MESSAGE_CHARS = 1_200


@dataclass(frozen=True)
class ContextChunk:
    """Prompt-only chunk view; never mutates the stored SQLAlchemy chunk."""

    document_id: str
    text: str
    page_number: int | None
    section: str | None


SYSTEM_PROMPT = """You are CRuX GPT, a document analysis assistant for insurance, legal, medical, HR, and compliance documents.

Use ONLY the retrieved document context. Do NOT use outside knowledge, invent facts, numbers, clauses, or policy terms. If the context does not contain enough information to answer reliably, set "insufficient_context" to true, clearly state in "answer" that the document context is insufficient, and set "key_points" to [].

Rules:
1. Give a direct answer to the user's question first in "answer".
2. Provide a 1-2 sentence executive summary in "summary".
3. Use "key_points" for important supporting details or bullet points from the text.
4. For claim/policy evaluation, populate "decision", "conditions", and "exclusions" if relevant.
5. "confidence" must be a float between 0.0 and 1.0.
6. Return ONLY valid JSON matching this schema, without any markdown formatting or commentary outside the JSON object:

{
  "answer": "Direct answer to the question.",
  "summary": "Short 1-2 sentence summary.",
  "key_points": [
    "Important supporting detail 1",
    "Important supporting detail 2"
  ],
  "decision": "string or null",
  "conditions": ["string", "..."],
  "exclusions": ["string", "..."],
  "confidence": 0.9,
  "insufficient_context": false
}
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


def _word_tokens(text: str) -> set[str]:
    """Extract lowercase words of length >= 3 for textual redundancy checking."""
    return {w.lower() for w in re.findall(r"\b\w{3,}\b", text)}


def _is_redundant(candidate_tokens: set[str], selected_tokens_list: list[set[str]], threshold: float = 0.75) -> bool:
    """Check if candidate text has high token overlap with any already selected chunk."""
    if not candidate_tokens:
        return False
    for existing in selected_tokens_list:
        if not existing:
            continue
        intersection = len(candidate_tokens & existing)
        overlap = intersection / min(len(candidate_tokens), len(existing))
        if overlap >= threshold:
            return True
    return False


def select_context_chunks(
    chunks: list[tuple[DocumentChunk, float]],
    document_names: dict[str, str],
    max_chars: int = MAX_CONTEXT_CHARS,
    redundancy_threshold: float = 0.75,
) -> list[tuple[ContextChunk, float]]:
    """
    Select diverse, high-ranked unique chunks within the exact rendered context budget,
    filtering out exact duplicates and near-redundant chunks.
    """
    selected: list[tuple[ContextChunk, float]] = []
    seen_text: set[str] = set()
    selected_tokens_list: list[set[str]] = []
    used_chars = 0

    for chunk, score in chunks:
        normalized_text = " ".join(chunk.text.split())
        if not normalized_text or normalized_text in seen_text:
            continue

        candidate_tokens = _word_tokens(chunk.text)
        if selected_tokens_list and _is_redundant(candidate_tokens, selected_tokens_list, threshold=redundancy_threshold):
            continue

        doc_name = document_names.get(chunk.document_id, "Unknown document")
        header = _source_header(chunk, score, doc_name)
        separator_chars = 2 if selected else 0
        remaining_text_chars = max_chars - used_chars - separator_chars - len(header) - 1
        if remaining_text_chars <= 0:
            break

        prompt_text = chunk.text
        if len(prompt_text) > remaining_text_chars:
            # Keep a readable prefix while leaving the persisted chunk untouched.
            cutoff = prompt_text.rfind(" ", 0, remaining_text_chars - 1)
            cutoff = cutoff if cutoff > 0 else remaining_text_chars - 1
            prompt_text = f"{prompt_text[:cutoff].rstrip()}…"

        context_chunk = ContextChunk(
            document_id=chunk.document_id,
            text=prompt_text,
            page_number=chunk.page_number,
            section=chunk.section,
        )
        selected.append((context_chunk, score))
        seen_text.add(normalized_text)
        selected_tokens_list.append(candidate_tokens)
        used_chars += separator_chars + len(header) + 1 + len(prompt_text)

    return selected


def _source_header(chunk: ContextChunk | DocumentChunk, score: float, doc_name: str) -> str:
    location = []
    if chunk.page_number:
        location.append(f"page {chunk.page_number}")
    if chunk.section:
        location.append(f"section '{chunk.section}'")
    location_str = f" ({', '.join(location)})" if location else ""
    return f"[Source: {doc_name}{location_str}, relevance={score:.2f}]"


def format_context(chunks: list[tuple[ContextChunk, float]], document_names: dict[str, str]) -> str:
    if not chunks:
        return "(No relevant document context was found for this query.)"

    parts = []
    for chunk, score in chunks:
        doc_name = document_names.get(chunk.document_id, "Unknown document")
        parts.append(f"{_source_header(chunk, score, doc_name)}\n{chunk.text}")
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
