from pydantic import BaseModel
from typing import TypeVar, Generic, Any

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str = "Success"

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    detail: Any | None = None
