from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    hypothesis = Column(Text, nullable=False)
    action = Column(Text)
    result = Column(Text)
    learning = Column(Text)
    tags = Column(JSON)
    status = Column(String(20), default="open")
    closed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
