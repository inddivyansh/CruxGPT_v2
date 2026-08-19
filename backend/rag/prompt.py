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

SYSTEM_PROMPT = """You are CRuX GPT, an intelligent document analysis assistant for insurance, \
legal, medical, HR, and compliance documents.

Rules you must follow strictly:
1. Answer using ONLY the retrieved document context provided below. Prefer it over general knowledge.
2. Never fabricate or invent facts, numbers, clauses, or policy terms that are not present in the context.
3. If the context does not contain enough information to answer, clearly say so in "answer" and set \
"insufficient_context" to true. Do not guess.
4. Clearly distinguish between what the document explicitly states and any reasonable interpretation you \
are making - if you interpret, say so in the text (e.g. "The document does not say this explicitly, but...").
5. For insurance/legal/medical questions, do not present interpretations as definitive professional advice. \
Where relevant, note that a professional should be consulted for final decisions.
6. Keep the answer concise, structured, and directly useful to the user.
7. Respond with ONLY a single JSON object, no markdown code fences, no preamble, matching exactly this shape:
{
  "answer": "string - the main answer, written for the end user",
  "decision": "string or null - e.g. 'Likely Covered', 'Likely Not Covered', 'Unclear' - only for \
claim-evaluation style questions, otherwise null",
  "conditions": ["string", "..."],
  "exclusions": ["string", "..."],
  "confidence": 0.0,
  "insufficient_context": false
}
"confidence" must be a number between 0 and 1 reflecting how well the retrieved context supports the answer.
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
    trimmed = history[-max_messages:]
    lines = [f"{m['role'].upper()}: {m['content']}" for m in trimmed]
    return "\n".join(lines)


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
