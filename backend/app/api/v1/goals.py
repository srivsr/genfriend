from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from typing import Optional
from app.schemas.responses import APIResponse
from app.mentor import goal_coach, identity_builder
from app.dependencies import get_current_user_id, get_current_user_with_ensure
from app.core.database import get_db
from app.repositories.goal_repository import GoalRepository

router = APIRouter(prefix="/goals", tags=["goals"])


def _goal_to_dict(goal, include_details: bool = False) -> dict:
    data = {
        "id": goal.id,
        "title": goal.title,
        "description": goal.description,
        "why": goal.why,
        "category": goal.category,
        "timeframe": goal.timeframe,
        "goal_type": goal.goal_type,
        "start_date": goal.start_date.isoformat() if goal.start_date else None,
        "end_date": goal.end_date.isoformat() if goal.end_date else None,
        "status": goal.status,
        "progress_percent": goal.progress_percent,
        "identity_id": goal.identity_id,
        "current_streak": goal.current_streak or 0,
        "longest_streak": goal.longest_streak or 0,
        "total_tasks_completed": goal.total_tasks_completed or 0,
        "created_at": goal.created_at.isoformat() if goal.created_at else None,
    }
    if include_details:
        data.update({
            "woop_primary_obstacle": goal.woop_primary_obstacle,
            "woop_outcome": goal.woop_outcome,
            "paused_at": goal.paused_at.isoformat() if goal.paused_at else None,
            "paused_reason": goal.paused_reason,
            "expected_resume_date": goal.expected_resume_date.isoformat() if goal.expected_resume_date else None,
            "archived_at": goal.archived_at.isoformat() if goal.archived_at else None,
            "archive_reason": goal.archive_reason,
            "completed_at": goal.completed_at.isoformat() if goal.completed_at else None,
        })
    return data


class CreateGoalRequest(BaseModel):
    initial_input: str

class UpdateGoalRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    progress_percent: Optional[int] = None

class CreateKeyResultRequest(BaseModel):
    title: str
    target_value: float
    unit: str

class UpdateProgressRequest(BaseModel):
    progress_percent: int
    notes: Optional[str] = None


class PauseGoalRequest(BaseModel):
    reason: Optional[str] = None  # health, work, priorities, recharge, other
    expected_resume_date: Optional[date] = None


class ResumeGoalRequest(BaseModel):
    adjust_timeline: bool = False


class CompleteGoalRequest(BaseModel):
    proud_of: Optional[str] = None
    learned: Optional[str] = None
    next_goal: Optional[str] = None


class ArchiveGoalRequest(BaseModel):
    reason: str  # abandoned, not_relevant, duplicate, replaced, other
    learning: Optional[str] = None


class DeletePermanentRequest(BaseModel):
    confirmation: str  # Must be "DELETE_PERMANENTLY"


async def get_user_goals(user_id: str, db: AsyncSession, status: str = "active") -> list:
    repo = GoalRepository(db)
    if status == "all":
        goals = await repo.get_by_user(user_id)
    else:
        goals = await repo.get_by_status(user_id, status)
    return [_goal_to_dict(g) for g in goals]


