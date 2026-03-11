from sqlalchemy import Column, String, Time, Boolean, DateTime

from sqlalchemy.sql import func
from app.core.database import Base

class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id = Column(String(36), primary_key=True)
    daily_checkin_time = Column(Time, default="09:00")
    preferred_channel = Column(String(20), default="push")
    checkin_frequency = Column(String(20), default="daily")
    mentor_tone = Column(String(20), default="balanced")
    notifications_enabled = Column(Boolean, default=True)
    quiet_hours_start = Column(Time)
    quiet_hours_end = Column(Time)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
