from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    original_filename: str
    mime_type: str
    file_size: int
    status: str
    error_message: str | None
    page_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
