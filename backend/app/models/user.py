from sqlalchemy import Column, String, Boolean, DateTime, Time, Integer
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for Clerk auth users
    name = Column(String(100))
    phone = Column(String(20))
    timezone = Column(String(50), default="Asia/Kolkata")
    onboarding_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Subscription & Billing
    subscription_tier = Column(String(20), default="free")  # free | basic | pro
    subscription_status = Column(String(20), default="active")  # active | cancelled | past_due
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    subscription_started_at = Column(DateTime(timezone=True))
    subscription_ends_at = Column(DateTime(timezone=True))
    monthly_message_count = Column(Integer, default=0)
    message_count_reset_at = Column(DateTime(timezone=True))

    # Coach Personalization (Gen-Friend v2)
    preferred_name = Column(String(100))  # What AI calls user
    coach_name = Column(String(100), default="Gen")  # What user calls AI
    coach_relationship = Column(String(255))  # e.g., "my dog", "my future self"
    coach_tone = Column(String(20), default="warm")  # warm | direct | playful
    quiet_hours_start = Column(Time, default="22:00")
    quiet_hours_end = Column(Time, default="07:00")
    reflection_day = Column(String(10), default="sunday")
    notification_level = Column(String(20), default="balanced")  # off | gentle | balanced | intense
    voice_enabled = Column(Boolean, default=False)
    onboarding_step = Column(String(50))
