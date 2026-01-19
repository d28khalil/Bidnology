"""
Authentication Routes

Provides endpoints for user authentication, token verification,
and user management using Supabase Auth.
"""

import os
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from .auth import (
    UserContext,
    get_current_user,
    get_current_user_optional,
    get_current_admin,
    SupabaseAuthClient,
    security,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# =============================================================================
# Models
# =============================================================================

class SignUpRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    user_metadata: Optional[dict] = None


class SignUpResponse(BaseModel):
    """User registration response."""
    id: str
    email: str
    email_confirmed_at: Optional[str] = None
    user_metadata: dict


class SignInRequest(BaseModel):
    """User sign-in request."""
    email: EmailStr
    password: str


class SignInResponse(BaseModel):
    """User sign-in response."""
    access_token: str
    refresh_token: str
    user: UserContext


class TokenResponse(BaseModel):
    """Token verification response."""
    valid: bool
    user: Optional[UserContext] = None


class UserResponse(BaseModel):
    """User information response."""
    id: str
    email: str
    email_verified: bool
    user_metadata: dict
    app_metadata: dict
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# =============================================================================
# Routes
# =============================================================================

@router.post(
    "/signup",
    response_model=SignUpResponse,
    summary="Register New User",
    description="""
    Register a new user account using Supabase Auth.

    ---

    ## Request Body

    | Field | Type | Required | Description |
    |-------|------|----------|-------------|
    | `email` | string | Yes | User email address |
    | `password` | string | Yes | User password (min 6 chars) |
    | `user_metadata` | object | No | Optional user metadata |

    ---

    ## Response

    Returns the created user record. The user will receive a confirmation email.

    ---

    ## Example

    ```bash
    curl -X POST "http://localhost:8080/auth/signup" \\
      -H "Content-Type: application/json" \\
      -d '{
        "email": "user@example.com",
        "password": "securepassword123",
        "user_metadata": {
          "full_name": "John Doe",
          "company": "Acme Investments"
        }
      }'
    ```
    """,
)
async def signup(request: SignUpRequest):
    """
    Register a new user.

    Creates a new user in Supabase Auth and sends a confirmation email.
    """
    import httpx

    auth_client = SupabaseAuthClient()

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{auth_client.base_url}/signup",
                headers=auth_client.headers,
                json={
                    "email": request.email,
                    "password": request.password,
                    "user_metadata": request.user_metadata or {},
                    "email_confirm": True,  # Send confirmation email
                },
                timeout=10.0
            )

            if response.status_code not in (200, 201):
                logger.error(f"Signup failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=response.text
                )

            data = response.json()

            return SignUpResponse(
                id=data.get("id", ""),
                email=data.get("email", ""),
                email_confirmed_at=data.get("email_confirmed_at"),
                user_metadata=data.get("user_metadata", {})
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during signup: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to connect to auth service"
            )


@router.post(
    "/signin",
    response_model=SignInResponse,
    summary="Sign In User",
    description="""
    Sign in with email and password.

    ---

    ## Request Body

    | Field | Type | Required | Description |
    |-------|------|----------|-------------|
    | `email` | string | Yes | User email address |
    | `password` | string | Yes | User password |

    ---

    ## Response

    Returns JWT access token and refresh token along with user information.

    ---

    ## Example

    ```bash
    curl -X POST "http://localhost:8080/auth/signin" \\
      -H "Content-Type: application/json" \\
      -d '{
        "email": "user@example.com",
        "password": "securepassword123"
      }'
    ```
    """,
)
async def signin(request: SignInRequest):
    """
    Sign in a user.

    Returns JWT tokens for authentication.
    """
    import httpx

    auth_client = SupabaseAuthClient()

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{auth_client.base_url}/token?grant_type=password",
                headers=auth_client.headers,
                json={
                    "email": request.email,
                    "password": request.password,
                },
                timeout=10.0
            )

            if response.status_code != 200:
                logger.error(f"Signin failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            data = response.json()

            # Get user details to include in response
            access_token = data.get("access_token")

            # Decode JWT directly to get user info
            from .auth import decode_jwt, extract_user_from_token
            try:
                jwt_payload = decode_jwt(access_token)
                user_payload = extract_user_from_token(jwt_payload)
            except Exception as e:
                logger.error(f"Failed to decode JWT: {e}")
                # Fallback: create minimal user context from response data
                user_payload = UserContext(
                    id=data.get("user", {}).get("id", ""),
                    email=request.email,
                    email_verified=data.get("user", {}).get("email_confirmed_at") is not None,
                    phone_verified=False,
                    role="authenticated",
                    app_metadata=data.get("user", {}).get("app_metadata", {}),
                    user_metadata=data.get("user", {}).get("user_metadata", {}),
                )

            return SignInResponse(
                access_token=access_token,
                refresh_token=data.get("refresh_token", ""),
                user=user_payload
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during signin: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to connect to auth service"
            )


@router.post(
    "/verify",
    response_model=TokenResponse,
    summary="Verify JWT Token",
    description="""
    Verify a JWT token and return user information.

    ---

    ## Description

    Validates the JWT token from the Authorization header and returns
    the associated user information if the token is valid.

    This endpoint is useful for frontend apps to verify session state on load.

    ---

    ## Example

    ```bash
    curl -X POST "http://localhost:8080/auth/verify" \\
      -H "Authorization: Bearer YOUR_JWT_TOKEN"
    ```
    """,
)
async def verify_token(
    user: Optional[UserContext] = Depends(get_current_user_optional)
) -> TokenResponse:
    """Verify JWT token and return user info."""
    if user:
        return TokenResponse(valid=True, user=user)
    return TokenResponse(valid=False, user=None)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
    description="""
    Get information about the currently authenticated user.

    ---

    ## Authentication

    Requires valid JWT token in Authorization header.

    ---

    ## Example

    ```bash
    curl -X GET "http://localhost:8080/auth/me" \\
      -H "Authorization: Bearer YOUR_JWT_TOKEN"
    ```
    """,
)
async def get_current_user_endpoint(
    user: UserContext = Depends(get_current_user)
) -> UserResponse:
    """Return current user information."""
    # Fetch full user details from Supabase Auth
    auth_client = SupabaseAuthClient()
    user_data = await auth_client.get_user(user.id)

    return UserResponse(
        id=user.id,
        email=user.email,
        email_verified=user.email_verified,
        user_metadata=user.user_metadata,
        app_metadata=user.app_metadata,
        created_at=user_data.get("created_at") if user_data else None,
        updated_at=user_data.get("updated_at") if user_data else None,
    )


