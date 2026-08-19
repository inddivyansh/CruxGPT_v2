from pydantic import BaseModel, EmailStr, Field


class SuggestionRequest(BaseModel):
    email: EmailStr | None = None
    organization: str | None = Field(default=None, max_length=255)
    contact: str | None = Field(default=None, max_length=255)
    suggestion: str = Field(min_length=1, max_length=5000)
