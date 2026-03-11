from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.journal import JournalEntry
from .base import BaseRepository

class JournalRepository(BaseRepository[JournalEntry]):
    def __init__(self, db: AsyncSession):
        super().__init__(JournalEntry, db)

    async def get_by_type(self, user_id: str, entry_type: str, limit: int = 50) -> List[JournalEntry]:
        result = await self.db.execute(
            select(JournalEntry)
            .where(and_(JournalEntry.user_id == user_id, JournalEntry.entry_type == entry_type))
            .order_by(JournalEntry.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_wins(self, user_id: str, limit: int = 20) -> List[JournalEntry]:
        return await self.get_by_type(user_id, "win", limit)

    async def get_moments(self, user_id: str, limit: int = 50) -> List[JournalEntry]:
        return await self.get_by_type(user_id, "moment", limit)

    async def get_recent(self, user_id: str, days: int = 30) -> List[JournalEntry]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(JournalEntry)
            .where(and_(JournalEntry.user_id == user_id, JournalEntry.created_at >= cutoff))
            .order_by(JournalEntry.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_goal(self, user_id: str, goal_id: str) -> List[JournalEntry]:
        result = await self.db.execute(
            select(JournalEntry)
            .where(and_(
                JournalEntry.user_id == user_id,
                JournalEntry.related_goal_id == goal_id
            ))
            .order_by(JournalEntry.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_mood(self, user_id: str, mood: str) -> List[JournalEntry]:
        result = await self.db.execute(
            select(JournalEntry)
            .where(and_(JournalEntry.user_id == user_id, JournalEntry.mood == mood))
            .order_by(JournalEntry.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_favorites(self, user_id: str) -> List[JournalEntry]:
        result = await self.db.execute(
            select(JournalEntry)
            .where(and_(JournalEntry.user_id == user_id, JournalEntry.is_favorite == True))
            .order_by(JournalEntry.created_at.desc())
        )
        return list(result.scalars().all())

    async def search_content(self, user_id: str, query: str, limit: int = 20) -> List[JournalEntry]:
        result = await self.db.execute(
            select(JournalEntry)
            .where(and_(
                JournalEntry.user_id == user_id,
                JournalEntry.content.ilike(f"%{query}%")
            ))
            .order_by(JournalEntry.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_mood_stats(self, user_id: str, days: int = 30) -> dict:
        entries = await self.get_recent(user_id, days)

        mood_counts = {}
        energy_by_mood = {}
        entries_by_day = {}

        for entry in entries:
            if entry.mood:
                mood_counts[entry.mood] = mood_counts.get(entry.mood, 0) + 1
                if entry.energy_level:
                    if entry.mood not in energy_by_mood:
                        energy_by_mood[entry.mood] = []
                    energy_by_mood[entry.mood].append(entry.energy_level)

            day = entry.created_at.strftime("%A")
            if day not in entries_by_day:
                entries_by_day[day] = {"count": 0, "moods": []}
            entries_by_day[day]["count"] += 1
            if entry.mood:
                entries_by_day[day]["moods"].append(entry.mood)

        avg_energy_by_mood = {
            mood: sum(energies) / len(energies)
            for mood, energies in energy_by_mood.items()
            if energies
        }

        return {
            "total_entries": len(entries),
            "mood_distribution": mood_counts,
            "avg_energy_by_mood": avg_energy_by_mood,
            "entries_by_day": entries_by_day
        }
