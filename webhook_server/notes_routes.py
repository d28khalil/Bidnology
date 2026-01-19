"""
User Notes API Routes

REST API endpoints for user-specific property notes.
Users can only view and manage their own notes.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/api/notes",
    tags=["User Notes"]
)

# Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)


# ============================================
# Request/Response Models
# ============================================

class NoteCreate(BaseModel):
    """Create a new note."""
    property_id: int = Field(..., description="Property ID to attach note to")
    note: str = Field(..., min_length=1, max_length=10000, description="Note content")


class NoteUpdate(BaseModel):
    """Update an existing note."""
    note: str = Field(..., min_length=1, max_length=10000, description="Updated note content")


class NoteResponse(BaseModel):
    """Note response."""
    id: int
    user_id: str
    property_id: int
    note: str
    created_at: str
    updated_at: str


# ============================================
# API ENDPOINTS
# ============================================

@router.get(
    "/property/{property_id}",
    response_model=Optional[NoteResponse],
    summary="Get User Note for Property",
    description="Get the current user's note for a specific property"
)
async def get_user_note(
    property_id: int,
    user_id: str = Query(..., description="User ID from Clerk")
) -> Optional[NoteResponse]:
    """Get the current user's note for a property."""
    try:
        result = supabase.table('user_notes').select('*').eq('user_id', user_id).eq('property_id', property_id).execute()

        if not result.data:
            return None

        note = result.data[0]
        return NoteResponse(
            id=note['id'],
            user_id=note['user_id'],
            property_id=note['property_id'],
            note=note['note'],
            created_at=note['created_at'].isoformat() if hasattr(note['created_at'], 'isoformat') else str(note['created_at']),
            updated_at=note['updated_at'].isoformat() if hasattr(note['updated_at'], 'isoformat') else str(note['updated_at']),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching note: {str(e)}")


@router.get(
    "/user/{user_id}",
    response_model=list[NoteResponse],
    summary="Get All User Notes",
    description="Get all notes for a specific user"
)
async def get_all_user_notes(
    user_id: str,
    limit: int = 100,
    offset: int = 0
) -> list[NoteResponse]:
    """Get all notes for a user."""
    try:
        result = supabase.table('user_notes').select('*').eq('user_id', user_id).order('updated_at', desc=True).range(offset, offset + limit - 1).execute()

        notes = []
        for note in result.data:
            notes.append(NoteResponse(
                id=note['id'],
                user_id=note['user_id'],
                property_id=note['property_id'],
                note=note['note'],
                created_at=note['created_at'].isoformat() if hasattr(note['created_at'], 'isoformat') else str(note['created_at']),
                updated_at=note['updated_at'].isoformat() if hasattr(note['updated_at'], 'isoformat') else str(note['updated_at']),
            ))

        return notes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching notes: {str(e)}")


@router.post(
    "/",
    response_model=NoteResponse,
    summary="Create Note",
    description="Create a new note for a property"
)
async def create_note(
    request: NoteCreate,
    user_id: str = Query(..., description="User ID from Clerk")
) -> NoteResponse:
    """Create a new note."""
    try:
        # Check if property exists
        prop_result = supabase.table('foreclosure_listings').select('id').eq('id', request.property_id).single().execute()
        if not prop_result.data:
            raise HTTPException(status_code=404, detail="Property not found")

        # Insert note
        result = supabase.table('user_notes').insert({
            'user_id': user_id,
            'property_id': request.property_id,
            'note': request.note
        }).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create note")

        note = result.data[0]
        return NoteResponse(
            id=note['id'],
            user_id=note['user_id'],
            property_id=note['property_id'],
            note=note['note'],
            created_at=note['created_at'].isoformat() if hasattr(note['created_at'], 'isoformat') else str(note['created_at']),
            updated_at=note['updated_at'].isoformat() if hasattr(note['updated_at'], 'isoformat') else str(note['updated_at']),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating note: {str(e)}")


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update Note",
    description="Update an existing note"
)
async def update_note(
    note_id: int,
    request: NoteUpdate,
    user_id: str = Query(..., description="User ID from Clerk")
) -> NoteResponse:
    """Update a note."""
    try:
        # First verify the note belongs to the user
        existing = supabase.table('user_notes').select('*').eq('id', note_id).eq('user_id', user_id).single().execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Note not found or doesn't belong to user")

        # Update the note
        result = supabase.table('user_notes').update({
            'note': request.note
        }).eq('id', note_id).eq('user_id', user_id).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update note")

        note = result.data[0]
        return NoteResponse(
            id=note['id'],
            user_id=note['user_id'],
            property_id=note['property_id'],
            note=note['note'],
            created_at=note['created_at'].isoformat() if hasattr(note['created_at'], 'isoformat') else str(note['created_at']),
            updated_at=note['updated_at'].isoformat() if hasattr(note['updated_at'], 'isoformat') else str(note['updated_at']),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating note: {str(e)}")


@router.delete(
    "/{note_id}",
    summary="Delete Note",
    description="Delete an existing note"
)
async def delete_note(
    note_id: int,
    user_id: str = Query(..., description="User ID from Clerk")
):
    """Delete a note."""
    try:
        # First verify the note belongs to the user
        existing = supabase.table('user_notes').select('*').eq('id', note_id).eq('user_id', user_id).single().execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Note not found or doesn't belong to user")

        # Delete the note
        supabase.table('user_notes').delete().eq('id', note_id).eq('user_id', user_id).execute()

        return {"message": "Note deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting note: {str(e)}")
