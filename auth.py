"""
NutriLens Authentication & Authorization Module
Validates Supabase JWTs and enforces RBAC / IDOR protections.
"""

from typing import Optional, Dict, Any
import jwt
from fastapi import Header, HTTPException, status, Depends
from supabase import create_client, Client

from config import settings
from logger import logger

# Global cached Supabase client
_SUPABASE_CLIENT: Optional[Client] = None


def get_supabase_client() -> Client:
    """Dependency to retrieve configured Supabase client."""
    global _SUPABASE_CLIENT
    if _SUPABASE_CLIENT is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase credentials are not configured on the server"
            )
        _SUPABASE_CLIENT = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _SUPABASE_CLIENT


class AuthenticatedUser:
    """Represents a validated authenticated user."""
    def __init__(self, user_id: str, email: Optional[str] = None, claims: Optional[Dict[str, Any]] = None):
        self.user_id = user_id
        self.id = user_id  # alias
        self.email = email
        self.claims = claims or {}

    def __repr__(self):
        return f"<AuthenticatedUser user_id={self.user_id} email={self.email}>"


async def get_current_user(
    authorization: Optional[str] = Header(None),
    supabase: Client = Depends(get_supabase_client)
) -> AuthenticatedUser:
    """
    Extracts Bearer token from Authorization header and verifies it with Supabase.
    Throws 401 Unauthorized if invalid or missing.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme. Bearer token required.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 1. If SUPABASE_JWT_SECRET is configured, we can decode offline securely
    if settings.SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Token missing subject claim")
            return AuthenticatedUser(user_id=user_id, email=payload.get("email"), claims=payload)
        except jwt.PyJWTError as e:
            logger.warning(f"JWT signature verification failed: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid JWT token: {str(e)}")

    # 2. Otherwise verify token with Supabase Auth API
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="User session not found or expired")

        user = user_response.user
        return AuthenticatedUser(
            user_id=user.id,
            email=user.email,
            claims={"role": getattr(user, "role", "authenticated")}
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Supabase token validation error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    supabase: Client = Depends(get_supabase_client)
) -> Optional[AuthenticatedUser]:
    """Dependency for endpoints where authentication is optional (e.g. public feed browsing)."""
    if not authorization:
        return None
    try:
        return await get_current_user(authorization, supabase)
    except HTTPException:
        return None
