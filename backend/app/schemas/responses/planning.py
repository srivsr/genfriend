from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime

class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    goal_id: UUID | None
    priority: str
    status: str
    scheduled_date: date | None
    scheduled_time_block: str | None
    completed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True

class GoalResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    category: str | None
    status: str
    target_date: date | None
    created_at: datetime

    class Config:
        from_attributes = True

class DailyPlanResponse(BaseModel):
    date: date
    tasks: list[TaskResponse]
    mood: str | None = None
    summary: str | None = None
