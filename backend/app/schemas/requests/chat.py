from pydantic import BaseModel
from uuid import UUID

class ChatRequest(BaseModel):
    message: str
    conversation_id: UUID | None = None
