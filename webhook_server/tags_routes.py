"""
User Tags API Routes

REST API endpoints for user-specific property tags.
Users can create custom tags and apply them to properties.
Tags are user-specific - each user has their own set of tags.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/api/tags",
    tags=["User Tags"]
)

# Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)


# ============================================
# Request/Response Models
# ============================================

class TagCreate(BaseModel):
    """Create a new tag."""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: str = Field("#3B82F6", description="Hex color code (e.g., #3B82F6)")


class TagUpdate(BaseModel):
    """Update an existing tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Tag name")
    color: Optional[str] = Field(None, description="Hex color code")


class TagResponse(BaseModel):
    """Tag response."""
    id: int
    user_id: str
    name: str
    color: str
    created_at: str
    updated_at: str


class PropertyTagCreate(BaseModel):
    """Add a tag to a property."""
    property_id: int = Field(..., description="Property ID")
    tag_id: int = Field(..., description="Tag ID")


class PropertyTagResponse(BaseModel):
    """Property tag response."""
    id: int
    user_id: str
    property_id: int
    tag_id: int
    tag: Optional[TagResponse] = None
    created_at: str


class PropertyTagsResponse(BaseModel):
    """Response for property tags with tag details."""
    property_id: int
    tags: List[TagResponse]


# ============================================
# TAG MANAGEMENT ENDPOINTS
# ============================================

@router.get(
    "/",
    response_model=List[TagResponse],
    summary="Get All User Tags",
    description="Get all tags created by the current user"
)
async def get_user_tags(
    user_id: str = Query(..., description="User ID from Clerk")
) -> List[TagResponse]:
    """Get all tags for a user."""
    try:
        result = supabase.table('user_tags').select('*').eq('user_id', user_id).order('name').execute()

        tags = []
        for tag in result.data:
            tags.append(TagResponse(
                id=tag['id'],
                user_id=tag['user_id'],
                name=tag['name'],
                color=tag['color'],
                created_at=tag['created_at'].isoformat() if hasattr(tag['created_at'], 'isoformat') else str(tag['created_at']),
                updated_at=tag['updated_at'].isoformat() if hasattr(tag['updated_at'], 'isoformat') else str(tag['updated_at']),
            ))

        return tags
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tags: {str(e)}")


@router.post(
    "/",
    response_model=TagResponse,
    summary="Create Tag",
    description="Create a new tag for the current user"
)
async def create_tag(
    request: TagCreate,
    user_id: str = Query(..., description="User ID from Clerk")
) -> TagResponse:
    """Create a new tag."""
    try:
        # Insert tag
        result = supabase.table('user_tags').insert({
            'user_id': user_id,
            'name': request.name,
            'color': request.color
        }).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create tag")

        tag = result.data[0]
        return TagResponse(
            id=tag['id'],
            user_id=tag['user_id'],
            name=tag['name'],
            color=tag['color'],
            created_at=tag['created_at'].isoformat() if hasattr(tag['created_at'], 'isoformat') else str(tag['created_at']),
            updated_at=tag['updated_at'].isoformat() if hasattr(tag['updated_at'], 'isoformat') else str(tag['updated_at']),
        )
    except Exception as e:
        # Check for unique constraint violation
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            raise HTTPException(status_code=400, detail="A tag with this name already exists")
        raise HTTPException(status_code=500, detail=f"Error creating tag: {str(e)}")


@router.put(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Update Tag",
    description="Update an existing tag"
)
async def update_tag(
    tag_id: int,
    request: TagUpdate,
    user_id: str = Query(..., description="User ID from Clerk")
) -> TagResponse:
    """Update a tag."""
    try:
        # First verify the tag belongs to the user
        existing = supabase.table('user_tags').select('*').eq('id', tag_id).eq('user_id', user_id).single().execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Tag not found or doesn't belong to user")

        # Build update data
        update_data = {}
        if request.name is not None:
            update_data['name'] = request.name
        if request.color is not None:
            update_data['color'] = request.color

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Update the tag
        result = supabase.table('user_tags').update(update_data).eq('id', tag_id).eq('user_id', user_id).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update tag")

        tag = result.data[0]
        return TagResponse(
            id=tag['id'],
            user_id=tag['user_id'],
            name=tag['name'],
            color=tag['color'],
            created_at=tag['created_at'].isoformat() if hasattr(tag['created_at'], 'isoformat') else str(tag['created_at']),
            updated_at=tag['updated_at'].isoformat() if hasattr(tag['updated_at'], 'isoformat') else str(tag['updated_at']),
        )
    except HTTPException:
        raise
    except Exception as e:
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            raise HTTPException(status_code=400, detail="A tag with this name already exists")
        raise HTTPException(status_code=500, detail=f"Error updating tag: {str(e)}")


