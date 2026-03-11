from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, JSON

from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    entry_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    related_goal_id = Column(String(36), ForeignKey("goals.id"))
    related_task_id = Column(String(36), ForeignKey("tasks.id"))
    mood = Column(String(20))
    energy_level = Column(Integer)
    tags = Column(JSON)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
