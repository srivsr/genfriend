from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.pattern_repository import PatternRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.journal_repository import JournalRepository
from app.repositories.goal_repository import GoalRepository
from app.config import settings


class PatternType(Enum):
    PRODUCTIVITY = "productivity"
    EMOTIONAL = "emotional"
    GOAL_PROGRESS = "goal_progress"
    TIME_MANAGEMENT = "time_management"
    ENERGY = "energy"
    BLOCKER = "blocker"
    STRENGTH = "strength"
    GROWTH = "growth"


@dataclass
class DetectedPattern:
    pattern_type: str
    name: str
    description: str
    evidence: dict
    confidence: float
    suggested_action: str = None


class PatternDetector:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pattern_repo = PatternRepository(db)
        self.task_repo = TaskRepository(db)
        self.journal_repo = JournalRepository(db)
        self.goal_repo = GoalRepository(db)
        from app.llm import LLMRouter
        self.llm = LLMRouter()

    async def detect_all_patterns(self, user_id: str, days: int = 30) -> List[DetectedPattern]:
        patterns = []

        productivity = await self._detect_productivity_patterns(user_id, days)
        patterns.extend(productivity)

        emotional = await self._detect_emotional_patterns(user_id, days)
        patterns.extend(emotional)

        goal = await self._detect_goal_patterns(user_id)
        patterns.extend(goal)

        for pattern in patterns:
            if pattern.confidence >= 0.6:
                await self.pattern_repo.upsert_pattern(
                    user_id=user_id,
                    pattern_type=pattern.pattern_type,
                    pattern_name=pattern.name,
                    description=pattern.description,
                    evidence=pattern.evidence,
                    confidence=pattern.confidence,
                    suggested_action=pattern.suggested_action
                )

        return patterns

    async def _detect_productivity_patterns(self, user_id: str, days: int) -> List[DetectedPattern]:
        patterns = []
        stats = await self.task_repo.get_completion_stats(user_id, days)

        if stats["total"] >= 10:
            completion_rate = stats["completed"] / stats["total"] if stats["total"] > 0 else 0

            if completion_rate >= 0.8:
                patterns.append(DetectedPattern(
                    pattern_type=PatternType.STRENGTH.value,
                    name="High Task Completion",
                    description=f"You complete {int(completion_rate * 100)}% of your tasks. This shows strong follow-through.",
                    evidence={"completion_rate": completion_rate, "total_tasks": stats["total"]},
                    confidence=0.85,
                    suggested_action="Keep up this consistency. Consider taking on more challenging goals."
                ))
            elif completion_rate < 0.4:
                patterns.append(DetectedPattern(
                    pattern_type=PatternType.BLOCKER.value,
                    name="Task Completion Challenge",
                    description=f"Task completion is at {int(completion_rate * 100)}%. Let's identify what's blocking progress.",
                    evidence={"completion_rate": completion_rate, "incomplete": stats["total"] - stats["completed"]},
                    confidence=0.75,
                    suggested_action="Try breaking tasks into smaller steps. Consider if tasks are realistic."
                ))

        if "by_day" in stats and len(stats["by_day"]) >= 7:
            weekday_avg = sum(d["completed"] for d in stats["by_day"] if d["day"] < 5) / max(1, sum(1 for d in stats["by_day"] if d["day"] < 5))
            weekend_avg = sum(d["completed"] for d in stats["by_day"] if d["day"] >= 5) / max(1, sum(1 for d in stats["by_day"] if d["day"] >= 5))

            if weekday_avg > weekend_avg * 2:
                patterns.append(DetectedPattern(
                    pattern_type=PatternType.TIME_MANAGEMENT.value,
                    name="Weekday Focus",
                    description="You're more productive on weekdays, completing twice as many tasks.",
                    evidence={"weekday_avg": weekday_avg, "weekend_avg": weekend_avg},
                    confidence=0.7,
                    suggested_action="Use weekends for rest and planning. Your weekday focus is a strength."
                ))

        return patterns

    async def _detect_emotional_patterns(self, user_id: str, days: int) -> List[DetectedPattern]:
        patterns = []
        mood_stats = await self.journal_repo.get_mood_stats(user_id, days)

        if mood_stats.get("total_entries", 0) >= 5:
            mood_counts = mood_stats.get("mood_distribution", {})
            total = sum(mood_counts.values())

            if total > 0:
                positive_moods = mood_counts.get("happy", 0) + mood_counts.get("excited", 0) + mood_counts.get("grateful", 0)
                negative_moods = mood_counts.get("stressed", 0) + mood_counts.get("anxious", 0) + mood_counts.get("sad", 0)

                if positive_moods / total >= 0.6:
                    patterns.append(DetectedPattern(
                        pattern_type=PatternType.STRENGTH.value,
                        name="Positive Outlook",
                        description="Your journal reflects a predominantly positive mindset.",
                        evidence={"positive_percentage": positive_moods / total * 100},
                        confidence=0.8,
                        suggested_action="Continue practices that maintain your positive outlook."
                    ))
                elif negative_moods / total >= 0.5:
                    patterns.append(DetectedPattern(
                        pattern_type=PatternType.EMOTIONAL.value,
                        name="Stress Pattern",
                        description="You've been experiencing stress frequently. Let's explore what's contributing.",
                        evidence={"negative_percentage": negative_moods / total * 100},
                        confidence=0.75,
                        suggested_action="Consider what's causing stress. Small breaks and wins can help."
                    ))

        return patterns

    async def _detect_goal_patterns(self, user_id: str) -> List[DetectedPattern]:
        patterns = []
        goal_stats = await self.goal_repo.get_goal_stats(user_id)

        active_goals = goal_stats.get("active", 0)
        completed_goals = goal_stats.get("completed", 0)
        total_goals = goal_stats.get("total", 0)

        if total_goals >= 3:
            if completed_goals > 0:
                patterns.append(DetectedPattern(
                    pattern_type=PatternType.GROWTH.value,
                    name="Goal Achiever",
                    description=f"You've completed {completed_goals} goals. This shows real progress.",
                    evidence={"completed": completed_goals, "total": total_goals},
                    confidence=0.85,
                    suggested_action="Celebrate these wins! Each completed goal builds momentum."
                ))

            if active_goals > 5:
                patterns.append(DetectedPattern(
                    pattern_type=PatternType.BLOCKER.value,
                    name="Goal Overload",
                    description=f"You have {active_goals} active goals. Too many can dilute focus.",
                    evidence={"active_goals": active_goals},
                    confidence=0.7,
                    suggested_action="Consider prioritizing 2-3 key goals. Focus drives achievement."
                ))

        avg_progress = goal_stats.get("avg_progress", 0)
        if avg_progress > 0 and active_goals > 0:
            if avg_progress >= 50:
                patterns.append(DetectedPattern(
                    pattern_type=PatternType.GOAL_PROGRESS.value,
                    name="Strong Progress",
                    description=f"Average goal progress is {int(avg_progress)}%. You're on track.",
                    evidence={"avg_progress": avg_progress},
                    confidence=0.8,
                    suggested_action="Keep the momentum. Review what's working and do more of it."
                ))
            elif avg_progress < 20 and total_goals >= 3:
                patterns.append(DetectedPattern(
                    pattern_type=PatternType.BLOCKER.value,
                    name="Slow Progress",
                    description="Goal progress is under 20%. Let's identify blockers.",
                    evidence={"avg_progress": avg_progress},
                    confidence=0.65,
                    suggested_action="Break goals into smaller milestones. Celebrate small wins."
                ))

        return patterns

    async def get_active_patterns(self, user_id: str) -> List[dict]:
        patterns = await self.pattern_repo.get_active(user_id)
        return [
            {
                "id": p.id,
                "type": p.pattern_type,
                "description": p.description,
                "confidence": float(p.confidence),
                "suggested_action": p.suggested_action,
                "detected_at": p.detected_at.isoformat() if p.detected_at else None
            }
            for p in patterns
        ]

    async def address_pattern(self, pattern_id: str, user_id: str) -> bool:
        result = await self.pattern_repo.mark_addressed(pattern_id, user_id)
        return result is not None

    async def get_ai_insights(self, user_id: str) -> str:
        patterns = await self.get_active_patterns(user_id)
        if not patterns:
            return "Keep using Gen-Friend to build up data for personalized insights."

        pattern_summary = "\n".join([
            f"- {p['type']}: {p['description']} (Confidence: {p['confidence']*100:.0f}%)"
            for p in patterns[:5]
        ])

        prompt = f"""Based on these detected patterns about the user, provide brief, actionable insights:

Patterns:
{pattern_summary}

Provide 2-3 specific, encouraging insights. Be warm but actionable.
Focus on strengths first, then growth opportunities."""

        from app.llm import TaskType
        response = await self.llm.generate(
            prompt=prompt,
            task_type=TaskType.GENERATION
        )
        return response.content
