from pydantic import BaseModel
from uuid import UUID
from datetime import date

class CreateTaskRequest(BaseModel):
    title: str
    description: str | None = None
    goal_id: UUID | None = None
    priority: str = "medium"
    scheduled_date: date | None = None
    scheduled_time_block: str | None = None

class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    scheduled_date: date | None = None
    scheduled_time_block: str | None = None

class CreateGoalRequest(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    target_date: date | None = None

class UpdateGoalRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    status: str | None = None
    target_date: date | None = None
