from pydantic import BaseModel

class CreateEntryRequest(BaseModel):
    content: str
    entry_type: str = "journal"
    mood: str | None = None
    mood_intensity: int | None = None
    tags: list[str] = []

class UpdateEntryRequest(BaseModel):
    content: str | None = None
    entry_type: str | None = None
    mood: str | None = None
    mood_intensity: int | None = None
    tags: list[str] | None = None
