from sqlalchemy import Column, String, Date, Integer, Boolean, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class DailyLeadingIndicator(Base):
    """Track daily leading indicators (what user controls) vs lagging (outcomes).
    Research: U Penn Behavior Change Initiative (2022) - tracking leading indicators
    leads to 3.2x higher habit retention past 90 days.
    """
    __tablename__ = "daily_leading_indicators"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    goal_id = Column(String(36), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Leading Indicators (what you control)
    showed_up = Column(Boolean, default=False)  # Any engagement today?
    task_attempted = Column(Boolean, default=False)  # Started a task?
    if_then_triggered = Column(Boolean, default=False)  # Obstacle showed up?
    if_then_used = Column(Boolean, default=False)  # Used the plan when triggered?
    time_invested_minutes = Column(Integer, default=0)  # Minutes spent on goal
    engagement_quality = Column(Integer)  # 1-5 focus rating

    # Calculated leading score (0-100)
    leading_score = Column(Float, default=0.0)

    # Lagging indicators (outcomes) for the day
    tasks_completed = Column(Integer, default=0)
    minimum_viable_used = Column(Boolean, default=False)  # Used 2-min fallback?

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'goal_id', 'date', name='uq_leading_indicator_user_goal_date'),
    )

    def calculate_leading_score(self) -> float:
        """Calculate leading indicator score (0-100)."""
        score = 0.0
        if self.showed_up:
            score += 25.0
        if self.task_attempted:
            score += 25.0
        if self.if_then_triggered and self.if_then_used:
            score += 25.0
        elif not self.if_then_triggered:
            score += 15.0  # Partial credit if obstacle didn't show up
        if self.time_invested_minutes >= 15:
            score += 25.0
        elif self.time_invested_minutes >= 5:
            score += 15.0
        elif self.time_invested_minutes > 0:
            score += 5.0
        return min(score, 100.0)


class ProgressVelocity(Base):
    """Track weekly velocity and predict goal completion.
    Research: Goal Gradient Effect (Hull 1932, Kivetz 2006) - motivation
    increases as you approach a goal.
    """
    __tablename__ = "progress_velocity"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start = Column(Date, nullable=False, index=True)

    # Weekly metrics
    tasks_completed = Column(Integer, default=0)
    tasks_attempted = Column(Integer, default=0)
    active_days = Column(Integer, default=0)
    time_invested_minutes = Column(Integer, default=0)
    avg_difficulty_rating = Column(Float)
    avg_leading_score = Column(Float)

    # Calculated velocity (vs previous week)
    completion_velocity = Column(Float, default=1.0)  # tasks this week / tasks last week
    engagement_velocity = Column(Float, default=1.0)  # active days this week / last week

    # Prediction
    projected_completion_date = Column(Date)
    days_ahead_behind = Column(Integer, default=0)  # Negative = behind schedule
    confidence = Column(String(20), default="low")  # low, medium, high

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('goal_id', 'week_start', name='uq_velocity_goal_week'),
    )
