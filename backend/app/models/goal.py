from sqlalchemy import Column, String, Text, Date, Integer, DateTime, ForeignKey, JSON, Float
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Goal(Base):
    __tablename__ = "goals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    identity_id = Column(String(36), ForeignKey("identities.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    why = Column(Text)
    category = Column(String(50))
    timeframe = Column(String(20), nullable=False, default="quarterly")  # 1_month, 3_months, 6_months, 1_year
    goal_type = Column(String(20), default="performance")  # performance | learning
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default="active")  # active, paused, completed, abandoned
    progress_percent = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Endowed Progress (Research: Nunes & Drèze 2006 - start at 20% not 0%)
    initial_progress_percent = Column(Float, default=20.0)

    # Multi-dimensional Progress Scores (0-100 each)
    effort_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    completion_score = Column(Float, default=0.0)
    momentum_score = Column(Float, default=0.0)
    composite_progress_score = Column(Float, default=20.0)  # Weighted combination

    # Velocity & Trends
    current_velocity = Column(Float, default=1.0)  # >1 accelerating, <1 slowing
    velocity_trend = Column(String(20), default="steady")  # accelerating, steady, slowing
    predicted_completion_date = Column(Date)

    # Future You (Identity Connection)
    future_you_time_horizon = Column(String(20))  # How far ahead they visualized
    future_you_visualization = Column(Text)  # User's vision of future self
    future_you_identity_statement = Column(Text)  # "I am someone who..."

    # WOOP Framework (Oettingen)
    woop_wish = Column(Text)  # The core wish/goal
    woop_outcome = Column(Text)  # Visualization of success (sensory details)
    woop_primary_obstacle = Column(String(50))  # procrastination, perfectionism, fear_of_failure, etc.
    woop_custom_obstacle = Column(Text)  # If primary_obstacle is 'custom'

    # Locke-Latham Validation Scores (1-5 each)
    ll_clarity_score = Column(Integer)  # Specific and measurable
    ll_challenge_score = Column(Integer)  # Stretching but achievable (70-90% confidence)
    ll_commitment_score = Column(Integer)  # Emotional investment
    ll_feedback_score = Column(Integer)  # Progress indicators defined
    ll_complexity_score = Column(Integer)  # Right-sized for timeframe

    @property
    def ll_total_score(self) -> int:
        scores = [self.ll_clarity_score, self.ll_challenge_score, self.ll_commitment_score,
                  self.ll_feedback_score, self.ll_complexity_score]
        return sum(s for s in scores if s is not None)

    # Execution System (JSON)
    execution_system = Column(JSON)  # Daily system, triggers, milestones, adaptation rules

    # Streak Tracking (Enhanced with Resilience - Anti-fragile streaks)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_tasks_completed = Column(Integer, default=0)
    total_tasks_created = Column(Integer, default=0)

    # Streak Resilience (Research: Total days > consecutive days for motivation)
    total_active_days = Column(Integer, default=0)  # All-time days with activity
    freeze_days_available = Column(Integer, default=0)  # Earned protection days
    freeze_days_used = Column(Integer, default=0)
    streak_recovery_count = Column(Integer, default=0)  # Times bounced back after miss
    last_recovery_date = Column(Date)

    # Completion
    completed_at = Column(DateTime(timezone=True))
    completion_reflection = Column(Text)
    completion_proud_of = Column(Text)
    completion_learned = Column(Text)
    completion_next_goal = Column(Text)

    # Pause State
    paused_at = Column(DateTime(timezone=True))
    paused_reason = Column(String(50))  # health, work, priorities, recharge, other
    expected_resume_date = Column(Date)
    pause_duration_days = Column(Integer)
    streak_at_pause = Column(Integer)

    # Archive State
    archived_at = Column(DateTime(timezone=True))
    archive_reason = Column(String(50))  # abandoned, not_relevant, duplicate, replaced, other
    archive_learning = Column(Text)
