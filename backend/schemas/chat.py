from typing import Literal

from pydantic import BaseModel, Field

ActionType = Literal["general", "evaluate_claim", "search_policy", "check_compliance", "risk_assessment"]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    action: ActionType = "general"


class SourceItem(BaseModel):
    document_id: str
    document_name: str
    page: int | None = None
    section: str | None = None
    text: str
    relevance_score: float


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    decision: str | None = None
    conditions: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    sources: list[SourceItem] = Field(default_factory=list)
    confidence: float | None = None
    processing_time: float
