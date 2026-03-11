from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class EntryResponse(BaseModel):
    id: UUID
    content: str
    entry_type: str
    mood: str | None
    mood_intensity: int | None
    tags: list[str]
    created_at: datetime

    class Config:
        from_attributes = True
