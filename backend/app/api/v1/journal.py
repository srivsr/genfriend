from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.responses import APIResponse
from app.mentor import journal_keeper, identity_builder
from app.dependencies import get_current_user_id
from app.core.database import get_db
from app.repositories.journal_repository import JournalRepository

router = APIRouter(prefix="/journal", tags=["journal"])


def _entry_to_dict(entry) -> dict:
    return {
        "id": entry.id,
        "entry_type": entry.entry_type,
        "content": entry.content,
        "enrichment": entry.enrichment,
        "mood": entry.mood,
        "energy_level": entry.energy_level,
        "related_goal_id": entry.related_goal_id,
        "tags": entry.tags or [],
        "is_favorite": entry.is_favorite,
        "created_at": entry.created_at.isoformat() if entry.created_at else None
    }


class CreateEntryRequest(BaseModel):
    entry_type: str
    content: str
    related_goal_id: Optional[UUID] = None
    mood: Optional[str] = None
    energy_level: Optional[int] = None
    tags: list[str] = []


class UpdateEntryRequest(BaseModel):
    content: Optional[str] = None
    mood: Optional[str] = None
    energy_level: Optional[int] = None
    tags: Optional[list[str]] = None
    is_favorite: Optional[bool] = None


@router.get("")
async def list_entries(
    entry_type: Optional[str] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = JournalRepository(db)

    if entry_type and entry_type != 'all':
        entries = await repo.get_by_type(str(user_id), entry_type)
    else:
        entries = await repo.get_by_user(str(user_id))

    return APIResponse(data=[_entry_to_dict(e) for e in entries])


@router.post("")
async def create_entry(
    request: CreateEntryRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    identity = await identity_builder.get_identity(str(user_id))
    repo = JournalRepository(db)

    if request.entry_type == "win":
        enriched = await journal_keeper.capture_win(
            str(user_id),
            request.content,
            str(request.related_goal_id) if request.related_goal_id else None,
            identity
        )
    else:
        enriched = await journal_keeper.capture_moment(
            str(user_id),
            request.content,
            request.mood,
            request.energy_level
        )

    entry = await repo.create(
        user_id=str(user_id),
        entry_type=enriched.entry_type,
        content=enriched.content,
        enrichment=enriched.enrichment,
        mood=enriched.mood or request.mood,
        energy_level=request.energy_level,
        related_goal_id=str(request.related_goal_id) if request.related_goal_id else None,
        tags=request.tags
    )

    return APIResponse(data=_entry_to_dict(entry), message="Entry saved")


@router.get("/wins")
async def get_wins(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = JournalRepository(db)
    wins = await repo.get_wins(str(user_id))
    return APIResponse(data=[_entry_to_dict(w) for w in wins])


@router.get("/moments")
async def get_moments(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = JournalRepository(db)
    moments = await repo.get_moments(str(user_id))
    return APIResponse(data=[_entry_to_dict(m) for m in moments])


@router.get("/favorites")
async def get_favorites(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = JournalRepository(db)
    favorites = await repo.get_favorites(str(user_id))
    return APIResponse(data=[_entry_to_dict(f) for f in favorites])


@router.get("/search")
async def search_entries(
    q: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = JournalRepository(db)
    entries = await repo.search_content(str(user_id), q)
    return APIResponse(data=[_entry_to_dict(e) for e in entries])


@router.get("/stats/mood")
async def get_mood_stats(
    days: int = 30,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = JournalRepository(db)
    stats = await repo.get_mood_stats(str(user_id), days)
    return APIResponse(data=stats)


@router.post("/recall")
async def recall_wins(
    context: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    identity = await identity_builder.get_identity(str(user_id))
    recalled = await journal_keeper.recall_relevant_wins(str(user_id), context, identity)
    return APIResponse(data={"encouragement": recalled})


@router.patch("/{entry_id}")
async def update_entry(
    entry_id: UUID,
    request: UpdateEntryRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    from fastapi import HTTPException
    repo = JournalRepository(db)
    entry = await repo.get_by_id(str(entry_id))

    if not entry or entry.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Entry not found")

    update_data = request.model_dump(exclude_none=True)
    updated = await repo.update(str(entry_id), **update_data)

    return APIResponse(data=_entry_to_dict(updated), message="Entry updated")


@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    from fastapi import HTTPException
    repo = JournalRepository(db)
    entry = await repo.get_by_id(str(entry_id))

    if not entry or entry.user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Entry not found")

    await repo.delete(str(entry_id))
    return APIResponse(data=None, message="Entry deleted")


async def get_user_entries(user_id: str, db: AsyncSession, entry_type: str = None) -> list:
    repo = JournalRepository(db)
    if entry_type:
        entries = await repo.get_by_type(user_id, entry_type)
    else:
        entries = await repo.get_by_user(user_id)
    return [_entry_to_dict(e) for e in entries]
