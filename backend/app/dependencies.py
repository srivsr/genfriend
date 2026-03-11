from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict
import httpx
import os
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

# Environment detection - MUST be explicitly set to enable dev mode
ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower()
IS_DEV_MODE = ENVIRONMENT in ("development", "dev", "local", "test")

# Dev user UUID for testing (consistent UUID for dev_user_001)
# SECURITY: Only used when ENVIRONMENT is explicitly set to development
DEV_USER_UUID = "00000000-0000-0000-0000-000000000001"
DEV_USER_EMAIL = "dev@example.com"

# Clerk secret key
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")

# SECURITY: Warn loudly if no auth is configured in non-dev mode
if not CLERK_SECRET_KEY and not IS_DEV_MODE:
    logger.critical(
        "SECURITY CRITICAL: CLERK_SECRET_KEY not set and ENVIRONMENT is not 'development'. "
        "Authentication is DISABLED. Set CLERK_SECRET_KEY or ENVIRONMENT=development."
    )

# Cache for user creation to avoid repeated DB calls
_user_cache: set = set()


async def verify_clerk_token(token: str) -> Dict[str, str]:
    """Verify Clerk JWT token by calling Clerk's API"""
    if not CLERK_SECRET_KEY:
        # SECURITY: Only allow dev mode when explicitly enabled
        if IS_DEV_MODE:
            logger.warning("CLERK_SECRET_KEY not set - using dev mode (ENVIRONMENT=%s)", ENVIRONMENT)
            return {"user_id": DEV_USER_UUID, "email": DEV_USER_EMAIL}
        else:
            logger.error("CLERK_SECRET_KEY not set and not in dev mode - rejecting request")
            raise HTTPException(status_code=503, detail="Authentication service not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.clerk.com/v1/tokens/verify",
                headers={"Authorization": f"Bearer {CLERK_SECRET_KEY}"},
                params={"token": token}
            )

            if response.status_code == 200:
                data = response.json()
                user_id = data.get("sub") or data.get("user_id")

                if user_id:
                    # Get user email
                    user_response = await client.get(
                        f"https://api.clerk.com/v1/users/{user_id}",
                        headers={"Authorization": f"Bearer {CLERK_SECRET_KEY}"}
                    )

                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        email = user_data.get("email_addresses", [{}])[0].get("email_address")
                        return {"user_id": user_id, "email": email}

                return {"user_id": user_id, "email": data.get("email")}

            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            else:
                logger.error(f"Clerk API error: {response.status_code}")
                raise HTTPException(status_code=401, detail="Token verification failed")

    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Clerk API: {e}")
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def ensure_user_exists(user_id: str, email: str, db: AsyncSession) -> None:
    """Ensure user record exists in database, create if not"""
    if user_id in _user_cache:
        return

    from app.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        # Extract name from email (before @)
        name = email.split('@')[0].replace('.', ' ').replace('_', ' ').title() if email else "User"
        user = User(
            id=user_id,
            email=email,
            name=name,
            preferred_name=name.split()[0] if name else "Friend",
            is_active=True
        )
        db.add(user)
        await db.commit()
        logger.info(f"Created new user: {user_id} ({email})")

    _user_cache.add(user_id)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """Get current user ID from Clerk token or return dev user if no auth"""

    # If no credentials provided
    if not credentials:
        # SECURITY: Only allow dev mode when explicitly enabled via ENVIRONMENT
        if IS_DEV_MODE and not CLERK_SECRET_KEY:
            logger.debug("No credentials - using dev user (ENVIRONMENT=%s)", ENVIRONMENT)
            return DEV_USER_UUID
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify the Clerk token
    user_data = await verify_clerk_token(credentials.credentials)
    return user_data["user_id"]


from app.core.database import get_db

async def get_current_user_with_ensure(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> str:
    """Get current user ID and ensure user exists in database"""
    # Get user_id first
    if not credentials:
        # SECURITY: Only allow dev mode when explicitly enabled via ENVIRONMENT
        if IS_DEV_MODE and not CLERK_SECRET_KEY:
            user_id = DEV_USER_UUID
            email = DEV_USER_EMAIL
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    else:
        user_data = await verify_clerk_token(credentials.credentials)
        user_id = user_data["user_id"]
        email = user_data.get("email", "unknown@example.com")

    # Ensure user exists in database
    await ensure_user_exists(user_id, email, db)

    return user_id


# Alias for backward compatibility
async def get_current_user_id_with_db(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> str:
    """Alias for get_current_user_with_ensure"""
    return await get_current_user_with_ensure(credentials, db)
