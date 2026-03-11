from sqlalchemy import Column, String, Text, DateTime, JSON

from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class AcademyTopic(Base):
    __tablename__ = "academy_topics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(100), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(50))
    difficulty = Column(String(20))
    content = Column(Text, nullable=False)
    examples = Column(JSON)
    prerequisites = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
