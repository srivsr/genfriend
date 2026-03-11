from fastapi import APIRouter, Depends
from uuid import UUID
from datetime import datetime
from app.schemas.requests import CreateEntryRequest, UpdateEntryRequest
from app.schemas.responses import APIResponse, EntryResponse
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/entries", tags=["entries"])

@router.get("", response_model=APIResponse[list[EntryResponse]])
async def list_entries(user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data=[])

@router.post("", response_model=APIResponse[EntryResponse])
async def create_entry(request: CreateEntryRequest, user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data=EntryResponse(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        content=request.content,
        entry_type=request.entry_type,
        mood=request.mood,
        mood_intensity=request.mood_intensity,
        tags=request.tags,
        created_at=datetime.utcnow()
    ), message="Entry created")

@router.get("/{entry_id}", response_model=APIResponse[EntryResponse])
async def get_entry(entry_id: UUID, user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data=None, message="Entry not found")

@router.patch("/{entry_id}", response_model=APIResponse[EntryResponse])
async def update_entry(entry_id: UUID, request: UpdateEntryRequest, user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data=None, message="Entry updated")

@router.delete("/{entry_id}")
async def delete_entry(entry_id: UUID, user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data=None, message="Entry deleted")
