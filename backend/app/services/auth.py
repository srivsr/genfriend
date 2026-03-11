from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.requests import SignupRequest, LoginRequest
from app.schemas.responses import TokenResponse, UserResponse
from fastapi import HTTPException, status

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def signup(self, request: SignupRequest) -> TokenResponse:
        existing = await self.db.execute(select(User).where(User.email == request.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user = User(email=request.email, password_hash=hash_password(request.password), name=request.name)
        self.db.add(user)
        await self.db.commit()

        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=token)

    async def login(self, request: LoginRequest) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.email == request.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=token)

    async def get_user(self, user_id: str) -> UserResponse:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserResponse.model_validate(user)
