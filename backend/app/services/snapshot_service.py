from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.snapshot_repository import SnapshotRepository, NudgeRepository, CoachingMomentRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.journal_repository import JournalRepository
from app.services.pattern_detector import PatternDetector
from app.llm import LLMRouter, TaskType


class NudgeType(Enum):
    MORNING_CHECKIN = "morning_checkin"
    MIDDAY_CHECKIN = "midday_checkin"
    EVENING_CHECKIN = "evening_checkin"
    GOAL_REMINDER = "goal_reminder"
    TASK_REMINDER = "task_reminder"
    WIN_CELEBRATION = "win_celebration"
    PATTERN_INSIGHT = "pattern_insight"
    STREAK_ALERT = "streak_alert"
    SKILL_PRACTICE = "skill_practice"


@dataclass
class CheckInResponse:
    message: str
    suggestions: List[str]
    context: dict


class DailySnapshotService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.snapshot_repo = SnapshotRepository(db)
        self.task_repo = TaskRepository(db)
        self.goal_repo = GoalRepository(db)
        self.journal_repo = JournalRepository(db)
        self.llm = LLMRouter()

    async def get_or_create_today(self, user_id: str) -> Dict:
        snapshot = await self.snapshot_repo.get_or_create_today(user_id)
        return self._snapshot_to_dict(snapshot)

    async def morning_checkin(
        self,
        user_id: str,
        energy: int,
        focus: str,
        intentions: List[str]
    ) -> CheckInResponse:
        snapshot = await self.snapshot_repo.get_or_create_today(user_id)
        await self.snapshot_repo.update_morning(snapshot.id, energy, focus, intentions)

        goals = await self.goal_repo.get_active(user_id)
        tasks_today = await self.task_repo.get_by_date(user_id, date.today())

        prompt = f"""Generate an encouraging morning coaching message.

User's Energy Level: {energy}/10
Today's Focus: {focus}
Intentions: {intentions}
Active Goals: {len(goals)}
Tasks Scheduled: {len(tasks_today)}

Provide:
1. A warm, brief morning message (2-3 sentences)
2. 2-3 specific suggestions for the day based on their focus

Be encouraging but realistic. Reference their focus area."""

        response = await self.llm.route(prompt=prompt, task_type=TaskType.GENERATION)

        return CheckInResponse(
            message=response.content,
            suggestions=intentions[:3],
            context={
                "energy": energy,
                "focus": focus,
                "goals_count": len(goals),
                "tasks_today": len(tasks_today)
            }
        )

    async def midday_checkin(
        self,
        user_id: str,
        progress: List[str],
        blockers: List[str]
    ) -> CheckInResponse:
        snapshot = await self.snapshot_repo.get_or_create_today(user_id)
        await self.snapshot_repo.update_midday(snapshot.id, progress, blockers)

        morning_focus = snapshot.morning_focus or "your goals"

        prompt = f"""Generate a supportive midday check-in response.

Morning Focus: {morning_focus}
Progress Made: {progress}
Current Blockers: {blockers}

Provide:
1. Acknowledge progress (be specific)
2. Address blockers with practical advice
3. Suggest prioritization for the afternoon

Keep it brief and actionable."""

        response = await self.llm.route(prompt=prompt, task_type=TaskType.GENERATION)

        suggestions = []
        if blockers:
            suggestions.append("Take a 5-minute break to reset")
            suggestions.append("Break the blocker into smaller steps")
        if progress:
            suggestions.append("Build on your morning momentum")

        return CheckInResponse(
            message=response.content,
            suggestions=suggestions,
            context={"progress_count": len(progress), "blocker_count": len(blockers)}
        )

    async def evening_checkin(
        self,
        user_id: str,
        accomplishments: List[str],
        learnings: str,
        gratitude: str
    ) -> CheckInResponse:
        snapshot = await self.snapshot_repo.get_or_create_today(user_id)

        tasks_today = await self.task_repo.get_by_date(user_id, date.today())
        completed = sum(1 for t in tasks_today if t.status == "completed")
        total = len(tasks_today)

        await self.snapshot_repo.update_evening(
            snapshot.id, accomplishments, learnings, gratitude, completed, total
        )

        ai_reflection = await self._generate_daily_reflection(
            user_id, snapshot, accomplishments, completed, total
        )

        snapshot.ai_reflection = ai_reflection
        await self.db.commit()

        return CheckInResponse(
            message=ai_reflection,
            suggestions=["Rest well", "Review tomorrow's priorities", "Celebrate your wins"],
            context={
                "accomplishments": len(accomplishments),
                "tasks_completed": completed,
                "tasks_total": total,
                "completion_rate": (completed / total * 100) if total > 0 else 0
            }
        )

    async def _generate_daily_reflection(
        self,
        user_id: str,
        snapshot,
        accomplishments: List[str],
        completed: int,
        total: int
    ) -> str:
        morning_intentions = snapshot.morning_intentions or []
        morning_focus = snapshot.morning_focus or "your day"

        prompt = f"""Generate a warm, reflective evening summary.

Morning Focus: {morning_focus}
Morning Intentions: {morning_intentions}
Day's Accomplishments: {accomplishments}
Task Completion: {completed}/{total}

Provide:
1. A brief celebration of wins (1-2 sentences)
2. One key insight or learning
3. A gentle prompt for tomorrow

Be warm and encouraging. End on a positive note."""

        response = await self.llm.route(prompt=prompt, task_type=TaskType.GENERATION)
        return response.content

    async def get_weekly_summary(self, user_id: str) -> Dict:
        snapshots = await self.snapshot_repo.get_recent(user_id, 7)

        if not snapshots:
            return {"message": "Start checking in daily to build your weekly summary!"}

        total_tasks = sum(s.tasks_total or 0 for s in snapshots)
        completed_tasks = sum(s.tasks_completed or 0 for s in snapshots)
        avg_energy = sum(s.morning_energy or 5 for s in snapshots) / len(snapshots)

        all_accomplishments = []
        for s in snapshots:
            if s.evening_accomplishments:
                all_accomplishments.extend(s.evening_accomplishments)

        prompt = f"""Generate a weekly reflection summary.

Days Tracked: {len(snapshots)}
Tasks Completed: {completed_tasks}/{total_tasks}
Average Energy: {avg_energy:.1f}/10
Key Accomplishments: {all_accomplishments[:10]}

Provide:
1. Week overview (2-3 sentences)
2. Top 3 wins to celebrate
3. One focus area for next week

Be encouraging and insightful."""

        response = await self.llm.route(prompt=prompt, task_type=TaskType.GENERATION)

        return {
            "days_tracked": len(snapshots),
            "tasks_completed": completed_tasks,
            "tasks_total": total_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "avg_energy": round(avg_energy, 1),
            "streak": await self.snapshot_repo.get_streak(user_id),
            "summary": response.content
        }

    def _snapshot_to_dict(self, snapshot) -> Dict:
        return {
            "id": snapshot.id,
            "date": snapshot.snapshot_date.isoformat() if snapshot.snapshot_date else None,
            "morning": {
                "energy": snapshot.morning_energy,
                "focus": snapshot.morning_focus,
                "intentions": snapshot.morning_intentions
            },
            "midday": {
                "progress": snapshot.midday_progress,
                "blockers": snapshot.midday_blockers
            },
            "evening": {
                "accomplishments": snapshot.evening_accomplishments,
                "learnings": snapshot.evening_learnings,
                "gratitude": snapshot.evening_gratitude,
                "tasks_completed": snapshot.tasks_completed,
                "tasks_total": snapshot.tasks_total
            },
            "ai_reflection": snapshot.ai_reflection
        }


class NudgeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.nudge_repo = NudgeRepository(db)
        self.task_repo = TaskRepository(db)
        self.goal_repo = GoalRepository(db)
        self.pattern_detector = PatternDetector(db)
        self.llm = LLMRouter()

    async def get_pending_nudges(self, user_id: str) -> List[Dict]:
        await self.nudge_repo.cleanup_expired(user_id)
        nudges = await self.nudge_repo.get_pending(user_id)
        return [self._nudge_to_dict(n) for n in nudges]

    async def generate_contextual_nudges(self, user_id: str) -> List[Dict]:
        generated = []

        generated.extend(await self._check_time_based_nudges(user_id))
        generated.extend(await self._check_goal_nudges(user_id))
        generated.extend(await self._check_pattern_nudges(user_id))
        generated.extend(await self._check_streak_nudges(user_id))

        return generated

    async def _check_time_based_nudges(self, user_id: str) -> List[Dict]:
        hour = datetime.now().hour
        nudges = []

        if 6 <= hour <= 9:
            existing = await self.nudge_repo.get_by_type(user_id, NudgeType.MORNING_CHECKIN.value)
            today_nudge = [n for n in existing if n.created_at.date() == date.today()]
            if not today_nudge:
                nudge = await self.nudge_repo.create_nudge(
                    user_id=user_id,
                    nudge_type=NudgeType.MORNING_CHECKIN.value,
                    title="Good Morning!",
                    message="Ready to start your day? Let's set your intentions and energy level.",
                    action_url="/snapshot/morning",
                    action_label="Morning Check-in",
                    priority=3,
                    expires_hours=4
                )
                nudges.append(self._nudge_to_dict(nudge))

        elif 11 <= hour <= 14:
            existing = await self.nudge_repo.get_by_type(user_id, NudgeType.MIDDAY_CHECKIN.value)
            today_nudge = [n for n in existing if n.created_at.date() == date.today()]
            if not today_nudge:
                nudge = await self.nudge_repo.create_nudge(
                    user_id=user_id,
                    nudge_type=NudgeType.MIDDAY_CHECKIN.value,
                    title="Midday Check-in",
                    message="How's your day going? Share your progress and any blockers.",
                    action_url="/snapshot/midday",
                    action_label="Check In",
                    priority=2,
                    expires_hours=4
                )
                nudges.append(self._nudge_to_dict(nudge))

        elif 17 <= hour <= 21:
            existing = await self.nudge_repo.get_by_type(user_id, NudgeType.EVENING_CHECKIN.value)
            today_nudge = [n for n in existing if n.created_at.date() == date.today()]
            if not today_nudge:
                nudge = await self.nudge_repo.create_nudge(
                    user_id=user_id,
                    nudge_type=NudgeType.EVENING_CHECKIN.value,
                    title="End of Day Reflection",
                    message="Time to reflect on your wins and learnings today.",
                    action_url="/snapshot/evening",
                    action_label="Reflect",
                    priority=2,
                    expires_hours=5
                )
                nudges.append(self._nudge_to_dict(nudge))

        return nudges

    async def _check_goal_nudges(self, user_id: str) -> List[Dict]:
        nudges = []
        goals = await self.goal_repo.get_active(user_id)

        for goal in goals:
            if goal.end_date:
                days_left = (goal.end_date - date.today()).days
                if days_left <= 7 and goal.progress_percent < 70:
                    nudge = await self.nudge_repo.create_nudge(
                        user_id=user_id,
                        nudge_type=NudgeType.GOAL_REMINDER.value,
                        title=f"Goal Deadline Approaching",
                        message=f"'{goal.title}' is due in {days_left} days at {goal.progress_percent}%. Let's make progress!",
                        action_url=f"/goals/{goal.id}",
                        action_label="View Goal",
                        priority=3,
                        context={"goal_id": goal.id, "days_left": days_left},
                        expires_hours=24
                    )
                    nudges.append(self._nudge_to_dict(nudge))
                    break

        return nudges

    async def _check_pattern_nudges(self, user_id: str) -> List[Dict]:
        nudges = []
        patterns = await self.pattern_detector.get_active_patterns(user_id)

        high_confidence = [p for p in patterns if p["confidence"] >= 0.7]
        for pattern in high_confidence[:1]:
            nudge = await self.nudge_repo.create_nudge(
                user_id=user_id,
                nudge_type=NudgeType.PATTERN_INSIGHT.value,
                title="Pattern Detected",
                message=pattern["description"][:200],
                action_url="/insights/patterns",
                action_label="View Insights",
                priority=2,
                context={"pattern_id": pattern["id"]},
                expires_hours=48
            )
            nudges.append(self._nudge_to_dict(nudge))

        return nudges

    async def _check_streak_nudges(self, user_id: str) -> List[Dict]:
        nudges = []
        snapshot_repo = SnapshotRepository(self.db)
        streak = await snapshot_repo.get_streak(user_id)

        milestone_streaks = [7, 14, 30, 60, 100]
        if streak in milestone_streaks:
            nudge = await self.nudge_repo.create_nudge(
                user_id=user_id,
                nudge_type=NudgeType.STREAK_ALERT.value,
                title=f"{streak}-Day Streak!",
                message=f"Amazing! You've checked in for {streak} days straight. Keep the momentum going!",
                action_url="/achievements",
                action_label="View Achievements",
                priority=3,
                context={"streak": streak},
                expires_hours=24
            )
            nudges.append(self._nudge_to_dict(nudge))

        return nudges

    async def mark_read(self, nudge_id: str) -> bool:
        nudge = await self.nudge_repo.mark_read(nudge_id)
        return nudge is not None

    async def mark_acted(self, nudge_id: str) -> bool:
        nudge = await self.nudge_repo.mark_acted(nudge_id)
        return nudge is not None

    def _nudge_to_dict(self, nudge) -> Dict:
        return {
            "id": nudge.id,
            "type": nudge.nudge_type,
            "title": nudge.title,
            "message": nudge.message,
            "action_url": nudge.action_url,
            "action_label": nudge.action_label,
            "priority": nudge.priority,
            "is_read": nudge.is_read,
            "expires_at": nudge.expires_at.isoformat() if nudge.expires_at else None,
            "created_at": nudge.created_at.isoformat() if nudge.created_at else None
        }
