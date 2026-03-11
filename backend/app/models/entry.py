from sqlalchemy import Column, String, Text, Integer, DateTime, JSON

from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Entry(Base):
    __tablename__ = "entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    content = Column(Text, nullable=False)
    entry_type = Column(String(50), default="journal")
    mood = Column(String(50))
    mood_intensity = Column(Integer)
    tags = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
