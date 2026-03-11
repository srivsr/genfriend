from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey

from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class KeyResult(Base):
    __tablename__ = "key_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    target_value = Column(Numeric(10, 2))
    current_value = Column(Numeric(10, 2), default=0)
    unit = Column(String(50))
    progress_percent = Column(Integer, default=0)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
