from pydantic import BaseModel
from uuid import UUID

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str | None
    timezone: str

    class Config:
        from_attributes = True
