from sqlalchemy import Column, String, Integer, Numeric, DateTime

from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class AICostLog(Base):
    __tablename__ = "ai_cost_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), index=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    estimated_cost = Column(Numeric(10, 6))
    request_type = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
