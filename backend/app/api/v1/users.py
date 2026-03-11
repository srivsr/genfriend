from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
import json

from app.core import get_db
from app.dependencies import get_current_user_id
from app.models.user import User
from app.models.goal import Goal
from app.models.task import Task
from app.models.conversation import Conversation
from app.models.journal import JournalEntry
from app.models.if_then_plan import IfThenPlan
from app.models.snapshot import DailySnapshot
from app.models.experience import Experience
from app.models.identity import Identity
from app.schemas.responses import APIResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return APIResponse(data={
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "preferred_name": user.preferred_name,
        "coach_name": user.coach_name,
        "coach_tone": user.coach_tone,
        "coach_relationship": user.coach_relationship,
        "timezone": user.timezone,
        "onboarding_completed": user.onboarding_completed,
        "notification_level": user.notification_level,
        "voice_enabled": user.voice_enabled,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    })


@router.delete("/me")
async def delete_account(
    confirmation: str = Query(..., description="Must be 'DELETE' to confirm"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    if confirmation != "DELETE":
        raise HTTPException(
            status_code=400,
            detail="Confirmation required. Pass confirmation='DELETE' to proceed."
        )

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
    await db.execute(delete(Identity).where(Identity.user_id == user_id))
    await db.execute(delete(User).where(User.id == user_id))

    await db.commit()

    return APIResponse(
        data={"deleted": True},
        message="Your account and all associated data have been permanently deleted."
    )


@router.get("/me/export")
async def export_user_data(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    goals = (await db.execute(
        select(Goal).where(Goal.user_id == user_id)
    )).scalars().all()

    tasks = (await db.execute(
        select(Task).where(Task.user_id == user_id)
    )).scalars().all()

    journals = (await db.execute(
        select(JournalEntry).where(JournalEntry.user_id == user_id)
    )).scalars().all()

    def serialize_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "preferred_name": user.preferred_name,
            "timezone": user.timezone,
            "created_at": serialize_datetime(user.created_at),
        },
        "goals": [
            {
                "id": g.id,
                "title": g.title,
                "description": g.description,
                "status": g.status,
                "progress_percent": g.progress_percent,
                "current_streak": g.current_streak,
                "longest_streak": g.longest_streak,
                "woop_wish": g.woop_wish,
                "woop_outcome": g.woop_outcome,
                "woop_primary_obstacle": g.woop_primary_obstacle,
                "created_at": serialize_datetime(g.created_at),
            }
            for g in goals
        ],
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "scheduled_date": serialize_datetime(t.scheduled_date) if t.scheduled_date else None,
                "created_at": serialize_datetime(t.created_at),
            }
            for t in tasks
        ],
        "journal_entries": [
            {
                "id": j.id,
                "content": j.content,
                "entry_type": j.entry_type,
                "created_at": serialize_datetime(j.created_at),
            }
            for j in journals
        ]
    }

    return APIResponse(
        data=export_data,
        message="Your data export is ready. This contains all your personal data stored in Gen-Friend."
    )
