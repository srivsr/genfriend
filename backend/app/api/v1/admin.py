from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from typing import Optional
from datetime import datetime

from app.config import settings
from app.core import get_db
from app.models.user import User
from app.models.goal import Goal
from app.models.task import Task
from app.models.conversation import Conversation
from app.models.journal import JournalEntry
from app.models.if_then_plan import IfThenPlan
from app.models.snapshot import DailySnapshot
from app.models.experience import Experience
from app.schemas.responses import APIResponse

router = APIRouter(prefix="/admin", tags=["admin"])


async def verify_admin(admin_key: str = Query(..., alias="admin_key")):
    if admin_key != settings.admin_secret_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return True


@router.get("/users")
async def list_users(
    _: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None
):
    query = select(User)
    if search:
        query = query.where(
            (User.email.ilike(f"%{search}%")) |
            (User.name.ilike(f"%{search}%"))
        )
    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()

    count_query = select(func.count(User.id))
    if search:
        count_query = count_query.where(
            (User.email.ilike(f"%{search}%")) |
            (User.name.ilike(f"%{search}%"))
        )
    total = (await db.execute(count_query)).scalar()

    user_list = []
    for user in users:
        goals_count = (await db.execute(
            select(func.count(Goal.id)).where(Goal.user_id == user.id)
        )).scalar()

        user_list.append({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "preferred_name": user.preferred_name,
            "timezone": user.timezone,
            "onboarding_completed": user.onboarding_completed,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "goals_count": goals_count
        })

    return APIResponse(
        data={"users": user_list, "total": total, "skip": skip, "limit": limit},
        message=f"Found {len(user_list)} users"
    )


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    _: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    goals = (await db.execute(
        select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at.desc())
    )).scalars().all()

    tasks_count = (await db.execute(
        select(func.count(Task.id)).where(Task.user_id == user_id)
    )).scalar()

    conversations_count = (await db.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
    )).scalar()

    return APIResponse(data={
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "preferred_name": user.preferred_name,
            "coach_name": user.coach_name,
            "coach_tone": user.coach_tone,
            "timezone": user.timezone,
            "onboarding_completed": user.onboarding_completed,
            "onboarding_step": user.onboarding_step,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "stats": {
            "goals_count": len(goals),
            "tasks_count": tasks_count,
            "conversations_count": conversations_count,
        },
        "goals": [
            {
                "id": g.id,
                "title": g.title,
                "status": g.status,
                "progress_percent": g.progress_percent,
                "current_streak": g.current_streak,
                "created_at": g.created_at.isoformat() if g.created_at else None
            }
            for g in goals
        ]
    })


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    _: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(delete(IfThenPlan).where(IfThenPlan.user_id == user_id))
    await db.execute(delete(Task).where(Task.user_id == user_id))
    await db.execute(delete(Goal).where(Goal.user_id == user_id))
    await db.execute(delete(JournalEntry).where(JournalEntry.user_id == user_id))
    await db.execute(delete(Conversation).where(Conversation.user_id == user_id))
    await db.execute(delete(DailySnapshot).where(DailySnapshot.user_id == user_id))
    await db.execute(delete(Experience).where(Experience.user_id == user_id))
    await db.execute(delete(User).where(User.id == user_id))

    await db.commit()

    return APIResponse(data={"deleted_user_id": user_id}, message="User deleted successfully")


@router.post("/users/{user_id}/reset")
async def reset_user_data(
    user_id: str,
    reset_type: str = Query("all", description="all | goals | onboarding | streaks"),
    _: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_actions = []

    if reset_type in ["all", "goals"]:
        await db.execute(delete(IfThenPlan).where(IfThenPlan.user_id == user_id))
        await db.execute(delete(Task).where(Task.user_id == user_id))
        await db.execute(delete(Goal).where(Goal.user_id == user_id))
        reset_actions.append("goals, tasks, if-then plans deleted")

    if reset_type in ["all", "onboarding"]:
        user.onboarding_completed = False
        user.onboarding_step = None
        reset_actions.append("onboarding reset")

    if reset_type in ["all", "streaks"]:
        goals = (await db.execute(
            select(Goal).where(Goal.user_id == user_id)
        )).scalars().all()
        for goal in goals:
            goal.current_streak = 0
            goal.longest_streak = 0
            goal.total_tasks_completed = 0
        reset_actions.append("all streaks reset to 0")

    if reset_type == "all":
        await db.execute(delete(JournalEntry).where(JournalEntry.user_id == user_id))
        await db.execute(delete(Conversation).where(Conversation.user_id == user_id))
        await db.execute(delete(DailySnapshot).where(DailySnapshot.user_id == user_id))
        reset_actions.append("journal, conversations, snapshots deleted")

    await db.commit()

    return APIResponse(
        data={"user_id": user_id, "reset_type": reset_type, "actions": reset_actions},
        message=f"User data reset: {', '.join(reset_actions)}"
    )


@router.get("/stats")
async def get_admin_stats(
    _: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    active_users = (await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )).scalar()
    total_goals = (await db.execute(select(func.count(Goal.id)))).scalar()
    active_goals = (await db.execute(
        select(func.count(Goal.id)).where(Goal.status == "active")
    )).scalar()
    total_tasks = (await db.execute(select(func.count(Task.id)))).scalar()

    return APIResponse(data={
        "users": {"total": total_users, "active": active_users},
        "goals": {"total": total_goals, "active": active_goals},
        "tasks": {"total": total_tasks}
    })
