from sqlalchemy import Column, String, Text, Integer, DateTime

from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class MoodLog(Base):
    __tablename__ = "mood_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    mood = Column(String(50), nullable=False)
    intensity = Column(Integer)
    notes = Column(Text)
    source = Column(String(50), default="detected")
    logged_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
