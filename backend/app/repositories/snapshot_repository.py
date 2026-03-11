from typing import List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.snapshot import DailySnapshot, Nudge, CoachingMoment
from .base import BaseRepository


class SnapshotRepository(BaseRepository[DailySnapshot]):
    def __init__(self, db: AsyncSession):
        super().__init__(DailySnapshot, db)

    async def get_for_date(self, user_id: str, target_date: date) -> Optional[DailySnapshot]:
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        result = await self.db.execute(
            select(DailySnapshot)
            .where(and_(
                DailySnapshot.user_id == user_id,
                DailySnapshot.snapshot_date >= start,
                DailySnapshot.snapshot_date <= end
            ))
        )
        return result.scalar_one_or_none()

    async def get_recent(self, user_id: str, days: int = 7) -> List[DailySnapshot]:
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(DailySnapshot)
            .where(and_(DailySnapshot.user_id == user_id, DailySnapshot.snapshot_date >= since))
            .order_by(DailySnapshot.snapshot_date.desc())
        )
        return list(result.scalars().all())

    async def get_or_create_today(self, user_id: str) -> DailySnapshot:
        today = date.today()
        existing = await self.get_for_date(user_id, today)
        if existing:
            return existing
        return await self.create(
            user_id=user_id,
            snapshot_date=datetime.combine(today, datetime.min.time())
        )

    async def update_morning(
        self,
        snapshot_id: str,
        energy: int,
        focus: str,
        intentions: List[str]
    ) -> DailySnapshot:
        snapshot = await self.get_by_id(snapshot_id)
        if snapshot:
            snapshot.morning_energy = energy
            snapshot.morning_focus = focus
            snapshot.morning_intentions = intentions
            await self.db.commit()
            await self.db.refresh(snapshot)
        return snapshot

    async def update_midday(
        self,
        snapshot_id: str,
        progress: List[str],
        blockers: List[str]
    ) -> DailySnapshot:
        snapshot = await self.get_by_id(snapshot_id)
        if snapshot:
            snapshot.midday_progress = progress
            snapshot.midday_blockers = blockers
            await self.db.commit()
            await self.db.refresh(snapshot)
        return snapshot

    async def update_evening(
        self,
        snapshot_id: str,
        accomplishments: List[str],
        learnings: str,
        gratitude: str,
        tasks_completed: int,
        tasks_total: int
    ) -> DailySnapshot:
        snapshot = await self.get_by_id(snapshot_id)
        if snapshot:
            snapshot.evening_accomplishments = accomplishments
            snapshot.evening_learnings = learnings
            snapshot.evening_gratitude = gratitude
            snapshot.tasks_completed = tasks_completed
            snapshot.tasks_total = tasks_total
            await self.db.commit()
            await self.db.refresh(snapshot)
        return snapshot

    async def get_streak(self, user_id: str) -> int:
        snapshots = await self.get_recent(user_id, 30)
        if not snapshots:
            return 0

        streak = 0
        current_date = date.today()
        for snapshot in sorted(snapshots, key=lambda s: s.snapshot_date, reverse=True):
            snap_date = snapshot.snapshot_date.date() if hasattr(snapshot.snapshot_date, 'date') else snapshot.snapshot_date
            if snap_date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        return streak


class NudgeRepository(BaseRepository[Nudge]):
    def __init__(self, db: AsyncSession):
        super().__init__(Nudge, db)

    async def get_pending(self, user_id: str) -> List[Nudge]:
        now = datetime.utcnow()
        result = await self.db.execute(
            select(Nudge)
            .where(and_(
                Nudge.user_id == user_id,
                Nudge.is_read == False,
                (Nudge.expires_at == None) | (Nudge.expires_at > now),
                (Nudge.scheduled_for == None) | (Nudge.scheduled_for <= now)
            ))
            .order_by(Nudge.priority.desc(), Nudge.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_type(self, user_id: str, nudge_type: str) -> List[Nudge]:
        result = await self.db.execute(
            select(Nudge)
            .where(and_(Nudge.user_id == user_id, Nudge.nudge_type == nudge_type))
            .order_by(Nudge.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_read(self, nudge_id: str) -> Optional[Nudge]:
        nudge = await self.get_by_id(nudge_id)
        if nudge:
            nudge.is_read = True
            await self.db.commit()
        return nudge

    async def mark_acted(self, nudge_id: str) -> Optional[Nudge]:
        nudge = await self.get_by_id(nudge_id)
        if nudge:
            nudge.is_acted = True
            nudge.is_read = True
            await self.db.commit()
        return nudge

    async def create_nudge(
        self,
        user_id: str,
        nudge_type: str,
        title: str,
        message: str,
        action_url: str = None,
        action_label: str = None,
        priority: int = 1,
        context: dict = None,
        expires_hours: int = None,
        schedule_for: datetime = None
    ) -> Nudge:
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours) if expires_hours else None
        return await self.create(
            user_id=user_id,
            nudge_type=nudge_type,
            title=title,
            message=message,
            action_url=action_url,
            action_label=action_label,
            priority=priority,
            context=context,
            expires_at=expires_at,
            scheduled_for=schedule_for,
            delivered_at=datetime.utcnow() if not schedule_for else None
        )

    async def cleanup_expired(self, user_id: str) -> int:
        from sqlalchemy import delete
        now = datetime.utcnow()
        result = await self.db.execute(
            delete(Nudge)
            .where(and_(Nudge.user_id == user_id, Nudge.expires_at < now))
        )
        await self.db.commit()
        return result.rowcount


class CoachingMomentRepository(BaseRepository[CoachingMoment]):
    def __init__(self, db: AsyncSession):
        super().__init__(CoachingMoment, db)

    async def get_recent(self, user_id: str, limit: int = 10) -> List[CoachingMoment]:
        result = await self.db.execute(
            select(CoachingMoment)
            .where(CoachingMoment.user_id == user_id)
            .order_by(CoachingMoment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_type(self, user_id: str, moment_type: str) -> List[CoachingMoment]:
        result = await self.db.execute(
            select(CoachingMoment)
            .where(and_(CoachingMoment.user_id == user_id, CoachingMoment.moment_type == moment_type))
            .order_by(CoachingMoment.created_at.desc())
        )
        return list(result.scalars().all())

    async def record_feedback(self, moment_id: str, was_helpful: bool, response: str = None) -> Optional[CoachingMoment]:
        moment = await self.get_by_id(moment_id)
        if moment:
            moment.was_helpful = was_helpful
            moment.user_response = response
            await self.db.commit()
        return moment

    async def get_effectiveness_stats(self, user_id: str) -> dict:
        moments = await self.get_by_user(user_id)
        if not moments:
            return {"total": 0, "helpful": 0, "rate": 0}

        total = len(moments)
        helpful = sum(1 for m in moments if m.was_helpful)
        return {
            "total": total,
            "helpful": helpful,
            "rate": (helpful / total * 100) if total > 0 else 0
        }
