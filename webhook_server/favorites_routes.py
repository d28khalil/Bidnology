"""
Favorites API Routes
Manages user favorite properties (simple star/favorite functionality)
"""

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field
from typing import Optional
import os
from supabase import create_client

router = APIRouter(prefix="/api/favorites", tags=["favorites"])

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ============================================================================
# Pydantic Models
# ============================================================================

class FavoriteRequest(BaseModel):
    user_id: str
    property_id: int

class FavoriteResponse(BaseModel):
    message: str

# ============================================================================
# Routes
# ============================================================================

@router.get("/user/{user_id}")
async def get_user_favorites(user_id: str):
    """
    Get all favorite property IDs for a user.

    Returns a list of property IDs that the user has favorited.
    """
    try:
        result = supabase.table('user_favorites').select('property_id').eq('user_id', user_id).execute()

        # Extract just the property IDs
        favorite_ids = [item['property_id'] for item in result.data] if result.data else []

        return favorite_ids

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching favorites: {str(e)}")


@router.post("")
async def add_favorite(request: FavoriteRequest):
    """
    Add a property to user's favorites.

    Creates a record in user_favorites table if it doesn't exist.
    """
    try:
        # Check if already favorited
        existing = supabase.table('user_favorites').select('*').eq('user_id', request.user_id).eq('property_id', request.property_id).execute()

        if existing.data:
            # Already favorited, return success
            return {"message": "Already favorited"}

        # Add to favorites
        supabase.table('user_favorites').insert({
            'user_id': request.user_id,
            'property_id': request.property_id
        }).execute()

        return {"message": "Added to favorites"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding favorite: {str(e)}")


@router.delete("")
async def remove_favorite(request: FavoriteRequest):
    """
    Remove a property from user's favorites.

    Deletes the record from user_favorites table.
    """
    try:
        # Delete from favorites
        result = supabase.table('user_favorites').delete().eq('user_id', request.user_id).eq('property_id', request.property_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Favorite not found")

        return {"message": "Removed from favorites"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing favorite: {str(e)}")
