from typing import List, Optional
from datetime import date, datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from .base import BaseRepository

class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: AsyncSession):
        super().__init__(Task, db)

    async def get_by_date(self, user_id: str, target_date: date) -> List[Task]:
        result = await self.db.execute(
            select(Task)
            .where(and_(Task.user_id == user_id, Task.scheduled_date == target_date))
            .order_by(Task.scheduled_time)
        )
        return list(result.scalars().all())

    async def get_by_goal(self, user_id: str, goal_id: str) -> List[Task]:
        result = await self.db.execute(
            select(Task)
            .where(and_(Task.user_id == user_id, Task.goal_id == goal_id))
            .order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_status(self, user_id: str, status: str) -> List[Task]:
        result = await self.db.execute(
            select(Task)
            .where(and_(Task.user_id == user_id, Task.status == status))
            .order_by(Task.scheduled_date)
        )
        return list(result.scalars().all())

    async def get_pending_for_date_range(
        self, user_id: str, start_date: date, end_date: date
    ) -> List[Task]:
        result = await self.db.execute(
            select(Task)
            .where(and_(
                Task.user_id == user_id,
                Task.scheduled_date >= start_date,
                Task.scheduled_date <= end_date,
                Task.status == "pending"
            ))
            .order_by(Task.scheduled_date, Task.scheduled_time)
        )
        return list(result.scalars().all())

    async def mark_complete(
        self, task_id: str, user_id: str, outcome_notes: Optional[str] = None
    ) -> Optional[Task]:
        task = await self.get_by_id(task_id)
        if task and task.user_id == user_id:
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            if outcome_notes:
                task.outcome_notes = outcome_notes
            await self.db.commit()
            await self.db.refresh(task)
            return task
        return None

    async def get_completion_stats(self, user_id: str, days: int = 30) -> dict:
        from datetime import timedelta
        cutoff = date.today() - timedelta(days=days)

        result = await self.db.execute(
            select(Task)
            .where(and_(
                Task.user_id == user_id,
                Task.scheduled_date >= cutoff
            ))
        )
        tasks = list(result.scalars().all())

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == "completed")

        by_time = {"morning": 0, "afternoon": 0, "evening": 0}
        completed_by_time = {"morning": 0, "afternoon": 0, "evening": 0}

        for task in tasks:
            if task.scheduled_time:
                hour = task.scheduled_time.hour
                if 5 <= hour < 12:
                    period = "morning"
                elif 12 <= hour < 17:
                    period = "afternoon"
                else:
                    period = "evening"
                by_time[period] += 1
                if task.status == "completed":
                    completed_by_time[period] += 1

        return {
            "total": total,
            "completed": completed,
            "completion_rate": completed / total if total > 0 else 0,
            "by_time_of_day": by_time,
            "completed_by_time": completed_by_time
        }
