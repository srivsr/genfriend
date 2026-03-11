from fastapi import APIRouter, Depends
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from datetime import time
from app.schemas.responses import APIResponse
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/preferences", tags=["preferences"])

class UpdatePreferencesRequest(BaseModel):
    daily_checkin_time: Optional[str] = None
    preferred_channel: Optional[str] = None
    checkin_frequency: Optional[str] = None
    mentor_tone: Optional[str] = None
    notifications_enabled: Optional[bool] = None

@router.get("")
async def get_preferences(user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data={
        "daily_checkin_time": "09:00",
        "preferred_channel": "push",
        "checkin_frequency": "daily",
        "mentor_tone": "balanced",
        "notifications_enabled": True
    })

@router.patch("")
async def update_preferences(request: UpdatePreferencesRequest, user_id: UUID = Depends(get_current_user_id)):
    return APIResponse(data=request.model_dump(exclude_none=True), message="Preferences updated")
