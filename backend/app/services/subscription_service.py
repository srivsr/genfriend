from typing import Optional
from dataclasses import dataclass
from enum import Enum

class SubscriptionTier(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"

@dataclass
class TierConfig:
    name: str
    price_monthly: float
    price_yearly: float
    llm_model: str
    max_messages_per_month: int
    features: list[str]

TIER_CONFIGS: dict[SubscriptionTier, TierConfig] = {
    SubscriptionTier.FREE: TierConfig(
        name="Free Trial",
        price_monthly=0,
        price_yearly=0,
        llm_model="gpt-4o-mini",
        max_messages_per_month=50,
        features=[
            "Basic AI coaching",
            "Daily planning (limited)",
            "GPT-4o-mini responses",
        ]
    ),
    SubscriptionTier.BASIC: TierConfig(
        name="Basic",
        price_monthly=5,
        price_yearly=50,
        llm_model="gpt-4o-mini",
        max_messages_per_month=500,
        features=[
            "Daily AI-powered planning",
            "Career coaching chat",
            "Skill development tips",
            "Basic task tracking",
            "GPT-4o-mini responses",
            "Email support",
        ]
    ),
    SubscriptionTier.PRO: TierConfig(
        name="Pro",
        price_monthly=12,
        price_yearly=120,
        llm_model="gpt-4o",
        max_messages_per_month=2000,
        features=[
            "Everything in Basic",
            "Advanced GPT-4o responses",
            "Priority response times",
            "Deep career analysis",
            "Weekly progress reports",
            "Voice chat support",
            "Custom goal frameworks",
            "Priority support",
        ]
    ),
}

def get_tier_config(tier: str) -> TierConfig:
    try:
        return TIER_CONFIGS[SubscriptionTier(tier)]
    except (ValueError, KeyError):
        return TIER_CONFIGS[SubscriptionTier.FREE]

def get_llm_model_for_tier(tier: str) -> str:
    config = get_tier_config(tier)
    return config.llm_model

def get_message_limit_for_tier(tier: str) -> int:
    config = get_tier_config(tier)
    return config.max_messages_per_month

def can_send_message(tier: str, current_count: int) -> bool:
    limit = get_message_limit_for_tier(tier)
    return current_count < limit

def get_tier_features(tier: str) -> list[str]:
    config = get_tier_config(tier)
    return config.features

class SubscriptionService:
    @staticmethod
    def get_model_for_user(user) -> str:
        tier = user.subscription_tier or "free"
        if user.subscription_status != "active" and tier != "free":
            return get_llm_model_for_tier("free")
        return get_llm_model_for_tier(tier)

    @staticmethod
    def check_message_quota(user) -> tuple[bool, int, int]:
        tier = user.subscription_tier or "free"
        limit = get_message_limit_for_tier(tier)
        current = user.monthly_message_count or 0
        can_send = current < limit
        return can_send, current, limit

    @staticmethod
    def increment_message_count(user) -> int:
        user.monthly_message_count = (user.monthly_message_count or 0) + 1
        return user.monthly_message_count

    @staticmethod
    def get_upgrade_prompt(tier: str) -> Optional[str]:
        if tier == "free":
            return "Upgrade to Basic ($5/mo) for unlimited coaching with GPT-4o-mini"
        elif tier == "basic":
            return "Upgrade to Pro ($12/mo) for advanced GPT-4o responses"
        return None