@router.delete(
    "/{tag_id}",
    summary="Delete Tag",
    description="Delete a tag (also removes it from all properties)"
)
async def delete_tag(
    tag_id: int,
    user_id: str = Query(..., description="User ID from Clerk")
):
    """Delete a tag."""
    try:
        # First verify the tag belongs to the user
        existing = supabase.table('user_tags').select('*').eq('id', tag_id).eq('user_id', user_id).single().execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Tag not found or doesn't belong to user")

        # Delete the tag (property_tags will cascade delete due to FK constraint)
        supabase.table('user_tags').delete().eq('id', tag_id).eq('user_id', user_id).execute()

        return {"message": "Tag deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting tag: {str(e)}")


# ============================================
# PROPERTY TAG MANAGEMENT ENDPOINTS
# ============================================

@router.get(
    "/property/{property_id}",
    response_model=List[TagResponse],
    summary="Get Property Tags",
    description="Get all tags for a specific property (current user)"
)
async def get_property_tags(
    property_id: int,
    user_id: str = Query(..., description="User ID from Clerk")
) -> List[TagResponse]:
    """Get all tags for a property."""
    try:
        result = supabase.table('property_tags').select('tag_id, user_tags(*)').eq('user_id', user_id).eq('property_id', property_id).execute()

        tags = []
        for item in result.data:
            if item.get('user_tags'):
                tag_data = item['user_tags']
                tags.append(TagResponse(
                    id=tag_data['id'],
                    user_id=tag_data['user_id'],
                    name=tag_data['name'],
                    color=tag_data['color'],
                    created_at=tag_data['created_at'].isoformat() if hasattr(tag_data['created_at'], 'isoformat') else str(tag_data['created_at']),
                    updated_at=tag_data['updated_at'].isoformat() if hasattr(tag_data['updated_at'], 'isoformat') else str(tag_data['updated_at']),
                ))

        return tags
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching property tags: {str(e)}")


@router.post(
    "/property",
    response_model=TagResponse,
    summary="Add Tag to Property",
    description="Add a tag to a property"
)
async def add_tag_to_property(
    request: PropertyTagCreate,
    user_id: str = Query(..., description="User ID from Clerk")
) -> TagResponse:
    """Add a tag to a property."""
    try:
        # Verify the tag belongs to the user
        tag = supabase.table('user_tags').select('*').eq('id', request.tag_id).eq('user_id', user_id).single().execute()

        if not tag.data:
            raise HTTPException(status_code=404, detail="Tag not found or doesn't belong to user")

        # Check if property exists
        prop = supabase.table('foreclosure_listings').select('id').eq('id', request.property_id).single().execute()
        if not prop.data:
            raise HTTPException(status_code=404, detail="Property not found")

        # Add tag to property
        result = supabase.table('property_tags').insert({
            'user_id': user_id,
            'property_id': request.property_id,
            'tag_id': request.tag_id
        }).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to add tag to property")

        # Return the tag details
        tag_data = tag.data
        return TagResponse(
            id=tag_data['id'],
            user_id=tag_data['user_id'],
            name=tag_data['name'],
            color=tag_data['color'],
            created_at=tag_data['created_at'].isoformat() if hasattr(tag_data['created_at'], 'isoformat') else str(tag_data['created_at']),
            updated_at=tag_data['updated_at'].isoformat() if hasattr(tag_data['updated_at'], 'isoformat') else str(tag_data['updated_at']),
        )
    except HTTPException:
        raise
    except Exception as e:
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            raise HTTPException(status_code=400, detail="Property already has this tag")
        raise HTTPException(status_code=500, detail=f"Error adding tag to property: {str(e)}")


@router.delete(
    "/property/{property_id}/tag/{tag_id}",
    summary="Remove Tag from Property",
    description="Remove a tag from a property"
)
async def remove_tag_from_property(
    property_id: int,
    tag_id: int,
    user_id: str = Query(..., description="User ID from Clerk")
):
    """Remove a tag from a property."""
    try:
        # Delete the property tag
        result = supabase.table('property_tags').delete().eq('user_id', user_id).eq('property_id', property_id).eq('tag_id', tag_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Property tag not found")

        return {"message": "Tag removed from property successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing tag from property: {str(e)}")


@router.get(
    "/properties/by-tag/{tag_id}",
    response_model=List[int],
    summary="Get Properties by Tag",
    description="Get all property IDs that have a specific tag"
)
async def get_properties_by_tag(
    tag_id: int,
    user_id: str = Query(..., description="User ID from Clerk")
) -> List[int]:
    """Get all properties with a specific tag."""
    try:
        # Verify tag belongs to user
        tag = supabase.table('user_tags').select('id').eq('id', tag_id).eq('user_id', user_id).single().execute()
        if not tag.data:
            raise HTTPException(status_code=404, detail="Tag not found")

        # Get property IDs
        result = supabase.table('property_tags').select('property_id').eq('user_id', user_id).eq('tag_id', tag_id).execute()

        return [item['property_id'] for item in result.data]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching properties by tag: {str(e)}")
