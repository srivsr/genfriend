from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_db
from app.services import AuthService
from app.schemas.requests import SignupRequest, LoginRequest
from app.schemas.responses import APIResponse, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=APIResponse[TokenResponse])
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.signup(request)
    return APIResponse(data=result, message="Account created successfully")

@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.login(request)
    return APIResponse(data=result, message="Login successful")
