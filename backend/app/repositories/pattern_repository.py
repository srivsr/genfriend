from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.pattern import Pattern
from .base import BaseRepository

class PatternRepository(BaseRepository[Pattern]):
    def __init__(self, db: AsyncSession):
        super().__init__(Pattern, db)

    async def get_active(self, user_id: str) -> List[Pattern]:
        now = datetime.utcnow()
        result = await self.db.execute(
            select(Pattern)
            .where(and_(
                Pattern.user_id == user_id,
                Pattern.was_addressed == False,
                (Pattern.expires_at == None) | (Pattern.expires_at > now)
            ))
            .order_by(Pattern.confidence.desc())
        )
        return list(result.scalars().all())

    async def get_by_type(self, user_id: str, pattern_type: str) -> List[Pattern]:
        result = await self.db.execute(
            select(Pattern)
            .where(and_(Pattern.user_id == user_id, Pattern.pattern_type == pattern_type))
            .order_by(Pattern.detected_at.desc())
        )
        return list(result.scalars().all())

    async def mark_addressed(self, pattern_id: str, user_id: str) -> Optional[Pattern]:
        pattern = await self.get_by_id(pattern_id)
        if pattern and pattern.user_id == user_id:
            pattern.was_addressed = True
            await self.db.commit()
            await self.db.refresh(pattern)
            return pattern
        return None

    async def find_similar(
        self,
        user_id: str,
        pattern_type: str,
        description_keywords: List[str]
    ) -> Optional[Pattern]:
        patterns = await self.get_by_type(user_id, pattern_type)
        for pattern in patterns:
            if any(kw.lower() in pattern.description.lower() for kw in description_keywords):
                return pattern
        return None

    async def upsert_pattern(
        self,
        user_id: str,
        pattern_type: str,
        pattern_name: str,
        description: str,
        evidence: dict,
        confidence: float,
        suggested_action: str = None
    ) -> Pattern:
        existing = await self.find_similar(user_id, pattern_type, pattern_name.split())

        if existing:
            existing.description = description
            existing.evidence = evidence
            existing.confidence = max(existing.confidence, confidence)
            existing.detected_at = datetime.utcnow()
            if suggested_action:
                existing.suggested_action = suggested_action
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            return await self.create(
                user_id=user_id,
                pattern_type=pattern_type,
                description=f"{pattern_name}: {description}",
                evidence=evidence,
                confidence=confidence,
                suggested_action=suggested_action
            )

    async def get_all_patterns_summary(self, user_id: str) -> dict:
        patterns = await self.get_by_user(user_id)

        by_type = {}
        addressed = 0
        active = 0

        for p in patterns:
            by_type[p.pattern_type] = by_type.get(p.pattern_type, 0) + 1
            if p.was_addressed:
                addressed += 1
            else:
                active += 1

        return {
            "total": len(patterns),
            "active": active,
            "addressed": addressed,
            "by_type": by_type
        }
