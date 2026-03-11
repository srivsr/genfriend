from sqlalchemy import Column, String, Text, Date, DateTime, JSON

from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class WeeklySummary(Base):
    __tablename__ = "weekly_summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    week_start = Column(Date, nullable=False)
    summary = Column(Text, nullable=False)
    insights = Column(JSON)
    stats = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
