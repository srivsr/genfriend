from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class IfThenPlan(Base):
    __tablename__ = "if_then_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Plan Definition
    when_trigger = Column(Text, nullable=False)  # "I feel resistance to starting"
    then_action = Column(Text, nullable=False)  # "commit to just 5 minutes"
    obstacle_type = Column(String(50))  # procrastination, perfectionism, etc.
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Effectiveness Tracking
    times_triggered = Column(Integer, default=0)
    times_used = Column(Integer, default=0)
    times_effective = Column(Integer, default=0)

    @property
    def effectiveness_rate(self) -> float:
        if self.times_triggered == 0:
            return 0.0
        return (self.times_effective / self.times_triggered) * 100


class IfThenLog(Base):
    __tablename__ = "if_then_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    if_then_plan_id = Column(String(36), ForeignKey("if_then_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Log Data
    was_triggered = Column(Boolean, default=True)
    was_used = Column(Boolean, default=False)
    was_effective = Column(Boolean, default=False)
    context = Column(Text)  # What was happening when triggered
    notes = Column(Text)  # User's reflection
