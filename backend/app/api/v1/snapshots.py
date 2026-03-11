from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from typing import Optional, List
from app.schemas.responses import APIResponse
from app.dependencies import get_current_user_id
from app.core.database import get_db
from app.services.snapshot_service import DailySnapshotService, NudgeService

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


class MorningCheckinRequest(BaseModel):
    energy: int
    focus: str
    intentions: List[str]


class MiddayCheckinRequest(BaseModel):
    progress: List[str]
    blockers: List[str]


class EveningCheckinRequest(BaseModel):
    accomplishments: List[str]
    learnings: Optional[str] = None
    gratitude: Optional[str] = None


@router.get("/today")
async def get_today_snapshot(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = DailySnapshotService(db)
    snapshot = await service.get_or_create_today(str(user_id))
    return APIResponse(data=snapshot)


@router.post("/morning")
async def morning_checkin(
    request: MorningCheckinRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = DailySnapshotService(db)
    result = await service.morning_checkin(
        str(user_id),
        request.energy,
        request.focus,
        request.intentions
    )

    return APIResponse(data={
        "message": result.message,
        "suggestions": result.suggestions,
        "context": result.context
    }, message="Morning check-in complete!")


@router.post("/midday")
async def midday_checkin(
    request: MiddayCheckinRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = DailySnapshotService(db)
    result = await service.midday_checkin(
        str(user_id),
        request.progress,
        request.blockers
    )

    return APIResponse(data={
        "message": result.message,
        "suggestions": result.suggestions,
        "context": result.context
    }, message="Midday check-in complete!")


@router.post("/evening")
async def evening_checkin(
    request: EveningCheckinRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = DailySnapshotService(db)
    result = await service.evening_checkin(
        str(user_id),
        request.accomplishments,
        request.learnings or "",
        request.gratitude or ""
    )

    return APIResponse(data={
        "message": result.message,
        "suggestions": result.suggestions,
        "context": result.context
    }, message="Evening reflection saved!")


@router.get("/weekly")
async def get_weekly_summary(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = DailySnapshotService(db)
    summary = await service.get_weekly_summary(str(user_id))
    return APIResponse(data=summary)


@router.get("/history")
async def get_snapshot_history(
    days: int = 7,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = DailySnapshotService(db)
    snapshots = await service.snapshot_repo.get_recent(str(user_id), days)
    return APIResponse(data=[service._snapshot_to_dict(s) for s in snapshots])


@router.get("/streak")
async def get_streak(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = DailySnapshotService(db)
    streak = await service.snapshot_repo.get_streak(str(user_id))
    return APIResponse(data={"streak": streak})


nudge_router = APIRouter(prefix="/nudges", tags=["nudges"])


@nudge_router.get("")
async def get_nudges(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = NudgeService(db)
    nudges = await service.get_pending_nudges(str(user_id))
    return APIResponse(data=nudges)


@nudge_router.post("/generate")
async def generate_nudges(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = NudgeService(db)
    nudges = await service.generate_contextual_nudges(str(user_id))
    return APIResponse(data=nudges, message=f"Generated {len(nudges)} nudges")


@nudge_router.post("/{nudge_id}/read")
async def mark_nudge_read(
    nudge_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = NudgeService(db)
    result = await service.mark_read(str(nudge_id))
    return APIResponse(data={"marked": result})


@nudge_router.post("/{nudge_id}/acted")
async def mark_nudge_acted(
    nudge_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = NudgeService(db)
    result = await service.mark_acted(str(nudge_id))
    return APIResponse(data={"marked": result})
