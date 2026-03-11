from sqlalchemy import Column, String, Text, Date, Time, Integer, DateTime, ForeignKey

from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    goal_id = Column(String(36), ForeignKey("goals.id"), index=True)
    key_result_id = Column(String(36), ForeignKey("key_results.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    scheduled_date = Column(Date, index=True)
    scheduled_time = Column(Time)
    estimated_minutes = Column(Integer)
    status = Column(String(20), default="pending")
    completed_at = Column(DateTime(timezone=True))
    outcome_notes = Column(Text)
    contribution_to_goal = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
