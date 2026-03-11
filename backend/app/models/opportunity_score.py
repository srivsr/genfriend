from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class OpportunityScore(Base):
    __tablename__ = "opportunity_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    goal_id = Column(String(36), ForeignKey("goals.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    revenue_potential = Column(Integer, default=0)
    strategic_fit = Column(Integer, default=0)
    effort_complexity = Column(Integer, default=0)
    skill_match = Column(Integer, default=0)
    time_to_first_win = Column(Integer, default=0)
    risk_regret_cost = Column(Integer, default=0)
    total_score = Column(Float, default=0.0)
    reasoning = Column(JSON)
    anti_goal_conflicts = Column(JSON)
    status = Column(String(20), default="evaluated")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
