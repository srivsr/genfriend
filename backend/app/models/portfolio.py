from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, unique=True, index=True)
    display_name = Column(String(255))
    headline = Column(String(500))
    bio = Column(Text)
    avatar_url = Column(String(500))
    is_public = Column(Boolean, default=False)
    public_slug = Column(String(100), unique=True)
    theme = Column(String(50), default="professional")
    featured_experiences = Column(JSON)
    featured_skills = Column(JSON)
    contact_preferences = Column(JSON)
    social_links = Column(JSON)
    interview_enabled = Column(Boolean, default=False)
    interview_intro = Column(Text)
    interview_topics = Column(JSON)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String(36), nullable=False, index=True)
    interviewer_name = Column(String(255))
    interviewer_company = Column(String(255))
    interviewer_email = Column(String(255))
    session_type = Column(String(50))
    questions_asked = Column(JSON)
    topics_discussed = Column(JSON)
    duration_seconds = Column(DateTime)
    rating = Column(String(10))
    feedback = Column(Text)
    is_completed = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))


class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    sources_used = Column(JSON)
    confidence = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
