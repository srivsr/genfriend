from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from app.schemas.responses import APIResponse
from app.dependencies import get_current_user_id
from app.core.database import get_db
from app.services.skill_engine import UniversalSkillEngine

router = APIRouter(prefix="/skills", tags=["skills"])


class RecordPracticeRequest(BaseModel):
    skill_name: str
    activity: str
    duration_minutes: int = 0
    evidence: Optional[dict] = None


class GeneratePathRequest(BaseModel):
    target_skill: str
    target_level: int = 5


@router.get("/profile")
async def get_skill_profile(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    engine = UniversalSkillEngine(db)
    profile = await engine.get_skill_profile(str(user_id))
    return APIResponse(data=profile)


@router.get("/top")
async def get_top_skills(
    limit: int = 10,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    engine = UniversalSkillEngine(db)
    skills = await engine.skill_repo.get_top_skills(str(user_id), limit)
    return APIResponse(data=[engine._skill_to_dict(s) for s in skills])


@router.get("/by-category/{category}")
async def get_skills_by_category(
    category: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    engine = UniversalSkillEngine(db)
    skills = await engine.skill_repo.get_by_category(str(user_id), category)
    return APIResponse(data=[engine._skill_to_dict(s) for s in skills])


@router.post("/learning-path")
async def generate_learning_path(
    request: GeneratePathRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    engine = UniversalSkillEngine(db)
    path = await engine.generate_learning_path(str(user_id), request.target_skill, request.target_level)

    return APIResponse(data={
        "skill": path.skill_name,
        "current_level": path.current_level,
        "target_level": path.target_level,
        "milestones": path.milestones,
        "recommendations": path.recommended_actions,
        "estimated_time": path.estimated_time
    })


@router.get("/micro-lesson")
async def get_micro_lesson(
    skill: Optional[str] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    engine = UniversalSkillEngine(db)
    lesson = await engine.get_micro_lesson(str(user_id), skill)

    return APIResponse(data={
        "skill": lesson.skill,
        "title": lesson.title,
        "content": lesson.content,
        "duration_minutes": lesson.duration_minutes,
        "action_prompt": lesson.action_prompt,
        "xp_reward": lesson.xp_reward
    })


@router.post("/practice")
async def record_practice(
    request: RecordPracticeRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    engine = UniversalSkillEngine(db)
    result = await engine.record_practice(
        str(user_id),
        request.skill_name,
        request.activity,
        request.duration_minutes,
        request.evidence
    )

    message = "Practice recorded!"
    if result.get("level_up"):
        message = f"Level up! You're now {result['level_name']} in {result['skill']}"

    return APIResponse(data=result, message=message)


@router.get("/recommendations")
async def get_skill_recommendations(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    engine = UniversalSkillEngine(db)
    recommendations = await engine.get_skill_recommendations(str(user_id))
    return APIResponse(data=recommendations)


@router.get("/categories")
async def get_skill_categories():
    return APIResponse(data=UniversalSkillEngine.SKILL_CATEGORIES)


@router.get("/levels")
async def get_skill_levels():
    levels = [
        {"level": 1, "name": "Novice", "xp_required": 0, "description": "Just starting out"},
        {"level": 2, "name": "Beginner", "xp_required": 100, "description": "Learning the basics"},
        {"level": 3, "name": "Intermediate", "xp_required": 300, "description": "Building competence"},
        {"level": 4, "name": "Advanced", "xp_required": 600, "description": "Solid proficiency"},
        {"level": 5, "name": "Expert", "xp_required": 1000, "description": "Deep expertise"},
        {"level": 6, "name": "Master", "xp_required": 1500, "description": "Industry leader"}
    ]
    return APIResponse(data=levels)
