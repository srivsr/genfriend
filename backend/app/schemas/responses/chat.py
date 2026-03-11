from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    intent: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    message: MessageResponse
    conversation_id: UUID
