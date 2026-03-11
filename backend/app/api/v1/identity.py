from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from app.schemas.responses import APIResponse
from app.mentor import identity_builder
from app.dependencies import get_current_user_id, ensure_user_exists, DEV_USER_EMAIL
from app.core.database import get_db

router = APIRouter(prefix="/identity", tags=["identity"])

class CreateIdentityRequest(BaseModel):
    initial_input: str

class RefineIdentityRequest(BaseModel):
    additional_input: str

@router.get("")
async def get_identity(user_id: UUID = Depends(get_current_user_id)):
    identity = await identity_builder.get_identity(str(user_id))
    if not identity:
        return APIResponse(data=None, message="No identity defined yet. Tell us who you want to become!")
    return APIResponse(data=identity)

@router.post("")
async def create_identity(
    request: CreateIdentityRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    # Ensure user record exists in database
    await ensure_user_exists(str(user_id), DEV_USER_EMAIL, db)

    result = await identity_builder.build_identity(str(user_id), request.initial_input)
    return APIResponse(data=result, message="Identity created")

@router.post("/refine")
async def refine_identity(request: RefineIdentityRequest, user_id: UUID = Depends(get_current_user_id)):
    result = await identity_builder.refine_identity(str(user_id), request.additional_input)
    return APIResponse(data=result, message="Identity refined")
