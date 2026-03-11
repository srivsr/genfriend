from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.experience import Experience, SkillProgress, Achievement
from .base import BaseRepository


class ExperienceRepository(BaseRepository[Experience]):
    def __init__(self, db: AsyncSession):
        super().__init__(Experience, db)

    async def get_by_type(self, user_id: str, exp_type: str) -> List[Experience]:
        result = await self.db.execute(
            select(Experience)
            .where(and_(Experience.user_id == user_id, Experience.experience_type == exp_type))
            .order_by(Experience.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_verified(self, user_id: str) -> List[Experience]:
        result = await self.db.execute(
            select(Experience)
            .where(and_(Experience.user_id == user_id, Experience.is_verified == True))
            .order_by(Experience.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_skill(self, user_id: str, skill: str) -> List[Experience]:
        result = await self.db.execute(
            select(Experience)
            .where(Experience.user_id == user_id)
            .order_by(Experience.created_at.desc())
        )
        experiences = list(result.scalars().all())
        return [e for e in experiences if skill.lower() in str(e.skills_demonstrated or []).lower()]

    async def get_by_goal(self, user_id: str, goal_id: str) -> List[Experience]:
        result = await self.db.execute(
            select(Experience)
            .where(and_(Experience.user_id == user_id, Experience.related_goal_id == goal_id))
            .order_by(Experience.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_public(self, user_id: str) -> List[Experience]:
        result = await self.db.execute(
            select(Experience)
            .where(and_(Experience.user_id == user_id, Experience.visibility == "public"))
            .order_by(Experience.created_at.desc())
        )
        return list(result.scalars().all())

    async def verify_experience(self, exp_id: str, method: str) -> Optional[Experience]:
        exp = await self.get_by_id(exp_id)
        if exp:
            exp.is_verified = True
            exp.verification_method = method
            await self.db.commit()
            await self.db.refresh(exp)
        return exp

    async def get_stats(self, user_id: str) -> dict:
        experiences = await self.get_by_user(user_id)
        verified_count = sum(1 for e in experiences if e.is_verified)
        by_type = {}
        all_skills = set()

        for e in experiences:
            by_type[e.experience_type] = by_type.get(e.experience_type, 0) + 1
            if e.skills_demonstrated:
                for skill in e.skills_demonstrated:
                    all_skills.add(skill)

        return {
            "total": len(experiences),
            "verified": verified_count,
            "by_type": by_type,
            "unique_skills": len(all_skills),
            "skill_list": list(all_skills)
        }


class SkillProgressRepository(BaseRepository[SkillProgress]):
    def __init__(self, db: AsyncSession):
        super().__init__(SkillProgress, db)

    async def get_by_skill(self, user_id: str, skill_name: str) -> Optional[SkillProgress]:
        result = await self.db.execute(
            select(SkillProgress)
            .where(and_(
                SkillProgress.user_id == user_id,
                func.lower(SkillProgress.skill_name) == skill_name.lower()
            ))
        )
        return result.scalar_one_or_none()

    async def get_by_category(self, user_id: str, category: str) -> List[SkillProgress]:
        result = await self.db.execute(
            select(SkillProgress)
            .where(and_(SkillProgress.user_id == user_id, SkillProgress.skill_category == category))
            .order_by(SkillProgress.mastery_percentage.desc())
        )
        return list(result.scalars().all())

    async def get_top_skills(self, user_id: str, limit: int = 10) -> List[SkillProgress]:
        result = await self.db.execute(
            select(SkillProgress)
            .where(SkillProgress.user_id == user_id)
            .order_by(SkillProgress.mastery_percentage.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_progress(
        self,
        user_id: str,
        skill_name: str,
        xp_gained: int,
        hours_added: int = 0,
        experience_id: str = None
    ) -> SkillProgress:
        skill = await self.get_by_skill(user_id, skill_name)

        if not skill:
            skill = await self.create(
                user_id=user_id,
                skill_name=skill_name,
                experience_points=xp_gained,
                total_hours=hours_added,
                evidence_count=1 if experience_id else 0,
                last_practiced=datetime.utcnow(),
                related_experiences=[experience_id] if experience_id else []
            )
        else:
            skill.experience_points += xp_gained
            skill.total_hours += hours_added
            skill.last_practiced = datetime.utcnow()
            if experience_id:
                skill.evidence_count += 1
                related = skill.related_experiences or []
                related.append(experience_id)
                skill.related_experiences = related

            skill.current_level = self._calculate_level(skill.experience_points)
            skill.mastery_percentage = self._calculate_mastery(skill)

            await self.db.commit()
            await self.db.refresh(skill)

        return skill

    def _calculate_level(self, xp: int) -> int:
        thresholds = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500]
        for i, threshold in enumerate(thresholds):
            if xp < threshold:
                return i
        return 10

    def _calculate_mastery(self, skill: SkillProgress) -> int:
        level_weight = skill.current_level * 10
        evidence_weight = min(skill.evidence_count * 5, 30)
        hours_weight = min(skill.total_hours, 20)
        return min(level_weight + evidence_weight + hours_weight, 100)

    async def get_skill_summary(self, user_id: str) -> dict:
        skills = await self.get_by_user(user_id)
        if not skills:
            return {"total_skills": 0, "total_xp": 0, "avg_mastery": 0, "top_category": None}

        total_xp = sum(s.experience_points for s in skills)
        avg_mastery = sum(s.mastery_percentage for s in skills) / len(skills)

        categories = {}
        for s in skills:
            cat = s.skill_category or "general"
            categories[cat] = categories.get(cat, 0) + 1

        top_category = max(categories, key=categories.get) if categories else None

        return {
            "total_skills": len(skills),
            "total_xp": total_xp,
            "avg_mastery": round(avg_mastery, 1),
            "top_category": top_category,
            "by_category": categories
        }


class AchievementRepository(BaseRepository[Achievement]):
    def __init__(self, db: AsyncSession):
        super().__init__(Achievement, db)

    async def get_by_type(self, user_id: str, achievement_type: str) -> List[Achievement]:
        result = await self.db.execute(
            select(Achievement)
            .where(and_(Achievement.user_id == user_id, Achievement.achievement_type == achievement_type))
            .order_by(Achievement.earned_at.desc())
        )
        return list(result.scalars().all())

    async def has_achievement(self, user_id: str, title: str) -> bool:
        result = await self.db.execute(
            select(Achievement)
            .where(and_(Achievement.user_id == user_id, Achievement.title == title))
        )
        return result.scalar_one_or_none() is not None

    async def award(
        self,
        user_id: str,
        achievement_type: str,
        title: str,
        description: str,
        experience_id: str = None,
        badge_icon: str = None,
        rarity: str = "common"
    ) -> Optional[Achievement]:
        if await self.has_achievement(user_id, title):
            return None

        return await self.create(
            user_id=user_id,
            achievement_type=achievement_type,
            title=title,
            description=description,
            related_experience_id=experience_id,
            badge_icon=badge_icon,
            rarity=rarity
        )

    async def get_recent(self, user_id: str, limit: int = 10) -> List[Achievement]:
        result = await self.db.execute(
            select(Achievement)
            .where(Achievement.user_id == user_id)
            .order_by(Achievement.earned_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
