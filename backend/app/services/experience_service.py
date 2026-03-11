from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.experience_repository import ExperienceRepository, SkillProgressRepository, AchievementRepository
from app.services.embedding_service import EmbeddingService
from app.llm import LLMRouter, TaskType


@dataclass
class ExperienceInput:
    title: str
    description: str
    experience_type: str
    skills: List[str] = None
    evidence: dict = None
    outcome: str = None
    impact_metrics: dict = None
    related_goal_id: str = None
    visibility: str = "private"


class ExperienceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.exp_repo = ExperienceRepository(db)
        self.skill_repo = SkillProgressRepository(db)
        self.achievement_repo = AchievementRepository(db)
        self.embedding_service = EmbeddingService(db)
        self.llm = LLMRouter()

    async def create_experience(
        self,
        user_id: str,
        input_data: ExperienceInput
    ) -> Dict:
        experience = await self.exp_repo.create(
            user_id=user_id,
            title=input_data.title,
            description=input_data.description,
            experience_type=input_data.experience_type,
            skills_demonstrated=input_data.skills or [],
            evidence=input_data.evidence,
            outcome=input_data.outcome,
            impact_metrics=input_data.impact_metrics,
            related_goal_id=input_data.related_goal_id,
            visibility=input_data.visibility,
            start_date=datetime.utcnow()
        )

        embed_content = f"{input_data.title}. {input_data.description}"
        if input_data.outcome:
            embed_content += f" Outcome: {input_data.outcome}"
        await self.embedding_service.embed_and_store(
            user_id=user_id,
            content=embed_content,
            source_type="experience",
            source_id=experience.id,
            metadata={"type": input_data.experience_type, "skills": input_data.skills}
        )

        if input_data.skills:
            for skill in input_data.skills:
                xp = self._calculate_xp(input_data)
                await self.skill_repo.update_progress(
                    user_id=user_id,
                    skill_name=skill,
                    xp_gained=xp,
                    experience_id=experience.id
                )

        await self._check_achievements(user_id, experience.id, input_data)

        return self._experience_to_dict(experience)

    async def enrich_experience(self, user_id: str, experience_id: str) -> Dict:
        experience = await self.exp_repo.get_by_id(experience_id)
        if not experience or experience.user_id != user_id:
            return None

        prompt = f"""Analyze this experience and extract insights:

Title: {experience.title}
Description: {experience.description}
Outcome: {experience.outcome or 'Not specified'}

Provide:
1. Key skills demonstrated (list 3-5 specific skills)
2. Impact category (technical, leadership, creative, analytical)
3. Suggested improvements for the description to make it more impactful
4. Interview-ready summary (2-3 sentences)

Format as JSON with keys: skills, category, suggestions, summary"""

        response = await self.llm.route(prompt=prompt, task_type=TaskType.ANALYSIS)

        try:
            import json
            enrichment = json.loads(response.content)
        except:
            enrichment = {
                "skills": experience.skills_demonstrated or [],
                "suggestions": "Original description captured well",
                "summary": experience.description[:200]
            }

        if enrichment.get("skills"):
            current_skills = experience.skills_demonstrated or []
            new_skills = list(set(current_skills + enrichment["skills"]))
            await self.exp_repo.update(experience_id, skills_demonstrated=new_skills)

        return enrichment

    async def verify_from_tasks(self, user_id: str, experience_id: str, task_ids: List[str]) -> bool:
        experience = await self.exp_repo.get_by_id(experience_id)
        if not experience or experience.user_id != user_id:
            return False

        from app.repositories.task_repository import TaskRepository
        task_repo = TaskRepository(self.db)

        verified_tasks = []
        for task_id in task_ids:
            task = await task_repo.get_by_id(task_id)
            if task and task.user_id == user_id and task.status == "completed":
                verified_tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                })

        if verified_tasks:
            await self.exp_repo.update(
                experience_id,
                related_task_ids=[t["id"] for t in verified_tasks],
                evidence={"verified_tasks": verified_tasks}
            )
            await self.exp_repo.verify_experience(experience_id, "task_completion")
            return True

        return False

    async def verify_from_goal(self, user_id: str, experience_id: str, goal_id: str) -> bool:
        experience = await self.exp_repo.get_by_id(experience_id)
        if not experience or experience.user_id != user_id:
            return False

        from app.repositories.goal_repository import GoalRepository
        goal_repo = GoalRepository(self.db)

        goal = await goal_repo.get_by_id(goal_id)
        if goal and goal.user_id == user_id and goal.progress_percent >= 80:
            evidence = {
                "goal_id": goal_id,
                "goal_title": goal.title,
                "progress": goal.progress_percent,
                "verified_at": datetime.utcnow().isoformat()
            }
            await self.exp_repo.update(
                experience_id,
                related_goal_id=goal_id,
                evidence=evidence
            )
            await self.exp_repo.verify_experience(experience_id, "goal_achievement")
            return True

        return False

    async def get_portfolio(self, user_id: str, public_only: bool = False) -> Dict:
        if public_only:
            experiences = await self.exp_repo.get_public(user_id)
        else:
            experiences = await self.exp_repo.get_verified(user_id)

        skill_summary = await self.skill_repo.get_skill_summary(user_id)
        top_skills = await self.skill_repo.get_top_skills(user_id, 5)
        achievements = await self.achievement_repo.get_recent(user_id, 10)

        return {
            "experiences": [self._experience_to_dict(e) for e in experiences],
            "skills": {
                "summary": skill_summary,
                "top_skills": [self._skill_to_dict(s) for s in top_skills]
            },
            "achievements": [self._achievement_to_dict(a) for a in achievements],
            "stats": await self.exp_repo.get_stats(user_id)
        }

    async def search_experiences(self, user_id: str, query: str) -> List[Dict]:
        results = await self.embedding_service.search(
            user_id=user_id,
            query=query,
            source_types=["experience"],
            top_k=10
        )

        experience_ids = [r["source_id"] for r in results if r.get("similarity", 0) > 0.3]
        experiences = []
        for exp_id in experience_ids:
            exp = await self.exp_repo.get_by_id(exp_id)
            if exp:
                experiences.append(self._experience_to_dict(exp))

        return experiences

    def _calculate_xp(self, input_data: ExperienceInput) -> int:
        base_xp = 10
        if input_data.evidence:
            base_xp += 15
        if input_data.outcome:
            base_xp += 10
        if input_data.impact_metrics:
            base_xp += 20
        if input_data.experience_type == "project":
            base_xp *= 2
        elif input_data.experience_type == "achievement":
            base_xp *= 1.5
        return int(base_xp)

    async def _check_achievements(
        self,
        user_id: str,
        experience_id: str,
        input_data: ExperienceInput
    ):
        stats = await self.exp_repo.get_stats(user_id)

        if stats["total"] == 1:
            await self.achievement_repo.award(
                user_id=user_id,
                achievement_type="milestone",
                title="First Experience",
                description="Logged your first experience. The journey begins!",
                experience_id=experience_id,
                badge_icon="star",
                rarity="common"
            )

        if stats["total"] == 10:
            await self.achievement_repo.award(
                user_id=user_id,
                achievement_type="milestone",
                title="Experience Builder",
                description="Logged 10 experiences. Building a strong track record!",
                experience_id=experience_id,
                badge_icon="trophy",
                rarity="uncommon"
            )

        if stats["verified"] == 5:
            await self.achievement_repo.award(
                user_id=user_id,
                achievement_type="verification",
                title="Verified Professional",
                description="5 verified experiences. Your credibility is growing!",
                experience_id=experience_id,
                badge_icon="checkmark",
                rarity="rare"
            )

        if stats["unique_skills"] >= 10:
            await self.achievement_repo.award(
                user_id=user_id,
                achievement_type="skill",
                title="Renaissance Mind",
                description="Demonstrated 10+ different skills. True versatility!",
                experience_id=experience_id,
                badge_icon="brain",
                rarity="rare"
            )

    def _experience_to_dict(self, exp) -> Dict:
        return {
            "id": exp.id,
            "title": exp.title,
            "description": exp.description,
            "type": exp.experience_type,
            "category": exp.category,
            "skills": exp.skills_demonstrated or [],
            "evidence": exp.evidence,
            "outcome": exp.outcome,
            "impact_metrics": exp.impact_metrics,
            "is_verified": exp.is_verified,
            "verification_method": exp.verification_method,
            "related_goal_id": exp.related_goal_id,
            "visibility": exp.visibility,
            "created_at": exp.created_at.isoformat() if exp.created_at else None
        }

    def _skill_to_dict(self, skill) -> Dict:
        return {
            "name": skill.skill_name,
            "category": skill.skill_category,
            "level": skill.current_level,
            "xp": skill.experience_points,
            "hours": skill.total_hours,
            "mastery": skill.mastery_percentage,
            "evidence_count": skill.evidence_count
        }

    def _achievement_to_dict(self, achievement) -> Dict:
        return {
            "id": achievement.id,
            "type": achievement.achievement_type,
            "title": achievement.title,
            "description": achievement.description,
            "badge_icon": achievement.badge_icon,
            "rarity": achievement.rarity,
            "earned_at": achievement.earned_at.isoformat() if achievement.earned_at else None
        }
