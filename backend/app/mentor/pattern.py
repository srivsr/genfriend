from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta
from app.llm import llm_router, TaskType
from app.core.database import async_session
from app.repositories.pattern_repository import PatternRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.journal_repository import JournalRepository


class PatternType(Enum):
    RECURRING_FAILURE = "recurring_failure"
    ENERGY_PATTERN = "energy_pattern"
    AVOIDANCE = "avoidance"
    SUCCESS_PATTERN = "success_pattern"


@dataclass
class Pattern:
    pattern_type: PatternType
    description: str
    evidence: list
    confidence: float
    suggested_action: str


PATTERN_DETECTION_PROMPT = """Analyze this user's data for patterns:

Goals (including completed/abandoned): {goals}
Tasks (last 90 days): {tasks}
Journal entries: {journal}

Look for:
1. recurring_failure: Goals/activities tried multiple times but consistently abandoned
2. energy_pattern: Times when most productive vs least
3. avoidance: Tasks/categories consistently skipped or rescheduled
4. success_pattern: What conditions lead to achievement

For each pattern found, provide:
- type: one of the above
- description: Clear, specific description
- evidence: List of specific examples
- confidence: 0.0-1.0
- suggested_action: One specific action to address/leverage

Respond as JSON array of patterns."""


class PatternDetector:
    def __init__(self):
        self.llm = llm_router

    async def detect_patterns(self, user_id: str) -> list[Pattern]:
        goals = await self._get_user_goals(user_id, include_completed=True)
        tasks = await self._get_user_tasks(user_id, days=90)
        journal = await self._get_journal_entries(user_id, days=90)

        if not goals and not tasks:
            return []

        response = await self.llm.generate(
            prompt=PATTERN_DETECTION_PROMPT.format(
                goals=goals[:20],
                tasks=tasks[:50],
                journal=journal[:20]
            ),
            task_type=TaskType.GENERATION,
            user_id=user_id
        )

        try:
            import json
            patterns_data = json.loads(response.content)
            return [Pattern(
                pattern_type=PatternType(p["type"]),
                description=p["description"],
                evidence=p["evidence"],
                confidence=p["confidence"],
                suggested_action=p["suggested_action"]
            ) for p in patterns_data]
        except:
            return []

    async def get_recent_patterns(self, user_id: str) -> list:
        async with async_session() as db:
            repo = PatternRepository(db)
            patterns = await repo.get_active(user_id)
            return [
                {
                    "id": p.id,
                    "type": p.pattern_type,
                    "description": p.description,
                    "evidence": p.evidence,
                    "confidence": float(p.confidence) if p.confidence else 0,
                    "suggested_action": p.suggested_action,
                    "detected_at": p.detected_at.isoformat() if p.detected_at else None
                }
                for p in patterns[:5]
            ]

    async def detect_recurring_failures(self, user_id: str) -> list[Pattern]:
        goals = await self._get_user_goals(user_id, include_completed=True)
        similar_goals = self._find_similar_goals(goals)

        patterns = []
        for goal_group in similar_goals:
            if len(goal_group) >= 3:
                patterns.append(Pattern(
                    pattern_type=PatternType.RECURRING_FAILURE,
                    description=f"You've tried '{goal_group[0].get('title', '')}' {len(goal_group)} times",
                    evidence=[g.get("id") for g in goal_group],
                    confidence=0.8,
                    suggested_action="Let's understand what's different this time"
                ))

        return patterns

    async def detect_avoidance(self, user_id: str) -> list[Pattern]:
        tasks = await self._get_user_tasks(user_id, days=30)
        rescheduled = [t for t in tasks if t.get("rescheduled_count", 0) >= 3]

        patterns = []
        for task in rescheduled[:3]:
            patterns.append(Pattern(
                pattern_type=PatternType.AVOIDANCE,
                description=f"You've rescheduled '{task.get('title', '')}' multiple times",
                evidence=[task.get("id")],
                confidence=0.7,
                suggested_action="What's really blocking you on this?"
            ))

        return patterns

    def _find_similar_goals(self, goals: list) -> list[list]:
        from difflib import SequenceMatcher
        groups = []
        used = set()

        for i, goal in enumerate(goals):
            if i in used:
                continue
            group = [goal]
            for j, other in enumerate(goals[i+1:], i+1):
                if j in used:
                    continue
                title1 = goal.get("title", "").lower()
                title2 = other.get("title", "").lower()
                if SequenceMatcher(None, title1, title2).ratio() > 0.6:
                    group.append(other)
                    used.add(j)
            if len(group) > 1:
                groups.append(group)
            used.add(i)

        return groups

    async def _get_user_goals(self, user_id: str, include_completed: bool = False) -> list:
        async with async_session() as db:
            repo = GoalRepository(db)
            if include_completed:
                goals = await repo.get_by_user(user_id)
            else:
                goals = await repo.get_active(user_id)
            return [
                {
                    "id": g.id,
                    "title": g.title,
                    "status": g.status,
                    "progress_percent": g.progress_percent,
                    "category": g.category
                }
                for g in goals
            ]

    async def _get_user_tasks(self, user_id: str, days: int = 30) -> list:
        async with async_session() as db:
            repo = TaskRepository(db)
            stats = await repo.get_completion_stats(user_id, days)
            tasks = await repo.get_by_user(user_id)
            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None
                }
                for t in tasks[:50]
            ]

    async def _get_journal_entries(self, user_id: str, days: int = 30) -> list:
        async with async_session() as db:
            repo = JournalRepository(db)
            entries = await repo.get_recent(user_id, days)
            return [
                {
                    "id": e.id,
                    "type": e.entry_type,
                    "content": e.content[:200] if e.content else "",
                    "mood": e.mood,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in entries
            ]


pattern_detector = PatternDetector()
