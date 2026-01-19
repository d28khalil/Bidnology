"""
Supabase Authentication Module

Provides JWT validation and user context for protected routes.
Integrates with Supabase Auth for user authentication and authorization.
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import wraps

import httpx
import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")  # anon key for JWT verification
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# JWT settings
JWT_ALGORITHM = "HS256"
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", SUPABASE_ANON_KEY)

# Security scheme for FastAPI
security = HTTPBearer(auto_error=False)


# =============================================================================
# Models
# =============================================================================

class UserContext(BaseModel):
    """Authenticated user context from JWT."""
    id: str
    email: str
    email_verified: bool
    phone_verified: bool = False
    role: Optional[str] = "authenticated"
    app_metadata: Dict[str, Any] = {}
    user_metadata: Dict[str, Any] = {}

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.app_metadata.get("role") == "admin"


class AuthResponse(BaseModel):
    """Authentication check response."""
    authenticated: bool
    user: Optional[UserContext] = None
    error: Optional[str] = None


# =============================================================================
# JWT Validation Functions
# =============================================================================

def decode_jwt(token: str) -> Dict[str, Any]:
    """
    Decode and validate Supabase JWT token.

    Args:
        token: JWT token from Authorization header

    Returns:
        Decoded JWT payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode JWT without verification first to get header
        header_data = jwt.get_unverified_header(token)

        # Verify using Supabase JWT secret
        # The kid in the header helps identify which secret to use
        payload = jwt.decode(
            token,
            key=SUPABASE_ANON_KEY,
            algorithms=[JWT_ALGORITHM],
            options={
                "verify_aud": False,  # Supabase doesn't require aud verification
                "verify_exp": True,   # Verify expiration
            }
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_user_from_token(payload: Dict[str, Any]) -> UserContext:
    """
    Extract user information from decoded JWT payload.

    Args:
        payload: Decoded JWT payload

    Returns:
        UserContext with user information
    """
    # Supabase JWT structure
    return UserContext(
        id=payload.get("sub", ""),  # subject = user ID
        email=payload.get("email", ""),
        email_verified=payload.get("email_verified", False),
        phone_verified=payload.get("phone_verified", False),
        role=payload.get("role", "authenticated"),
        app_metadata=payload.get("app_metadata", {}),
        user_metadata=payload.get("user_metadata", {}),
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[UserContext]:
    """
    Get current user from JWT token (optional - returns None if no token).

    Use this for endpoints that work for both authenticated and anonymous users.

    Args:
        credentials: HTTP Authorization header

    Returns:
        UserContext if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        payload = decode_jwt(credentials.credentials)
        return extract_user_from_token(payload)
    except HTTPException:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> UserContext:
    """
    Get current authenticated user from JWT token (required).

    Use this for endpoints that require authentication.

    Args:
        credentials: HTTP Authorization header

    Returns:
        UserContext with authenticated user

    Raises:
        HTTPException: If not authenticated
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_jwt(credentials.credentials)
    return extract_user_from_token(payload)


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> UserContext:
    """
    Get current authenticated admin user.

    Use this for admin-only endpoints.

    Args:
        credentials: HTTP Authorization header

    Returns:
        UserContext with admin user

    Raises:
        HTTPException: If not authenticated or not an admin
    """
    user = await get_current_user(credentials)

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return user


# =============================================================================
# Supabase Auth Client Functions
# =============================================================================

class SupabaseAuthClient:
    """
    Client for interacting with Supabase Auth API.

    Provides user management functions beyond JWT validation.
    """

    def __init__(self):
        self.base_url = f"{SUPABASE_URL}/auth/v1"
        self.headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        }

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user details from Supabase Auth.

        Args:
            user_id: User UUID

        Returns:
            User data or None if not found
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/admin/users/{user_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception as e:
                logger.error(f"Error fetching user {user_id}: {e}")
                return None

    async def update_user_metadata(
        self,
        user_id: str,
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update user metadata in Supabase Auth.

        Args:
            user_id: User UUID
            metadata: Metadata to update

        Returns:
            Updated user data or None
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    f"{self.base_url}/admin/users/{user_id}",
                    headers=self.headers,
                    json={"user_metadata": metadata},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
                logger.error(f"Failed to update user metadata: {response.text}")
                return None
            except Exception as e:
                logger.error(f"Error updating user metadata: {e}")
                return None

    async def list_users(
        self,
        page: int = 1,
        per_page: int = 100
    ) -> list[Dict[str, Any]]:
        """
        List all users from Supabase Auth.

        Args:
            page: Page number
            per_page: Users per page

        Returns:
            List of user data
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/admin/users",
                    headers=self.headers,
                    params={"page": page, "per_page": per_page},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("users", [])
                logger.error(f"Failed to list users: {response.text}")
                return []
            except Exception as e:
                logger.error(f"Error listing users: {e}")
                return []


# =============================================================================
# Decorators for Route Protection
# =============================================================================

def require_auth(func):
    """
    Decorator to require authentication for a route.

    Usage:
        @router.get("/protected")
        @require_auth
        async def protected_endpoint(user: UserContext = Depends(get_current_user)):
            return {"message": f"Hello {user.email}"}
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check if user is in kwargs (injected by Depends)
        if 'user' not in kwargs or kwargs['user'] is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        return await func(*args, **kwargs)
    return wrapper


def require_admin(func):
    """
    Decorator to require admin role for a route.

    Usage:
        @router.get("/admin-only")
        @require_admin
        async def admin_endpoint(user: UserContext = Depends(get_current_admin)):
            return {"message": "Hello admin"}
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        user = kwargs.get('user')
        if not user or not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return await func(*args, **kwargs)
    return wrapper


# =============================================================================
# X-User-ID Header Support (Legacy)
# =============================================================================

async def get_user_id_from_header(
    x_user_id: Optional[str] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> str:
    """
    Get user ID from either JWT token or X-User-ID header.

    This provides backward compatibility during migration from X-User-ID to JWT.

    Priority:
    1. JWT token (if present and valid)
    2. X-User-ID header (fallback)

    Args:
        x_user_id: X-User-ID header value
        credentials: HTTP Authorization header with JWT

    Returns:
        User ID string

    Raises:
        HTTPException: If neither provides a valid user ID
    """
    # Try JWT first
    if credentials:
        try:
            user = await get_current_user_optional(credentials)
            if user:
                logger.debug(f"Using JWT user ID: {user.id}")
                return user.id
        except Exception as e:
            logger.debug(f"JWT validation failed: {e}")

    # Fallback to X-User-ID header
    if x_user_id:
        logger.warning(f"Using X-User-ID header (deprecated): {x_user_id}")
        return x_user_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required: Provide valid JWT or X-User-ID header"
    )
