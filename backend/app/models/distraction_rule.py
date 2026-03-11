from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class DistractionRule(Base):
    __tablename__ = "distraction_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    condition = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    rule_type = Column(String(20), default="custom")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
