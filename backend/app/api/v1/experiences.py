from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from typing import Optional, List
from app.schemas.responses import APIResponse
from app.dependencies import get_current_user_id
from app.core.database import get_db
from app.services.experience_service import ExperienceService, ExperienceInput

router = APIRouter(prefix="/experiences", tags=["experiences"])


class CreateExperienceRequest(BaseModel):
    title: str
    description: str
    experience_type: str
    skills: Optional[List[str]] = None
    evidence: Optional[dict] = None
    outcome: Optional[str] = None
    impact_metrics: Optional[dict] = None
    related_goal_id: Optional[UUID] = None
    visibility: Optional[str] = "private"


class VerifyFromTasksRequest(BaseModel):
    task_ids: List[UUID]


class VerifyFromGoalRequest(BaseModel):
    goal_id: UUID


@router.get("")
async def list_experiences(
    experience_type: Optional[str] = None,
    verified_only: bool = False,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceService(db)

    if verified_only:
        experiences = await service.exp_repo.get_verified(str(user_id))
    elif experience_type:
        experiences = await service.exp_repo.get_by_type(str(user_id), experience_type)
    else:
        experiences = await service.exp_repo.get_by_user(str(user_id))

    return APIResponse(data=[service._experience_to_dict(e) for e in experiences])


@router.post("")
async def create_experience(
    request: CreateExperienceRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceService(db)

    input_data = ExperienceInput(
        title=request.title,
        description=request.description,
        experience_type=request.experience_type,
        skills=request.skills,
        evidence=request.evidence,
        outcome=request.outcome,
        impact_metrics=request.impact_metrics,
        related_goal_id=str(request.related_goal_id) if request.related_goal_id else None,
        visibility=request.visibility
    )

    result = await service.create_experience(str(user_id), input_data)
    return APIResponse(data=result, message="Experience created")


@router.get("/search")
async def search_experiences(
    q: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceService(db)
    results = await service.search_experiences(str(user_id), q)
    return APIResponse(data=results)


@router.get("/portfolio")
async def get_portfolio(
    public_only: bool = False,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceService(db)
    portfolio = await service.get_portfolio(str(user_id), public_only)
    return APIResponse(data=portfolio)


@router.get("/stats")
async def get_experience_stats(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceService(db)
    stats = await service.exp_repo.get_stats(str(user_id))
    return APIResponse(data=stats)


@router.get("/{experience_id}")
async def get_experience(
    experience_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceService(db)
    experience = await service.exp_repo.get_by_id(str(experience_id))

    if not experience or experience.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Experience not found")

    return APIResponse(data=service._experience_to_dict(experience))


@router.post("/{experience_id}/enrich")
async def enrich_experience(
    experience_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceService(db)
    enrichment = await service.enrich_experience(str(user_id), str(experience_id))

    if not enrichment:
        raise HTTPException(status_code=404, detail="Experience not found")

    return APIResponse(data=enrichment, message="Experience enriched with AI insights")


@router.post("/{experience_id}/verify/tasks")
async def verify_from_tasks(
    experience_id: UUID,
    request: VerifyFromTasksRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceService(db)
    task_ids = [str(tid) for tid in request.task_ids]
    verified = await service.verify_from_tasks(str(user_id), str(experience_id), task_ids)

    if verified:
        return APIResponse(data={"verified": True}, message="Experience verified from completed tasks")
    else:
        return APIResponse(data={"verified": False}, success=False, message="Could not verify - ensure tasks are completed")


@router.post("/{experience_id}/verify/goal")
async def verify_from_goal(
    experience_id: UUID,
    request: VerifyFromGoalRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceService(db)
    verified = await service.verify_from_goal(str(user_id), str(experience_id), str(request.goal_id))

    if verified:
        return APIResponse(data={"verified": True}, message="Experience verified from goal achievement")
    else:
        return APIResponse(data={"verified": False}, success=False, message="Could not verify - ensure goal has 80%+ progress")


@router.get("/skills/summary")
async def get_skill_summary(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceService(db)
    summary = await service.skill_repo.get_skill_summary(str(user_id))
    return APIResponse(data=summary)


@router.get("/skills/top")
async def get_top_skills(
    limit: int = 10,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceService(db)
    skills = await service.skill_repo.get_top_skills(str(user_id), limit)
    return APIResponse(data=[service._skill_to_dict(s) for s in skills])


@router.get("/achievements")
async def get_achievements(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceService(db)
    achievements = await service.achievement_repo.get_recent(str(user_id), 20)
    return APIResponse(data=[service._achievement_to_dict(a) for a in achievements])
