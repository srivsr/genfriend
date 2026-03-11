from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.goal import Goal
from .base import BaseRepository

class GoalRepository(BaseRepository[Goal]):
    def __init__(self, db: AsyncSession):
        super().__init__(Goal, db)

    async def get_active(self, user_id: str) -> List[Goal]:
        result = await self.db.execute(
            select(Goal)
            .where(and_(Goal.user_id == user_id, Goal.status == "active"))
            .order_by(Goal.end_date)
        )
        return list(result.scalars().all())

    async def get_by_status(self, user_id: str, status: str) -> List[Goal]:
        result = await self.db.execute(
            select(Goal)
            .where(and_(Goal.user_id == user_id, Goal.status == status))
            .order_by(Goal.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_category(self, user_id: str, category: str) -> List[Goal]:
        result = await self.db.execute(
            select(Goal)
            .where(and_(Goal.user_id == user_id, Goal.category == category))
            .order_by(Goal.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_identity(self, user_id: str, identity_id: str) -> List[Goal]:
        result = await self.db.execute(
            select(Goal)
            .where(and_(Goal.user_id == user_id, Goal.identity_id == identity_id))
            .order_by(Goal.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_progress(self, goal_id: str, progress: int) -> Optional[Goal]:
        goal = await self.get_by_id(goal_id)
        if goal:
            goal.progress_percent = min(100, max(0, progress))
            if progress >= 100:
                goal.status = "completed"
            await self.db.commit()
            await self.db.refresh(goal)
            return goal
        return None

    async def get_goal_stats(self, user_id: str) -> dict:
        result = await self.db.execute(
            select(Goal).where(Goal.user_id == user_id)
        )
        goals = list(result.scalars().all())

        by_status = {}
        by_category = {}

        for goal in goals:
            by_status[goal.status] = by_status.get(goal.status, 0) + 1
            if goal.category:
                key = goal.category
                if key not in by_category:
                    by_category[key] = {"total": 0, "completed": 0, "abandoned": 0}
                by_category[key]["total"] += 1
                if goal.status == "completed":
                    by_category[key]["completed"] += 1
                elif goal.status == "abandoned":
                    by_category[key]["abandoned"] += 1

        return {
            "total": len(goals),
            "by_status": by_status,
            "by_category": by_category,
            "active": by_status.get("active", 0),
            "completed": by_status.get("completed", 0),
            "abandoned": by_status.get("abandoned", 0)
        }