@router.get("")
async def list_goals(
    status: str = "active",
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = GoalRepository(db)

    if status == "all":
        goals = await repo.get_by_user(str(user_id))
    else:
        goals = await repo.get_by_status(str(user_id), status)

    return APIResponse(data=[_goal_to_dict(g) for g in goals])


def _parse_woop_from_input(input_text: str) -> dict:
    """Parse WOOP fields from the formatted input string."""
    woop = {}
    lines = input_text.split('\n')
    current_key = None
    current_value = []

    key_mapping = {
        'goal:': 'woop_wish',
        'future vision': 'future_you_visualization',
        'success looks like:': 'woop_outcome',
        'main obstacle:': 'woop_primary_obstacle',
        'if-then plan:': 'if_then_plan',
        'timeframe:': 'timeframe_hint',
        'goal type:': 'goal_type_hint',
    }

    for line in lines:
        line_lower = line.lower().strip()
        matched = False
        for key_phrase, field_name in key_mapping.items():
            if line_lower.startswith(key_phrase):
                if current_key and current_value:
                    woop[current_key] = '\n'.join(current_value).strip()
                current_key = field_name
                value_part = line[len(key_phrase):].strip()
                current_value = [value_part] if value_part else []
                matched = True
                break
        if not matched and current_key and line.strip():
            current_value.append(line.strip())

    if current_key and current_value:
        woop[current_key] = '\n'.join(current_value).strip()

    return woop


@router.post("")
async def create_goal(
    request: CreateGoalRequest,
    user_id: str = Depends(get_current_user_with_ensure),
    db: AsyncSession = Depends(get_db)
):
    identity = await identity_builder.get_identity(user_id)
    if not identity:
        return APIResponse(data=None, success=False, message="Please define your identity first")

    # Parse WOOP fields from input
    woop_data = _parse_woop_from_input(request.initial_input)

    result = await goal_coach.create_goal_with_coaching(str(user_id), request.initial_input, identity)

    repo = GoalRepository(db)

    # Use parsed timeframe or AI result
    timeframe_hint = woop_data.get('timeframe_hint', '').lower()
    if '1_month' in timeframe_hint or '1 month' in timeframe_hint:
        timeframe = 'monthly'
    elif '3_month' in timeframe_hint or '3 month' in timeframe_hint:
        timeframe = 'quarterly'
    elif '6_month' in timeframe_hint or '6 month' in timeframe_hint:
        timeframe = 'biannual'
    elif '1_year' in timeframe_hint or '1 year' in timeframe_hint:
        timeframe = 'annual'
    else:
        timeframe = result.get("timeframe", "quarterly")

    today = date.today()
    if timeframe == "weekly":
        end_date = today + timedelta(days=7)
    elif timeframe == "monthly":
        end_date = today + timedelta(days=30)
    elif timeframe == "quarterly":
        end_date = today + timedelta(days=90)
    elif timeframe == "biannual":
        end_date = today + timedelta(days=180)
    else:
        end_date = today + timedelta(days=365)

    goal = await repo.create(
        user_id=str(user_id),
        title=result.get("title", woop_data.get('woop_wish', request.initial_input)),
        description=result.get("description", ""),
        why=result.get("why", ""),
        category=result.get("category", "personal"),
        timeframe=timeframe,
        start_date=today,
        end_date=end_date,
        status="active",
        progress_percent=0,
        woop_wish=woop_data.get('woop_wish'),
        woop_outcome=woop_data.get('woop_outcome'),
        woop_primary_obstacle=woop_data.get('woop_primary_obstacle'),
        future_you_visualization=woop_data.get('future_you_visualization'),
    )

    goal_data = _goal_to_dict(goal)
    goal_data["suggested_key_results"] = result.get("suggested_key_results", [])

    return APIResponse(data=goal_data, message="Goal created with coaching")


@router.get("/{goal_id}")
async def get_goal(
    goal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = GoalRepository(db)
    goal = await repo.get_by_id(str(goal_id))

    if not goal or goal.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Goal not found")

    return APIResponse(data=_goal_to_dict(goal))


@router.patch("/{goal_id}")
async def update_goal(
    goal_id: UUID,
    request: UpdateGoalRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = GoalRepository(db)
    goal = await repo.get_by_id(str(goal_id))

    if not goal or goal.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Goal not found")

    update_data = request.model_dump(exclude_none=True)
    updated_goal = await repo.update(str(goal_id), **update_data)

    return APIResponse(data=_goal_to_dict(updated_goal), message="Goal updated")


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = GoalRepository(db)
    goal = await repo.get_by_id(str(goal_id))

    if not goal or goal.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Goal not found")

    await repo.delete(str(goal_id))

    return APIResponse(data=None, message="Goal deleted")


@router.post("/{goal_id}/key-results")
async def add_key_result(
    goal_id: UUID,
    request: CreateKeyResultRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    from app.models.key_result import KeyResult
    import uuid

    repo = GoalRepository(db)
    goal = await repo.get_by_id(str(goal_id))

    if not goal or goal.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Goal not found")

    key_result = KeyResult(
        id=str(uuid.uuid4()),
        goal_id=str(goal_id),
        title=request.title,
        target_value=request.target_value,
        current_value=0,
        unit=request.unit,
        progress_percent=0
    )
    db.add(key_result)
    await db.commit()

    return APIResponse(data={
        "id": key_result.id,
        "goal_id": str(goal_id),
        "title": request.title,
        "target_value": request.target_value,
        "current_value": 0,
        "unit": request.unit,
        "progress_percent": 0
    }, message="Key result added")


@router.patch("/{goal_id}/progress")
async def update_progress(
    goal_id: UUID,
    request: UpdateProgressRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = GoalRepository(db)
    goal = await repo.get_by_id(str(goal_id))

    if not goal or goal.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Goal not found")

    updated_goal = await repo.update_progress(str(goal_id), request.progress_percent)

    return APIResponse(
        data=_goal_to_dict(updated_goal),
        message="Progress updated"
    )


@router.get("/{goal_id}/analysis")
async def analyze_goal(
    goal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    identity = await identity_builder.get_identity(str(user_id))
    analysis = await goal_coach.analyze_progress(str(user_id), str(goal_id), identity or {})
    return APIResponse(data=analysis)


@router.get("/stats/overview")
async def get_goal_stats(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = GoalRepository(db)
    stats = await repo.get_goal_stats(str(user_id))
    return APIResponse(data=stats)


@router.get("/archived")
async def list_archived_goals(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = GoalRepository(db)
    goals = await repo.get_by_status(str(user_id), "archived")
    return APIResponse(data=[_goal_to_dict(g, include_details=True) for g in goals])


@router.post("/{goal_id}/pause")
async def pause_goal(
    goal_id: UUID,
    request: PauseGoalRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = GoalRepository(db)
    goal = await repo.get_by_id(str(goal_id))

    if not goal or goal.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Goal not found")

    if goal.status != "active":
        raise HTTPException(status_code=400, detail="Only active goals can be paused")

    updated = await repo.update(
        str(goal_id),
        status="paused",
        paused_at=datetime.utcnow(),
        paused_reason=request.reason,
        expected_resume_date=request.expected_resume_date,
        streak_at_pause=goal.current_streak or 0
    )

    return APIResponse(
        data=_goal_to_dict(updated, include_details=True),
        message=f"Goal paused. Your {goal.current_streak or 0}-day streak is preserved!"
    )


@router.post("/{goal_id}/resume")
async def resume_goal(
    goal_id: UUID,
    request: ResumeGoalRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = GoalRepository(db)
    goal = await repo.get_by_id(str(goal_id))

    if not goal or goal.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Goal not found")

    if goal.status != "paused":
        raise HTTPException(status_code=400, detail="Only paused goals can be resumed")

    update_data = {
        "status": "active",
        "current_streak": goal.streak_at_pause or 0,
    }

    if request.adjust_timeline and goal.paused_at and goal.end_date:
        pause_days = (datetime.utcnow() - goal.paused_at).days
        new_end_date = goal.end_date + timedelta(days=pause_days)
        update_data["end_date"] = new_end_date
        update_data["pause_duration_days"] = pause_days

    updated = await repo.update(str(goal_id), **update_data)

    return APIResponse(
        data=_goal_to_dict(updated, include_details=True),
        message=f"Welcome back! Your {updated.current_streak}-day streak is restored."
    )


@router.post("/{goal_id}/complete")
async def complete_goal(
    goal_id: UUID,
    request: CompleteGoalRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = GoalRepository(db)
    goal = await repo.get_by_id(str(goal_id))

    if not goal or goal.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Goal not found")

    if goal.status == "completed":
        raise HTTPException(status_code=400, detail="Goal is already completed")

    updated = await repo.update(
        str(goal_id),
        status="completed",
        progress_percent=100,
        completed_at=datetime.utcnow(),
        completion_proud_of=request.proud_of,
        completion_learned=request.learned,
        completion_next_goal=request.next_goal
    )

    total_days = (datetime.utcnow().date() - goal.start_date).days if goal.start_date else 0

    return APIResponse(
        data={
            "goal": _goal_to_dict(updated, include_details=True),
            "stats": {
                "total_days": total_days,
                "longest_streak": goal.longest_streak or 0,
                "tasks_completed": goal.total_tasks_completed or 0,
            },
            "celebration": f"🎉 Congratulations! You completed '{goal.title}' in {total_days} days!"
        },
        message="Goal completed! Amazing work!"
    )


@router.post("/{goal_id}/archive")
async def archive_goal(
    goal_id: UUID,
    request: ArchiveGoalRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = GoalRepository(db)
    goal = await repo.get_by_id(str(goal_id))

    if not goal or goal.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Goal not found")

    if goal.status == "archived":
        raise HTTPException(status_code=400, detail="Goal is already archived")

    updated = await repo.update(
        str(goal_id),
        status="archived",
        archived_at=datetime.utcnow(),
        archive_reason=request.reason,
        archive_learning=request.learning
    )

    return APIResponse(
        data=_goal_to_dict(updated, include_details=True),
        message="Goal archived. You can restore it anytime from Settings → Archived Goals."
    )


@router.post("/{goal_id}/restore")
async def restore_goal(
    goal_id: UUID,
    new_target_date: Optional[date] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = GoalRepository(db)
    goal = await repo.get_by_id(str(goal_id))

    if not goal or goal.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Goal not found")

    if goal.status != "archived":
        raise HTTPException(status_code=400, detail="Only archived goals can be restored")

    update_data = {"status": "active"}
    if new_target_date:
        update_data["end_date"] = new_target_date

    updated = await repo.update(str(goal_id), **update_data)

    return APIResponse(
        data=_goal_to_dict(updated, include_details=True),
        message="Goal restored! Let's continue where you left off."
    )


@router.delete("/{goal_id}/permanent")
async def delete_goal_permanent(
    goal_id: UUID,
    request: DeletePermanentRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    if request.confirmation != "DELETE_PERMANENTLY":
        raise HTTPException(
            status_code=400,
            detail="To permanently delete, set confirmation to 'DELETE_PERMANENTLY'"
        )

    repo = GoalRepository(db)
    goal = await repo.get_by_id(str(goal_id))

    if not goal or goal.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Goal not found")

    await repo.delete(str(goal_id))

    return APIResponse(
        data={"deleted": True, "goal_id": str(goal_id)},
        message="Goal permanently deleted. This cannot be undone."
    )
