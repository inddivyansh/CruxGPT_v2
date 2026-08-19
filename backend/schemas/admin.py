from pydantic import BaseModel


class AdminStatsResponse(BaseModel):
    overall_accuracy: float | str  # numeric % once there's enough feedback data, else "Not enough evaluation data"
    average_response_time: float
    queries_today: int
    total_users: int
    total_documents: int
    total_conversations: int
    positive_feedback: int
    negative_feedback: int
    system_status: str
    rag_pipeline: str
    maintenance_mode: bool
