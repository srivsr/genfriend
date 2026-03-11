from datetime import datetime, date
from typing import Optional
from .messages import MessageGenerator
from .channels.whatsapp import WhatsAppChannel
from .channels.push import PushChannel

class CheckinTrigger:
    def __init__(self):
        self.message_generator = MessageGenerator()
        self.whatsapp = WhatsAppChannel()
        self.push = PushChannel()

    async def daily_plan_checkin(self, user_id: str):
        prefs = await self._get_preferences(user_id)
        identity = await self._get_identity(user_id)
        pending_tasks = await self._get_pending_tasks(user_id)
        top_goal = await self._get_top_goal(user_id)

        message = await self.message_generator.daily_checkin(
            user_id=user_id,
            identity=identity,
            pending_tasks=pending_tasks,
            top_goal=top_goal
        )

        await self._send_message(user_id, message, prefs.get("preferred_channel", "push"))
        await self._log_checkin(user_id, "daily_plan", message)

        await self.decision_review_checkin(user_id)

    async def decision_review_checkin(self, user_id: str):
        from app.core.database import async_session
        from app.repositories.strategic_brain_repository import DecisionLogRepository

        async with async_session() as db:
            repo = DecisionLogRepository(db)
            pending = await repo.get_pending_reviews(user_id)

        if not pending:
            return

        identity = await self._get_identity(user_id)
        prefs = await self._get_preferences(user_id)

        for decision in pending:
            message = await self.message_generator.decision_review(
                user_id=user_id,
                identity=identity,
                decision={
                    "decision": decision.decision,
                    "why": decision.why,
                    "expected_outcome": decision.expected_outcome,
                    "created_at": str(decision.created_at),
                    "review_date": str(decision.review_date),
                }
            )
            await self._send_message(user_id, message, prefs.get("preferred_channel", "push"))
            await self._log_checkin(user_id, "decision_review", message, {"decision_id": decision.id})

    async def goal_at_risk_checkin(self, user_id: str, goal: dict):
        identity = await self._get_identity(user_id)
        analysis = await self._analyze_goal(user_id, goal.get("id"))

        message = await self.message_generator.goal_at_risk(
            user_id=user_id,
            identity=identity,
            goal=goal,
            analysis=analysis
        )

        await self._send_message(user_id, message, "whatsapp")
        await self._log_checkin(user_id, "goal_at_risk", message, {"goal_id": goal.get("id")})

    async def pattern_alert_checkin(self, user_id: str, pattern: dict):
        identity = await self._get_identity(user_id)

        message = await self.message_generator.pattern_alert(
            user_id=user_id,
            identity=identity,
            pattern=pattern
        )

        await self._send_message(user_id, message, "whatsapp")
        await self._log_checkin(user_id, "pattern_alert", message, {"pattern": pattern})

    async def encouragement_checkin(self, user_id: str, context: str = None):
        identity = await self._get_identity(user_id)
        wins = await self._get_recent_wins(user_id)

        message = await self.message_generator.encouragement(
            user_id=user_id,
            identity=identity,
            wins=wins,
            context=context
        )

        await self._send_message(user_id, message, "push")
        await self._log_checkin(user_id, "encouragement", message)

    async def trigger_checkin(self, user_id: str, checkin_type: str, context: dict = None):
        match checkin_type:
            case "daily_plan":
                await self.daily_plan_checkin(user_id)
            case "goal_at_risk":
                await self.goal_at_risk_checkin(user_id, context.get("goal", {}))
            case "pattern_alert":
                await self.pattern_alert_checkin(user_id, context.get("pattern", {}))
            case "encouragement":
                await self.encouragement_checkin(user_id, context.get("context"))
            case "decision_review":
                await self.decision_review_checkin(user_id)

    async def _send_message(self, user_id: str, message: str, channel: str):
        user = await self._get_user(user_id)
        if channel == "whatsapp" and user.get("phone"):
            await self.whatsapp.send_message(user.get("phone"), message)
        else:
            await self.push.send_notification(user_id, "Gen-Friend", message)

    async def _log_checkin(self, user_id: str, checkin_type: str, message: str, context: dict = None):
        pass

    async def _get_preferences(self, user_id: str) -> dict:
        return {"preferred_channel": "push", "daily_checkin_time": "09:00"}

    async def _get_identity(self, user_id: str) -> dict:
        return {}

    async def _get_pending_tasks(self, user_id: str) -> list:
        return []

    async def _get_top_goal(self, user_id: str) -> Optional[dict]:
        return None

    async def _get_user(self, user_id: str) -> dict:
        return {}

    async def _analyze_goal(self, user_id: str, goal_id: str) -> dict:
        return {}

    async def _get_recent_wins(self, user_id: str) -> list:
        return []

checkin_trigger = CheckinTrigger()
