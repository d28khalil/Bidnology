"""
Notes & Checklist Service

Manages user notes and due diligence checklists for properties.
Now uses the consolidated user_data table.

The user_data table stores:
- notes: JSONB array of note objects
- checklist: JSONB object with checklist items
- checklist_total, checklist_completed, checklist_completed_at
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from .feature_toggle_service import FeatureToggleService

logger = logging.getLogger(__name__)

# Note types
NOTE_TYPES = [
    "general",
    "due_diligence",
    "inspection",
    "financial",
    "legal"
]

# Default due diligence checklist items
DEFAULT_CHECKLIST = {
    "title_search_ordered": False,
    "title_review_complete": False,
    "inspection_complete": False,
    "pest_inspection_complete": False,
    "property_photos_reviewed": False,
    "comps_analyzed": False,
    "rehab_estimate_complete": False,
    "financing_secured": False,
    "insurance_quoted": False,
    "utility_costs_checked": False,
    "rental_research_complete": False,
    "hoa_documents_reviewed": False,
    "zoning_verified": False,
    "environmental_check_done": False,
    "closing_timeline_confirmed": False
}


class NotesService:
    """Service for property notes and due diligence checklists using user_data table"""

    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        self.feature_service = FeatureToggleService()

    async def is_feature_enabled(
        self,
        user_id: Optional[str] = None,
        county_id: Optional[int] = None,
        state: Optional[str] = None
    ) -> bool:
        """Check if notes and checklist feature is enabled"""
        return await self.feature_service.is_feature_enabled(
            "notes_checklist",
            user_id=user_id,
            county_id=county_id,
            state=state
        )

    # ========================================================================
    # PROPERTY NOTES (JSONB array in user_data)
    # ========================================================================

    async def add_note(
        self,
        property_id: int,
        user_id: str,
        note_text: str,
        note_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Add a note to a property.

        Notes are stored in the notes JSONB column in user_data table.
        """
        if not await self.is_feature_enabled(user_id):
            raise PermissionError("Notes feature not enabled")

        if note_type not in NOTE_TYPES:
            raise ValueError(f"Invalid note_type: {note_type}")

        current_time = datetime.utcnow().isoformat()

        # Create note object
        new_note = {
            "id": None,  # Will be set by database or generate unique ID
            "text": note_text,
            "type": note_type,
            "color": "default",
            "is_pinned": False,
            "created_at": current_time,
            "updated_at": current_time
        }

        # Get or create user_data entry
        result = self.supabase.table("user_data").select("*").eq(
            "user_id", user_id
        ).eq("property_id", property_id).execute()

        if result.data:
            # Add to existing notes array
            existing_data = result.data[0]
            notes = existing_data.get("notes", [])
            if isinstance(notes, str):
                notes = json.loads(notes)

            # Generate simple ID based on timestamp
            new_note["id"] = int(datetime.utcnow().timestamp() * 1000000)
            notes.append(new_note)

            update_result = self.supabase.table("user_data").update({
                "notes": notes,
                "updated_at": current_time
            }).eq("id", existing_data["id"]).execute()

            if update_result.data:
                logger.info(f"User {user_id} added {note_type} note to property {property_id}")
                return new_note
        else:
            # Create new user_data entry with notes
            new_note["id"] = 1
            insert_data = {
                "user_id": user_id,
                "property_id": property_id,
                "notes": [new_note],
                "created_at": current_time,
                "updated_at": current_time
            }

            insert_result = self.supabase.table("user_data").insert(insert_data).execute()

            if insert_result.data:
                logger.info(f"User {user_id} added {note_type} note to property {property_id}")
                return new_note

        raise Exception("Failed to add note")

    async def get_notes(
        self,
        property_id: int,
        user_id: str,
        note_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get notes for a property.

        Returns notes from the notes JSONB column in user_data.
        User-specific: only returns notes for the given user_id.
        """
        result = self.supabase.table("user_data").select("notes").eq(
            "user_id", user_id
        ).eq("property_id", property_id).execute()

        if not result.data or not result.data[0].get("notes"):
            return []

        notes = result.data[0].get("notes", [])
        if isinstance(notes, str):
            notes = json.loads(notes)

        # Filter by note_type if specified
        if note_type:
            notes = [n for n in notes if n.get("type") == note_type]

        # Sort by created_at descending
        notes.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return notes

    async def update_note(
        self,
        note_id: int,
        user_id: str,
        note_text: str
    ) -> Dict[str, Any]:
        """
        Update a note.

        Note: note_id is a simple integer ID, not a database primary key.
        """
        # Find the user_data entry containing this note
        result = self.supabase.table("user_data").select("*").eq(
            "user_id", user_id
        ).execute()

        current_time = datetime.utcnow().isoformat()

        for row in result.data:
            notes = row.get("notes", [])
            if isinstance(notes, str):
                notes = json.loads(notes)

            for note in notes:
                if note.get("id") == note_id:
                    note["text"] = note_text
                    note["updated_at"] = current_time

                    # Update the user_data row
                    self.supabase.table("user_data").update({
                        "notes": notes,
                        "updated_at": current_time
                    }).eq("id", row["id"]).execute()

                    logger.info(f"User {user_id} updated note {note_id}")
                    return note

        raise PermissionError("Not authorized to update this note")

    async def delete_note(
        self,
        note_id: int,
        user_id: str
    ) -> bool:
        """
        Delete a note from the notes JSONB array.
        """
        # Find the user_data entry containing this note
        result = self.supabase.table("user_data").select("*").eq(
            "user_id", user_id
        ).execute()

        current_time = datetime.utcnow().isoformat()

        for row in result.data:
            notes = row.get("notes", [])
            if isinstance(notes, str):
                notes = json.loads(notes)

            original_length = len(notes)
            notes = [n for n in notes if n.get("id") != note_id]

            if len(notes) < original_length:
                # Update the user_data row
                self.supabase.table("user_data").update({
                    "notes": notes,
                    "updated_at": current_time
                }).eq("id", row["id"]).execute()

                logger.info(f"User {user_id} deleted note {note_id}")
                return True

        return False

    # ========================================================================
    # DUE DILIGENCE CHECKLIST (JSONB in user_data)
    # ========================================================================

    async def get_checklist(
        self,
        property_id: int,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get due diligence checklist for a property.

        Returns checklist from the checklist JSONB column in user_data.
        """
        result = self.supabase.table("user_data").select(
            "checklist, checklist_total, checklist_completed, checklist_completed_at, created_at, updated_at"
        ).eq("property_id", property_id).eq("user_id", user_id).execute()

        if result.data:
            row = result.data[0]
            checklist = row.get("checklist", {})
            if isinstance(checklist, str):
                checklist = json.loads(checklist)

            # Return formatted response
            return {
                "property_id": property_id,
                "user_id": user_id,
                "checklist_items": checklist,
                "total_items": row.get("checklist_total", len(DEFAULT_CHECKLIST)),
                "completed_items": row.get("checklist_completed", 0),
                "completion_percent": round(
                    (row.get("checklist_completed", 0) / max(row.get("checklist_total", 1), 1)) * 100
                ) if row.get("checklist_total", 0) > 0 else 0,
                "completed_at": row.get("checklist_completed_at"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at")
            }

        # Create default checklist if none exists
        return await self._create_default_checklist(property_id, user_id)

    async def update_checklist(
        self,
        property_id: int,
        user_id: str,
        checklist_items: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        Update due diligence checklist.

        Updates the checklist JSONB column and calls update_checklist_progress function.
        """
        current_time = datetime.utcnow().isoformat()

        # Get existing user_data entry
        result = self.supabase.table("user_data").select("*").eq(
            "property_id", property_id
        ).eq("user_id", user_id).execute()

        total_items = len(checklist_items)
        completed_items = sum(1 for v in checklist_items.values() if v)
        completion_percent = round((completed_items / total_items * 100), 0) if total_items > 0 else 0

        checklist_completed_at = None
        if completed_items >= total_items:
            checklist_completed_at = current_time

        if result.data:
            # Update existing
            row = result.data[0]
            update_data = {
                "checklist": checklist_items,
                "checklist_total": total_items,
                "checklist_completed": completed_items,
                "checklist_completed_at": checklist_completed_at,
                "updated_at": current_time
            }

            update_result = self.supabase.table("user_data").update(
                update_data
            ).eq("id", row["id"]).execute()

            if update_result.data:
                logger.info(
                    f"User {user_id} updated checklist for property {property_id}: "
                    f"{completion_percent}% complete"
                )
                return {
                    "property_id": property_id,
                    "user_id": user_id,
                    "checklist_items": checklist_items,
                    "total_items": total_items,
                    "completed_items": completed_items,
                    "completion_percent": completion_percent,
                    "completed_at": checklist_completed_at,
                    "updated_at": current_time
                }
        else:
            # Create new user_data entry
            insert_data = {
                "user_id": user_id,
                "property_id": property_id,
                "checklist": checklist_items,
                "checklist_total": total_items,
                "checklist_completed": completed_items,
                "checklist_completed_at": checklist_completed_at,
                "created_at": current_time,
                "updated_at": current_time
            }

            insert_result = self.supabase.table("user_data").insert(insert_data).execute()

            if insert_result.data:
                return {
                    "property_id": property_id,
                    "user_id": user_id,
                    "checklist_items": checklist_items,
                    "total_items": total_items,
                    "completed_items": completed_items,
                    "completion_percent": completion_percent,
                    "completed_at": checklist_completed_at,
                    "created_at": current_time,
                    "updated_at": current_time
                }

        raise Exception("Failed to update checklist")

    async def reset_checklist(
        self,
        property_id: int,
        user_id: str
    ) -> Dict[str, Any]:
        """Reset checklist to default items (all unchecked)"""
        return await self.update_checklist(
            property_id, user_id, DEFAULT_CHECKLIST.copy()
        )

    async def get_all_checklists(
        self,
        user_id: str,
        min_completion: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all checklists for a user with optional filter.

        Returns user_data rows where checklist is not empty.
        """
        query = self.supabase.table("user_data").select(
            "*, foreclosure_listings(*)"
        ).eq("user_id", user_id).not_("checklist", "null").order("updated_at", desc=True)

        # Apply completion filter if specified
        if min_completion is not None:
            # Note: This filter is applied after fetching due to JSONB
            pass

        result = query.execute()

        checklists = []
        for row in result.data:
            completed = row.get("checklist_completed", 0)
            total = row.get("checklist_total", 1)
            completion_percent = round((completed / max(total, 1)) * 100)

            if min_completion is None or completion_percent >= min_completion:
                checklists.append({
                    "property_id": row.get("property_id"),
                    "user_id": row.get("user_id"),
                    "checklist_items": row.get("checklist", {}),
                    "total_items": total,
                    "completed_items": completed,
                    "completion_percent": completion_percent,
                    "completed_at": row.get("checklist_completed_at"),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at"),
                    "foreclosure_listings": row.get("foreclosure_listings")
                })

        return checklists

    async def _create_default_checklist(
        self,
        property_id: int,
        user_id: str
    ) -> Dict[str, Any]:
        """Create default checklist for a property"""
        current_time = datetime.utcnow().isoformat()

        checklist_data = {
            "user_id": user_id,
            "property_id": property_id,
            "checklist": DEFAULT_CHECKLIST.copy(),
            "checklist_total": len(DEFAULT_CHECKLIST),
            "checklist_completed": 0,
            "created_at": current_time,
            "updated_at": current_time
        }

        result = self.supabase.table("user_data").insert(checklist_data).execute()

        if not result.data:
            raise Exception("Failed to create default checklist")

        logger.info(f"Created default checklist for property {property_id}, user {user_id}")

        return {
            "property_id": property_id,
            "user_id": user_id,
            "checklist_items": DEFAULT_CHECKLIST.copy(),
            "total_items": len(DEFAULT_CHECKLIST),
            "completed_items": 0,
            "completion_percent": 0,
            "completed_at": None,
            "created_at": current_time,
            "updated_at": current_time
        }
