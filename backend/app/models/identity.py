from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Integer, Float
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Identity(Base):
    __tablename__ = "identities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    ideal_self = Column(String(100), nullable=False)
    description = Column(Text)
    why = Column(Text)
    role_models = Column(JSON)  # Changed from ARRAY to JSON for SQLite compatibility
    target_timeline = Column(String(50))
    attributes = Column(JSON)
    anti_goals = Column(JSON)
    weekly_hours_available = Column(Integer)
    monthly_budget = Column(Float)
    health_limits = Column(Text)
    risk_tolerance = Column(String(10))  # low, medium, high
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
