from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Boolean
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class DailySnapshot(Base):
    __tablename__ = "daily_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    snapshot_date = Column(DateTime(timezone=True), nullable=False, index=True)
    morning_energy = Column(Integer)
    morning_focus = Column(String(255))
    morning_intentions = Column(JSON)
    midday_progress = Column(JSON)
    midday_blockers = Column(JSON)
    evening_accomplishments = Column(JSON)
    evening_learnings = Column(Text)
    evening_gratitude = Column(Text)
    mood_trend = Column(JSON)
    tasks_completed = Column(Integer, default=0)
    tasks_total = Column(Integer, default=0)
    goals_progress = Column(JSON)
    ai_reflection = Column(Text)
    coach_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Nudge(Base):
    __tablename__ = "nudges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    nudge_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(255))
    action_label = Column(String(100))
    priority = Column(Integer, default=1)
    context = Column(JSON)
    is_read = Column(Boolean, default=False)
    is_acted = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))
    scheduled_for = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CoachingMoment(Base):
    __tablename__ = "coaching_moments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    moment_type = Column(String(50), nullable=False)
    trigger = Column(String(100))
    context = Column(JSON)
    coach_message = Column(Text, nullable=False)
    user_response = Column(Text)
    was_helpful = Column(Boolean)
    follow_up_scheduled = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
