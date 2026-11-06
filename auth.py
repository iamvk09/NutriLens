"""
NutriLens Authentication & Authorization Module
Validates Supabase JWTs, enforces RBAC / IDOR protections,
and propagates authenticated user JWTs to PostgREST for Row Level Security (RLS).
"""

from typing import Optional, Dict, Any
import jwt
from fastapi import Header, HTTPException, status, Depends
from supabase import create_client, Client
from supabase.client import ClientOptions

from config import settings
from logger import logger

# Global unauthenticated base client
_BASE_SUPABASE_CLIENT: Optional[Client] = None


def get_base_supabase_client() -> Client:
    """Returns unauthenticated base Supabase client (using anon key)."""
    global _BASE_SUPABASE_CLIENT
    if _BASE_SUPABASE_CLIENT is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase credentials are not configured on the server"
            )
        _BASE_SUPABASE_CLIENT = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _BASE_SUPABASE_CLIENT


def get_supabase_client() -> Client:
    """Dependency for public/unauthenticated endpoints."""
    return get_base_supabase_client()


class AuthenticatedUser:
    """Represents a validated authenticated user with access token."""
    def __init__(
        self,
        user_id: str,
        email: Optional[str] = None,
        token: Optional[str] = None,
        claims: Optional[Dict[str, Any]] = None
    ):
        self.user_id = user_id
        self.id = user_id  # alias
        self.email = email
        self.token = token
        self.claims = claims or {}

    def __repr__(self):
        return f"<AuthenticatedUser user_id={self.user_id} email={self.email}>"


async def get_current_user(
    authorization: Optional[str] = Header(None),
    base_supabase: Client = Depends(get_base_supabase_client)
) -> AuthenticatedUser:
    """
    Extracts Bearer token from Authorization header and verifies it.
    Returns AuthenticatedUser holding user credentials and raw JWT token.
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

    # 1. Offline verification if SUPABASE_JWT_SECRET configured
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
            return AuthenticatedUser(
                user_id=user_id,
                email=payload.get("email"),
                token=token,
                claims=payload
            )
        except jwt.PyJWTError as e:
            logger.warning(f"JWT signature verification failed: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid JWT token: {str(e)}")

    # 2. Supabase Auth API verification fallback
    try:
        user_response = base_supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="User session not found or expired")

        user = user_response.user
        return AuthenticatedUser(
            user_id=user.id,
            email=user.email,
            token=token,
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


def get_authenticated_supabase_client(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> Client:
    """
    Creates or configures a scoped per-request Supabase client authenticated
    with the current user's Bearer JWT.

    This propagates the user's JWT to PostgREST headers, ensuring that:
    1. PostgreSQL auth.uid() resolves to the authenticated user ID.
    2. Supabase Row-Level Security (RLS) policies evaluate with the true caller identity.
    3. Service-role credentials are NEVER exposed.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase credentials are not configured on the server"
        )

    # Instantiate client with anon key and user-scoped PostgREST auth header
    client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY,
        options=ClientOptions(
            headers={"Authorization": f"Bearer {current_user.token}"}
        )
    )
    if current_user.token:
        client.postgrest.auth(current_user.token)
    return client


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    base_supabase: Client = Depends(get_base_supabase_client)
) -> Optional[AuthenticatedUser]:
    """Dependency for endpoints where authentication is optional."""
    if not authorization:
        return None
    try:
        return await get_current_user(authorization, base_supabase)
    except HTTPException:
        return None
