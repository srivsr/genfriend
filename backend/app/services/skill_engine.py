from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.experience_repository import SkillProgressRepository, ExperienceRepository
from app.repositories.goal_repository import GoalRepository
from app.llm import LLMRouter, TaskType


class SkillLevel(Enum):
    NOVICE = 1
    BEGINNER = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5
    MASTER = 6


@dataclass
class LearningPath:
    skill_name: str
    current_level: int
    target_level: int
    milestones: List[dict]
    recommended_actions: List[str]
    estimated_time: str


@dataclass
class MicroLesson:
    skill: str
    title: str
    content: str
    duration_minutes: int
    action_prompt: str
    xp_reward: int


class UniversalSkillEngine:
    SKILL_CATEGORIES = {
        "technical": ["Python", "JavaScript", "SQL", "API Design", "System Design", "DevOps", "AI/ML", "Data Analysis"],
        "leadership": ["Team Management", "Decision Making", "Delegation", "Mentoring", "Strategic Thinking"],
        "communication": ["Writing", "Presentation", "Negotiation", "Active Listening", "Stakeholder Management"],
        "creative": ["Design Thinking", "Problem Solving", "Innovation", "Ideation", "Storytelling"],
        "professional": ["Time Management", "Project Management", "Critical Thinking", "Adaptability", "Networking"]
    }

    LEVEL_THRESHOLDS = {
        1: 0,      # Novice
        2: 100,    # Beginner
        3: 300,    # Intermediate
        4: 600,    # Advanced
        5: 1000,   # Expert
        6: 1500    # Master
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.skill_repo = SkillProgressRepository(db)
        self.exp_repo = ExperienceRepository(db)
        self.goal_repo = GoalRepository(db)
        self.llm = LLMRouter()

    async def get_skill_profile(self, user_id: str) -> Dict:
        all_skills = await self.skill_repo.get_by_user(user_id)
        top_skills = await self.skill_repo.get_top_skills(user_id, 10)
        summary = await self.skill_repo.get_skill_summary(user_id)

        skills_by_category = {}
        for skill in all_skills:
            cat = skill.skill_category or "general"
            if cat not in skills_by_category:
                skills_by_category[cat] = []
            skills_by_category[cat].append({
                "name": skill.skill_name,
                "level": skill.current_level,
                "level_name": self._level_name(skill.current_level),
                "xp": skill.experience_points,
                "xp_to_next": self._xp_to_next_level(skill.experience_points, skill.current_level),
                "mastery": skill.mastery_percentage,
                "hours": skill.total_hours,
                "evidence_count": skill.evidence_count
            })

        return {
            "summary": summary,
            "by_category": skills_by_category,
            "top_skills": [self._skill_to_dict(s) for s in top_skills],
            "total_xp": sum(s.experience_points for s in all_skills),
            "skill_count": len(all_skills),
            "strengths": await self._identify_strengths(user_id, all_skills),
            "growth_areas": await self._identify_growth_areas(user_id, all_skills)
        }

    async def generate_learning_path(self, user_id: str, target_skill: str, target_level: int = 5) -> LearningPath:
        current = await self.skill_repo.get_by_skill(user_id, target_skill)
        current_level = current.current_level if current else 0
        current_xp = current.experience_points if current else 0

        if current_level >= target_level:
            return LearningPath(
                skill_name=target_skill,
                current_level=current_level,
                target_level=target_level,
                milestones=[],
                recommended_actions=["You've reached your target level! Consider mentoring others."],
                estimated_time="Completed"
            )

        milestones = []
        for level in range(current_level + 1, target_level + 1):
            xp_needed = self.LEVEL_THRESHOLDS[level] - current_xp
            milestones.append({
                "level": level,
                "level_name": self._level_name(level),
                "xp_needed": max(0, xp_needed),
                "suggested_activities": self._activities_for_level(target_skill, level)
            })

        prompt = f"""Create a learning path for developing the skill: {target_skill}
Current level: {self._level_name(current_level)} (Level {current_level})
Target level: {self._level_name(target_level)} (Level {target_level})

Provide 3-5 specific, actionable recommendations.
Focus on practical application, not just theory.
Format as a numbered list."""

        response = await self.llm.route(prompt=prompt, task_type=TaskType.GENERATION)
        recommendations = [line.strip() for line in response.content.split("\n") if line.strip() and line[0].isdigit()]

        total_xp_needed = self.LEVEL_THRESHOLDS[target_level] - current_xp
        estimated_weeks = max(1, total_xp_needed // 50)

        return LearningPath(
            skill_name=target_skill,
            current_level=current_level,
            target_level=target_level,
            milestones=milestones,
            recommended_actions=recommendations[:5],
            estimated_time=f"{estimated_weeks} weeks with regular practice"
        )

    async def get_micro_lesson(self, user_id: str, skill: str = None) -> MicroLesson:
        if not skill:
            skills = await self.skill_repo.get_by_user(user_id)
            if skills:
                sorted_skills = sorted(skills, key=lambda s: s.last_practiced or datetime.min)
                skill = sorted_skills[0].skill_name if sorted_skills else "Time Management"
            else:
                skill = "Time Management"

        current = await self.skill_repo.get_by_skill(user_id, skill)
        level = current.current_level if current else 1

        prompt = f"""Create a 5-minute micro-lesson for: {skill}
Skill level: {self._level_name(level)}

Include:
1. Title (concise, action-oriented)
2. Core concept (2-3 sentences)
3. Quick tip or technique
4. Immediate action prompt (something to do in next 5 minutes)

Keep it practical and immediately actionable."""

        response = await self.llm.route(prompt=prompt, task_type=TaskType.GENERATION)

        lines = response.content.strip().split("\n")
        title = lines[0].replace("Title:", "").replace("1.", "").strip() if lines else f"{skill} Quick Lesson"

        return MicroLesson(
            skill=skill,
            title=title,
            content=response.content,
            duration_minutes=5,
            action_prompt=f"Apply this {skill} technique in your next task",
            xp_reward=10
        )

    async def record_practice(
        self,
        user_id: str,
        skill_name: str,
        activity: str,
        duration_minutes: int = 0,
        evidence: dict = None
    ) -> Dict:
        base_xp = 5
        if duration_minutes >= 30:
            base_xp += 10
        elif duration_minutes >= 15:
            base_xp += 5

        if evidence:
            base_xp += 15

        category = self._categorize_skill(skill_name)

        skill = await self.skill_repo.get_by_skill(user_id, skill_name)
        if not skill:
            await self.skill_repo.create(
                user_id=user_id,
                skill_name=skill_name,
                skill_category=category,
                experience_points=base_xp,
                total_hours=duration_minutes // 60,
                evidence_count=1 if evidence else 0,
                last_practiced=datetime.utcnow()
            )
            skill = await self.skill_repo.get_by_skill(user_id, skill_name)
        else:
            skill = await self.skill_repo.update_progress(
                user_id=user_id,
                skill_name=skill_name,
                xp_gained=base_xp,
                hours_added=duration_minutes // 60
            )

        level_up = False
        if skill:
            new_level = self._calculate_level(skill.experience_points)
            if new_level > (skill.current_level or 1):
                level_up = True
                skill.current_level = new_level
                await self.db.commit()

        return {
            "skill": skill_name,
            "xp_gained": base_xp,
            "total_xp": skill.experience_points if skill else base_xp,
            "current_level": skill.current_level if skill else 1,
            "level_name": self._level_name(skill.current_level if skill else 1),
            "level_up": level_up,
            "xp_to_next": self._xp_to_next_level(skill.experience_points if skill else base_xp, skill.current_level if skill else 1)
        }

    async def get_skill_recommendations(self, user_id: str) -> List[Dict]:
        current_skills = await self.skill_repo.get_by_user(user_id)
        current_skill_names = {s.skill_name.lower() for s in current_skills}

        goals = await self.goal_repo.get_active(user_id)
        goal_text = " ".join([g.title + " " + (g.description or "") for g in goals])

        prompt = f"""Based on these goals and context, suggest 3-5 skills to develop:

Goals: {goal_text[:500] if goal_text else 'General professional growth'}
Current skills: {list(current_skill_names)[:10]}

For each skill, provide:
1. Skill name
2. Why it's relevant
3. Starting point

Format as a list."""

        response = await self.llm.route(prompt=prompt, task_type=TaskType.GENERATION)

        recommendations = []
        for category, skills in self.SKILL_CATEGORIES.items():
            for skill in skills:
                if skill.lower() not in current_skill_names:
                    recommendations.append({
                        "skill": skill,
                        "category": category,
                        "relevance": "Complements your existing skills"
                    })
                    if len(recommendations) >= 5:
                        break
            if len(recommendations) >= 5:
                break

        return recommendations

    async def _identify_strengths(self, user_id: str, skills: list) -> List[str]:
        strong_skills = [s for s in skills if s.mastery_percentage >= 60]
        return [s.skill_name for s in sorted(strong_skills, key=lambda x: x.mastery_percentage, reverse=True)[:3]]

    async def _identify_growth_areas(self, user_id: str, skills: list) -> List[str]:
        goals = await self.goal_repo.get_active(user_id)
        goal_keywords = set()
        for g in goals:
            goal_keywords.update(g.title.lower().split())

        developing_skills = [s for s in skills if s.mastery_percentage < 50]
        relevant = [s for s in developing_skills if any(kw in s.skill_name.lower() for kw in goal_keywords)]

        if relevant:
            return [s.skill_name for s in relevant[:3]]
        return [s.skill_name for s in developing_skills[:3]]

    def _level_name(self, level: int) -> str:
        names = {1: "Novice", 2: "Beginner", 3: "Intermediate", 4: "Advanced", 5: "Expert", 6: "Master"}
        return names.get(level, "Novice")

    def _calculate_level(self, xp: int) -> int:
        for level in range(6, 0, -1):
            if xp >= self.LEVEL_THRESHOLDS[level]:
                return level
        return 1

    def _xp_to_next_level(self, current_xp: int, current_level: int) -> int:
        if current_level >= 6:
            return 0
        next_threshold = self.LEVEL_THRESHOLDS.get(current_level + 1, 1500)
        return max(0, next_threshold - current_xp)

    def _categorize_skill(self, skill_name: str) -> str:
        skill_lower = skill_name.lower()
        for category, skills in self.SKILL_CATEGORIES.items():
            if any(s.lower() in skill_lower or skill_lower in s.lower() for s in skills):
                return category
        return "general"

    def _activities_for_level(self, skill: str, level: int) -> List[str]:
        activities = {
            1: ["Watch introductory content", "Complete basic exercises", "Read beginner guides"],
            2: ["Practice regularly", "Work on small projects", "Join study groups"],
            3: ["Build portfolio projects", "Teach basics to others", "Contribute to open source"],
            4: ["Lead projects", "Mentor beginners", "Create advanced content"],
            5: ["Speak at events", "Write thought leadership", "Innovate new approaches"],
            6: ["Define industry standards", "Build training programs", "Advise organizations"]
        }
        return activities.get(level, activities[1])

    def _skill_to_dict(self, skill) -> Dict:
        return {
            "name": skill.skill_name,
            "category": skill.skill_category,
            "level": skill.current_level,
            "level_name": self._level_name(skill.current_level),
            "xp": skill.experience_points,
            "mastery": skill.mastery_percentage,
            "hours": skill.total_hours,
            "evidence_count": skill.evidence_count,
            "last_practiced": skill.last_practiced.isoformat() if skill.last_practiced else None
        }
