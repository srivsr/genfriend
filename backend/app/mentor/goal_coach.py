from dataclasses import dataclass
from typing import Optional
from datetime import date
from app.llm import llm_router, TaskType
from app.core.database import async_session
from app.repositories.goal_repository import GoalRepository
from app.repositories.task_repository import TaskRepository


@dataclass
class GoalSchema:
    title: str
    description: str
    why: str
    category: str
    timeframe: str
    start_date: str
    end_date: str
    suggested_key_results: list[dict]


GOAL_COACHING_PROMPT = """You're helping a user set an OKR-style goal connected to their identity.

User's identity: {identity}
User's input about their goal: {input}
Existing goals: {existing_goals}

Guide them through goal-setting:
1. What do you want to achieve? (Objective - clear, inspiring)
2. How does this connect to becoming {ideal_self}?
3. How will you measure success? (Suggest 2-3 Key Results with metrics)
4. What's the timeframe? (quarterly recommended for big goals)

Respond in JSON:
{{
  "title": "...",
  "description": "...",
  "why": "How this serves their identity...",
  "category": "career|health|skill|financial|personal",
  "timeframe": "quarterly|monthly|weekly",
  "suggested_key_results": [
    {{"title": "...", "target_value": X, "unit": "..."}},
    ...
  ],
  "follow_up_question": "..." or null
}}"""

PROGRESS_ANALYSIS_PROMPT = """Analyze this goal's progress with the voice of "future you":

Goal: {goal_title}
Progress: {progress}%
Days remaining: {days_remaining}
Key Results: {key_results}
Recent tasks: {tasks}
User's identity: {identity}

Provide:
1. Honest assessment: on track, at risk, or needs pivot
2. What patterns do you see?
3. What would future-{ideal_self} say about this?
4. One specific action to take today"""


class GoalCoach:
    def __init__(self):
        self.llm = llm_router

    async def create_goal_with_coaching(self, user_id: str, initial_input: str, identity: dict) -> dict:
        existing = await self.get_active_goals(user_id)

        response = await self.llm.generate(
            prompt=GOAL_COACHING_PROMPT.format(
                identity=identity,
                input=initial_input,
                existing_goals=[g.get("title") for g in existing],
                ideal_self=identity.get("ideal_self", "your best self")
            ),
            task_type=TaskType.GENERATION,
            user_id=user_id
        )

        try:
            import json
            return json.loads(response.content)
        except:
            return {
                "title": initial_input,
                "description": initial_input,
                "why": f"Moving toward becoming {identity.get('ideal_self', 'your best self')}",
                "category": "personal",
                "timeframe": "quarterly",
                "suggested_key_results": [],
                "follow_up_question": "How will you measure success on this goal?"
            }

    async def analyze_progress(self, user_id: str, goal_id: str, identity: dict) -> dict:
        goal = await self.get_goal(goal_id)
        if not goal:
            return {"status": "not_found"}

        tasks = await self._get_goal_tasks(goal_id)
        key_results = await self._get_key_results(goal_id)

        end_date = goal.get("end_date")
        if end_date:
            if isinstance(end_date, str):
                from datetime import datetime
                end_date = datetime.fromisoformat(end_date).date()
            days_remaining = (end_date - date.today()).days
        else:
            days_remaining = 0

        response = await self.llm.generate(
            prompt=PROGRESS_ANALYSIS_PROMPT.format(
                goal_title=goal.get("title"),
                progress=goal.get("progress_percent", 0),
                days_remaining=days_remaining,
                key_results=key_results,
                tasks=tasks[:5],
                identity=identity,
                ideal_self=identity.get("ideal_self", "your best self")
            ),
            task_type=TaskType.GENERATION,
            user_id=user_id
        )

        return {"analysis": response.content, "goal": goal, "days_remaining": days_remaining}

    async def get_active_goals(self, user_id: str) -> list:
        async with async_session() as db:
            repo = GoalRepository(db)
            goals = await repo.get_active(user_id)
            return [
                {
                    "id": g.id,
                    "title": g.title,
                    "description": g.description,
                    "why": g.why,
                    "category": g.category,
                    "timeframe": g.timeframe,
                    "progress_percent": g.progress_percent,
                    "start_date": g.start_date.isoformat() if g.start_date else None,
                    "end_date": g.end_date.isoformat() if g.end_date else None,
                    "status": g.status,
                    "woop_wish": g.woop_wish,
                    "woop_outcome": g.woop_outcome,
                    "woop_primary_obstacle": g.woop_primary_obstacle,
                    "future_you_visualization": g.future_you_visualization,
                    "current_streak": g.current_streak or 0,
                }
                for g in goals
            ]

    async def get_goal(self, goal_id: str) -> Optional[dict]:
        async with async_session() as db:
            repo = GoalRepository(db)
            goal = await repo.get_by_id(goal_id)
            if not goal:
                return None
            return {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "why": goal.why,
                "category": goal.category,
                "timeframe": goal.timeframe,
                "progress_percent": goal.progress_percent,
                "start_date": goal.start_date.isoformat() if goal.start_date else None,
                "end_date": goal.end_date.isoformat() if goal.end_date else None,
                "status": goal.status
            }

    async def _get_goal_tasks(self, goal_id: str) -> list:
        async with async_session() as db:
            repo = TaskRepository(db)
            from sqlalchemy import select
            from app.models.task import Task
            result = await db.execute(
                select(Task).where(Task.goal_id == goal_id).limit(10)
            )
            tasks = list(result.scalars().all())
            return [
                {"id": t.id, "title": t.title, "status": t.status}
                for t in tasks
            ]

    async def _get_key_results(self, goal_id: str) -> list:
        async with async_session() as db:
            from sqlalchemy import select
            from app.models.key_result import KeyResult
            result = await db.execute(
                select(KeyResult).where(KeyResult.goal_id == goal_id)
            )
            key_results = list(result.scalars().all())
            return [
                {
                    "id": kr.id,
                    "title": kr.title,
                    "target_value": kr.target_value,
                    "current_value": kr.current_value,
                    "unit": kr.unit,
                    "progress_percent": kr.progress_percent
                }
                for kr in key_results
            ]


goal_coach = GoalCoach()
