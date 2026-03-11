from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
from .base import BaseAgent, AgentContext, AgentResponse
from app.llm import TaskType
from app.services.pattern_detector import PatternDetector
from app.core.database import async_session
from app.repositories.task_repository import TaskRepository
from app.repositories.journal_repository import JournalRepository
from app.repositories.goal_repository import GoalRepository


class InsightType(Enum):
    PRODUCTIVITY = "productivity"
    EMOTIONAL_TREND = "emotional_trend"
    GOAL_PROGRESS = "goal_progress"
    BLOCKERS = "blockers"
    WEEKLY_SUMMARY = "weekly_summary"
    PATTERNS = "patterns"


@dataclass
class InsightData:
    summary: str
    metrics: dict = None
    chart_data: dict = None
    patterns: list = None


class InsightAgent(BaseAgent):
    name = "insight"
    description = "Finds patterns and generates insights from user data"

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        return await self.analyze(context.user_id, message)

    async def analyze(self, user_id: str, query: str) -> AgentResponse:
        insight_type = self._classify_insight_request(query)
        data = await self._gather_data(user_id, insight_type)

        prompt = f"""Analyze this user's data and provide meaningful insights.

Query: {query}

Data Summary:
{data.summary}

Metrics: {data.metrics or 'N/A'}
Patterns Detected: {len(data.patterns) if data.patterns else 0}

Provide 2-3 specific, actionable insights:
1. Start with a strength or positive observation
2. Identify one growth opportunity
3. Suggest a concrete next step

Be encouraging but honest. Reference specific data when possible."""

        response = await self._generate(prompt, task_type=TaskType.GENERATION)
        return AgentResponse(
            content=response,
            data={
                "type": insight_type.value,
                "metrics": data.metrics,
                "visualization": data.chart_data,
                "patterns": data.patterns
            }
        )

    def _classify_insight_request(self, query: str) -> InsightType:
        lower = query.lower()
        if any(w in lower for w in ["productive", "focus", "work", "accomplish", "tasks"]):
            return InsightType.PRODUCTIVITY
        elif any(w in lower for w in ["feel", "mood", "emotion", "happy", "sad", "stress"]):
            return InsightType.EMOTIONAL_TREND
        elif any(w in lower for w in ["goal", "progress", "achieve", "milestone"]):
            return InsightType.GOAL_PROGRESS
        elif any(w in lower for w in ["block", "stuck", "problem", "obstacle", "challenge"]):
            return InsightType.BLOCKERS
        elif any(w in lower for w in ["week", "summary", "review"]):
            return InsightType.WEEKLY_SUMMARY
        elif any(w in lower for w in ["pattern", "trend", "habit"]):
            return InsightType.PATTERNS
        return InsightType.PRODUCTIVITY

    async def _gather_data(self, user_id: str, insight_type: InsightType) -> InsightData:
        async with async_session() as db:
            if insight_type == InsightType.PRODUCTIVITY:
                return await self._gather_productivity_data(user_id, db)
            elif insight_type == InsightType.EMOTIONAL_TREND:
                return await self._gather_emotional_data(user_id, db)
            elif insight_type == InsightType.GOAL_PROGRESS:
                return await self._gather_goal_data(user_id, db)
            elif insight_type == InsightType.BLOCKERS:
                return await self._gather_blocker_data(user_id, db)
            elif insight_type == InsightType.WEEKLY_SUMMARY:
                return await self._gather_weekly_data(user_id, db)
            elif insight_type == InsightType.PATTERNS:
                return await self._gather_pattern_data(user_id, db)
            else:
                return InsightData(summary="No specific data type matched.")

    async def _gather_productivity_data(self, user_id: str, db) -> InsightData:
        task_repo = TaskRepository(db)
        stats = await task_repo.get_completion_stats(user_id, 30)

        total = stats.get("total", 0)
        completed = stats.get("completed", 0)
        rate = (completed / total * 100) if total > 0 else 0

        summary = f"""Productivity Overview (Last 30 Days):
- Total tasks: {total}
- Completed: {completed}
- Completion rate: {rate:.1f}%
- Pending: {stats.get('pending', 0)}"""

        metrics = {
            "total_tasks": total,
            "completed_tasks": completed,
            "completion_rate": rate,
            "pending_tasks": stats.get("pending", 0)
        }

        chart_data = {
            "type": "progress",
            "value": rate,
            "label": "Task Completion Rate"
        }

        detector = PatternDetector(db)
        patterns = await detector.get_active_patterns(user_id)
        productivity_patterns = [p for p in patterns if p["type"] in ["productivity", "time_management", "strength"]]

        return InsightData(
            summary=summary,
            metrics=metrics,
            chart_data=chart_data,
            patterns=productivity_patterns[:3]
        )

    async def _gather_emotional_data(self, user_id: str, db) -> InsightData:
        journal_repo = JournalRepository(db)
        mood_stats = await journal_repo.get_mood_stats(user_id, 30)

        total_entries = mood_stats.get("total_entries", 0)
        mood_dist = mood_stats.get("mood_distribution", {})

        summary = f"""Emotional Overview (Last 30 Days):
- Journal entries: {total_entries}
- Mood distribution: {mood_dist}
- Most common mood: {max(mood_dist, key=mood_dist.get) if mood_dist else 'N/A'}"""

        chart_data = {
            "type": "pie",
            "data": mood_dist,
            "label": "Mood Distribution"
        }

        detector = PatternDetector(db)
        patterns = await detector.get_active_patterns(user_id)
        emotional_patterns = [p for p in patterns if p["type"] in ["emotional", "strength"]]

        return InsightData(
            summary=summary,
            metrics={"entries": total_entries, "moods": mood_dist},
            chart_data=chart_data,
            patterns=emotional_patterns[:3]
        )

    async def _gather_goal_data(self, user_id: str, db) -> InsightData:
        goal_repo = GoalRepository(db)
        stats = await goal_repo.get_goal_stats(user_id)

        active = stats.get("active", 0)
        completed = stats.get("completed", 0)
        avg_progress = stats.get("avg_progress", 0)

        summary = f"""Goal Overview:
- Active goals: {active}
- Completed goals: {completed}
- Average progress: {avg_progress:.1f}%
- By category: {stats.get('by_category', {})}"""

        chart_data = {
            "type": "bar",
            "data": {"active": active, "completed": completed},
            "label": "Goals Status"
        }

        detector = PatternDetector(db)
        patterns = await detector.get_active_patterns(user_id)
        goal_patterns = [p for p in patterns if p["type"] in ["goal_progress", "growth", "blocker"]]

        return InsightData(
            summary=summary,
            metrics=stats,
            chart_data=chart_data,
            patterns=goal_patterns[:3]
        )

    async def _gather_blocker_data(self, user_id: str, db) -> InsightData:
        detector = PatternDetector(db)
        patterns = await detector.get_active_patterns(user_id)
        blockers = [p for p in patterns if p["type"] == "blocker"]

        if blockers:
            blocker_list = "\n".join([f"- {b['description']}" for b in blockers])
            summary = f"""Identified Blockers:
{blocker_list}

Each blocker has suggested actions to help you move forward."""
        else:
            summary = "No major blockers detected. You're making steady progress."

        return InsightData(
            summary=summary,
            metrics={"blocker_count": len(blockers)},
            patterns=blockers
        )

    async def _gather_weekly_data(self, user_id: str, db) -> InsightData:
        task_repo = TaskRepository(db)
        journal_repo = JournalRepository(db)
        goal_repo = GoalRepository(db)

        task_stats = await task_repo.get_completion_stats(user_id, 7)
        mood_stats = await journal_repo.get_mood_stats(user_id, 7)
        goal_stats = await goal_repo.get_goal_stats(user_id)

        summary = f"""Weekly Summary:

Tasks:
- Completed: {task_stats.get('completed', 0)} / {task_stats.get('total', 0)}
- Completion rate: {(task_stats.get('completed', 0) / max(1, task_stats.get('total', 1)) * 100):.0f}%

Journal:
- Entries this week: {mood_stats.get('total_entries', 0)}
- Dominant mood: {max(mood_stats.get('mood_distribution', {'neutral': 1}), key=mood_stats.get('mood_distribution', {'neutral': 1}).get)}

Goals:
- Active: {goal_stats.get('active', 0)}
- Average progress: {goal_stats.get('avg_progress', 0):.0f}%"""

        detector = PatternDetector(db)
        patterns = await detector.get_active_patterns(user_id)

        return InsightData(
            summary=summary,
            metrics={
                "tasks": task_stats,
                "moods": mood_stats,
                "goals": goal_stats
            },
            patterns=patterns[:5]
        )

    async def _gather_pattern_data(self, user_id: str, db) -> InsightData:
        detector = PatternDetector(db)
        await detector.detect_all_patterns(user_id, 30)
        patterns = await detector.get_active_patterns(user_id)

        if patterns:
            pattern_list = "\n".join([
                f"- [{p['type'].upper()}] {p['description']} ({p['confidence']*100:.0f}% confidence)"
                for p in patterns
            ])
            summary = f"""Detected Patterns:
{pattern_list}"""
        else:
            summary = "Continue using Gen-Friend to build up data for pattern detection."

        return InsightData(
            summary=summary,
            metrics={"pattern_count": len(patterns)},
            patterns=patterns
        )

    async def get_quick_insights(self, user_id: str) -> Dict:
        async with async_session() as db:
            detector = PatternDetector(db)
            patterns = await detector.get_active_patterns(user_id)

            strengths = [p for p in patterns if p["type"] in ["strength", "growth"]]
            blockers = [p for p in patterns if p["type"] == "blocker"]

            return {
                "strengths": strengths[:3],
                "blockers": blockers[:2],
                "pattern_count": len(patterns),
                "ai_summary": await detector.get_ai_insights(user_id) if patterns else None
            }


insight_agent = InsightAgent()
