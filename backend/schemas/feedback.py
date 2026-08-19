from typing import Literal

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    feedback: Literal["positive", "negative"]
    reason: str | None = Field(default=None, max_length=500)
