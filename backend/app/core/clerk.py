from typing import Optional
import jwt
from jwt import PyJWKClient
import httpx
from app.config import settings

_jwks_client: Optional[PyJWKClient] = None

def get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        if not settings.clerk_publishable_key:
            raise ValueError("CLERK_PUBLISHABLE_KEY not set")
        clerk_domain = settings.clerk_publishable_key.replace("pk_test_", "").replace("pk_live_", "")
        clerk_domain = clerk_domain.rstrip(".")
        jwks_url = f"https://{clerk_domain}.clerk.accounts.dev/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client

def verify_clerk_token(token: str) -> Optional[dict]:
    try:
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        return payload
    except Exception:
        return None

def get_clerk_user_id(token: str) -> Optional[str]:
    payload = verify_clerk_token(token)
    if payload:
        return payload.get("sub")
    return None