@router.put(
    "/me/metadata",
    summary="Update User Metadata",
    description="""
    Update current user's metadata.

    ---

    ## Authentication

    Requires valid JWT token in Authorization header.

    ---

    ## Request Body

    JSON object with metadata fields to update.

    ---

    ## Example

    ```bash
    curl -X PUT "http://localhost:8080/auth/me/metadata" \\
      -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "full_name": "John Doe",
        "company": "Acme Investments",
        "preferences": {
          "notifications": true,
          "default_county": "Essex"
        }
      }'
    ```
    """,
)
async def update_user_metadata(
    metadata: dict,
    user: UserContext = Depends(get_current_user)
):
    """Update current user's metadata."""
    auth_client = SupabaseAuthClient()

    result = await auth_client.update_user_metadata(user.id, metadata)

    if result:
        return {"message": "Metadata updated successfully", "user": result}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user metadata"
        )


class AdminUsersListResponse(BaseModel):
    """Admin users list response."""
    users: list
    total: int


@router.get(
    "/admin/users",
    response_model=AdminUsersListResponse,
    summary="List All Users (Admin)",
    description="""
    List all users in the system. Admin only.

    ---

    ## Authentication

    Requires valid JWT token with admin role.

    ---

    ## Query Parameters

    | Parameter | Type | Default | Description |
    |-----------|------|---------|-------------|
    | `page` | integer | 1 | Page number |
    | `per_page` | integer | 100 | Users per page |

    ---

    ## Example

    ```bash
    curl -X GET "http://localhost:8080/auth/admin/users?page=1&per_page=50" \\
      -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
    ```
    """,
)
async def list_users(
    page: int = 1,
    per_page: int = 100,
    admin: UserContext = Depends(get_current_admin)
) -> AdminUsersListResponse:
    """List all users (admin only)."""
    auth_client = SupabaseAuthClient()
    users = await auth_client.list_users(page=page, per_page=per_page)

    return AdminUsersListResponse(
        users=users,
        total=len(users)
    )


@router.post(
    "/admin/{user_id}/role",
    summary="Update User Role (Admin)",
    description="""
    Update a user's role (e.g., promote to admin). Admin only.

    ---

    ## Authentication

    Requires valid JWT token with admin role.

    ---

    ## Path Parameters

    | Parameter | Type | Description |
    |-----------|------|-------------|
    | `user_id` | string | User UUID |

    ---

    ## Request Body

    ```json
    {
      "role": "admin"
    }
    ```

    ---

    ## Example

    ```bash
    curl -X POST "http://localhost:8080/auth/admin/USER_ID/role" \\
      -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"role": "admin"}'
    ```
    """,
)
async def update_user_role(
    user_id: str,
    role_data: dict,
    admin: UserContext = Depends(get_current_admin)
):
    """
    Update a user's role.

    Updates the user's app_metadata.role field.
    """
    auth_client = SupabaseAuthClient()

    # Update app_metadata with role
    result = await auth_client.update_user_metadata(
        user_id,
        {"app_metadata": {"role": role_data.get("role", "authenticated")}}
    )

    if result:
        return {"message": f"User {user_id} role updated", "user": result}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user {user_id} role"
        )
