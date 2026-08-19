from datetime import datetime

from pydantic import BaseModel

from schemas.chat import SourceItem


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: list[SourceItem] = []
    action: str | None = None
    confidence: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []


class ConversationCreateRequest(BaseModel):
    title: str | None = None
