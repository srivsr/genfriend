from sqlalchemy import Column, String, Text, Boolean, Numeric, DateTime, JSON

from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Pattern(Base):
    __tablename__ = "patterns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(JSON)
    confidence = Column(Numeric(3, 2))
    suggested_action = Column(Text)
    was_addressed = Column(Boolean, default=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
