from sqlalchemy import Column, String, Text, DateTime, JSON

from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class ScheduledCheckin(Base):
    __tablename__ = "scheduled_checkins"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    checkin_type = Column(String(50), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    message = Column(Text)
    context = Column(JSON)
    status = Column(String(20), default="pending")
    sent_at = Column(DateTime(timezone=True))
    channel = Column(String(20))
    user_response = Column(Text)
    responded_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
