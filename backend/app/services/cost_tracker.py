import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from app.config import settings

logger = logging.getLogger(__name__)

PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "llama-guard-3-8b": {"input": 0.2, "output": 0.2},
    "text-embedding-3-small": {"input": 0.02, "output": 0},
}

class CostTracker:
    def __init__(self):
        self._records: list[dict] = []

    async def track(self, user_id: str, model: str, input_tokens: int, output_tokens: int, request_type: str):
        if not settings.enable_cost_tracking:
            return

        pricing = PRICING.get(model, {"input": 0, "output": 0})
        cost = Decimal(str((input_tokens / 1_000_000) * pricing["input"] + (output_tokens / 1_000_000) * pricing["output"]))

        self._records.append({
            "user_id": user_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": float(cost),
            "request_type": request_type,
            "timestamp": datetime.now(timezone.utc),
        })

        logger.info(f"Cost tracked: user={user_id} model={model} tokens={input_tokens}+{output_tokens} cost=${cost:.6f} type={request_type}")

    async def get_user_cost(self, user_id: str, days: int = 30) -> float:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return sum(
            r["cost_usd"] for r in self._records
            if r["user_id"] == user_id and r["timestamp"] >= cutoff
        )
