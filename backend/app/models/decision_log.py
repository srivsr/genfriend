from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    goal_id = Column(String(36), ForeignKey("goals.id"), nullable=True)
    decision = Column(Text, nullable=False)
    why = Column(Text)
    expected_outcome = Column(Text)
    review_date = Column(Date)
    actual_outcome = Column(Text)
    tags = Column(JSON)
    status = Column(String(20), default="pending_review")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
