from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Integer, ForeignKey
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Experience(Base):
    __tablename__ = "experiences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    experience_type = Column(String(50), nullable=False)
    category = Column(String(50))
    skills_demonstrated = Column(JSON)
    evidence = Column(JSON)
    outcome = Column(Text)
    impact_metrics = Column(JSON)
    is_verified = Column(Boolean, default=False)
    verification_method = Column(String(50))
    related_goal_id = Column(String(36), ForeignKey("goals.id"), nullable=True)
    related_task_ids = Column(JSON)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    visibility = Column(String(20), default="private")
    tags = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SkillProgress(Base):
    __tablename__ = "skill_progress"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False)
    skill_category = Column(String(50))
    current_level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)
    total_hours = Column(Integer, default=0)
    evidence_count = Column(Integer, default=0)
    last_practiced = Column(DateTime(timezone=True))
    mastery_percentage = Column(Integer, default=0)
    related_experiences = Column(JSON)
    milestones_achieved = Column(JSON)
    next_milestone = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    achievement_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    criteria = Column(JSON)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    related_experience_id = Column(String(36), ForeignKey("experiences.id"), nullable=True)
    badge_icon = Column(String(50))
    rarity = Column(String(20))
