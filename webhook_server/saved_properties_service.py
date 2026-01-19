"""
Saved Properties Service with Kanban Board

Manages saved properties and Kanban stage tracking.
Now uses the consolidated user_data table.

The user_data table consolidates:
- saved_properties -> is_saved, kanban_stage, saved_notes
- user_watchlist -> is_watched, watch_priority, alert_*
- property_notes -> notes (JSONB array)
- due_diligence_checklist -> checklist (JSONB)
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .feature_toggle_service import FeatureToggleService

logger = logging.getLogger(__name__)


# Kanban stages
KANBAN_STAGES = [
    "researching",      # Initial research phase
    "analyzing",         # Deep analysis in progress
    "due_diligence",     # Due diligence tasks
    "bidding",           # Preparing/placing bid
    "won",              # Successfully acquired
    "lost",             # Didn't get the property
    "archived"          # No longer relevant
]


class SavedPropertiesService:
    """
    Service for managing saved properties and Kanban board.

    Uses the consolidated user_data table which combines:
    - Saved properties (is_saved, kanban_stage, saved_notes)
    - Watchlist (is_watched, watch_priority, alerts)
    - Notes (notes JSONB array)
    - Checklist (checklist JSONB)

    Features:
    - Save/unsave properties
    - Move properties between Kanban stages
    - Get user's Kanban board
    - Track stage history
    """

    KANBAN_STAGES = KANBAN_STAGES

    def __init__(self):
        self.feature_service = FeatureToggleService()

    async def save_property(
        self,
        user_id: str,
        property_id: int,
        notes: Optional[str] = None,
        kanban_stage: str = "researching",
        county_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Save a property for a user.

        Args:
            user_id: User ID
            property_id: Property ID to save
            notes: Optional notes (goes into saved_notes)
            kanban_stage: Initial Kanban stage (default: researching)
            county_id: Optional county for feature check

        Returns:
            Saved property record or None if feature disabled
        """
        # Check if feature is enabled
        save_enabled = await self.feature_service.is_feature_enabled(
            "save_property",
            user_id=user_id,
            county_id=county_id
        )

        if not save_enabled:
            logger.debug("Save property feature is disabled")
            return None

        # Check Kanban feature
        kanban_enabled = await self.feature_service.is_feature_enabled(
            "kanban_board",
            user_id=user_id,
            county_id=county_id
        )

        if not kanban_enabled:
            kanban_stage = "researching"

        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            # Validate property exists before saving
            prop_check = supabase.table("foreclosure_listings").select("id").eq("id", property_id).execute()
            if not prop_check.data:
                logger.warning(f"Property {property_id} does not exist")
                return None

            # Check if user_data entry exists
            existing = supabase.table("user_data").select("*").eq(
                "user_id", user_id
            ).eq("property_id", property_id).execute()

            current_time = datetime.utcnow().isoformat()

            if existing.data:
                # Update existing entry to set is_saved
                update_data = {
                    "is_saved": True,
                    "saved_notes": notes,
                    "kanban_stage": kanban_stage,
                    "updated_at": current_time
                }
                result = supabase.table("user_data").update(
                    update_data
                ).eq("id", existing.data[0]["id"]).execute()
            else:
                # Insert new user_data entry
                insert_data = {
                    "user_id": user_id,
                    "property_id": property_id,
                    "is_saved": True,
                    "saved_notes": notes,
                    "kanban_stage": kanban_stage,
                    "created_at": current_time,
                    "updated_at": current_time
                }
                result = supabase.table("user_data").insert(insert_data).execute()

            if result.data:
                logger.info(f"Saved property {property_id} for user {user_id}")
                # Return in format compatible with old API
                return self._format_saved_property(result.data[0])
            return None

        except Exception as e:
            logger.error(f"Error saving property {property_id} for user {user_id}: {e}")
            return None

    def _format_saved_property(self, user_data_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format user_data row to match old saved_properties API format.
        """
        return {
            "id": user_data_row.get("id"),
            "user_id": user_data_row.get("user_id"),
            "property_id": user_data_row.get("property_id"),
            "notes": user_data_row.get("saved_notes"),
            "kanban_stage": user_data_row.get("kanban_stage"),
            "saved_at": user_data_row.get("created_at"),
            "stage_updated_at": user_data_row.get("updated_at"),
        }

    async def unsave_property(self, user_id: str, saved_id: int) -> bool:
        """
        Unsave/remove a saved property for a user.

        Note: saved_id is now the user_data table id, not property_id.
        For backward compatibility, we accept saved_id and delete the row.
        """
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            # First get the user_data entry to verify ownership
            existing = supabase.table("user_data").select("*").eq(
                "id", saved_id
            ).eq("user_id", user_id).execute()

            if not existing.data:
                logger.warning(f"User data entry {saved_id} not found for user {user_id}")
                return False

            # Instead of deleting, set is_saved to False to preserve other data
            result = supabase.table("user_data").update({
                "is_saved": False,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", saved_id).eq("user_id", user_id).execute()

            logger.info(f"Unsaved property for user {user_id}, user_data id {saved_id}")
            return True

        except Exception as e:
            logger.error(f"Error unsaving property for user {user_id}: {e}")
            return False

    async def update_kanban_stage(
        self,
        user_id: str,
        saved_id: int,
        new_stage: str
    ) -> Optional[Dict[str, Any]]:
        """
        Move a property to a new Kanban stage.

        Args:
            user_id: User ID
            saved_id: user_data table ID (was saved_properties id)
            new_stage: New Kanban stage

        Returns:
            Updated record or None
        """
        if new_stage not in self.KANBAN_STAGES:
            logger.warning(f"Invalid Kanban stage: {new_stage}")
            return None

        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            updates = {
                "kanban_stage": new_stage,
                "updated_at": datetime.utcnow().isoformat()
            }

            result = supabase.table("user_data").update(updates).eq("id", saved_id).eq("user_id", user_id).execute()

            if result.data:
                logger.info(f"Moved saved property {saved_id} to stage {new_stage}")
                return self._format_saved_property(result.data[0])
            return None

        except Exception as e:
            logger.error(f"Error updating Kanban stage for saved property {saved_id}: {e}")
            return None

    async def get_saved_properties(
        self,
        user_id: str,
        kanban_stage: Optional[str] = None,
        county_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get saved properties for a user.

        Args:
            user_id: User ID
            kanban_stage: Optional filter by Kanban stage
            county_id: Optional county for feature check

        Returns:
            List of saved properties with property details
        """
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        # Check if Kanban feature is enabled
        kanban_enabled = await self.feature_service.is_feature_enabled(
            "kanban_board",
            user_id=user_id,
            county_id=county_id
        )

        try:
            # Query user_data table for saved properties
            query = supabase.table("user_data").select(
                "*, foreclosure_listings(*)"
            ).eq("user_id", user_id).eq("is_saved", True)

            if kanban_enabled and kanban_stage:
                query = query.eq("kanban_stage", kanban_stage)

            query = query.order("created_at", desc=True)

            result = query.execute()

            # Format results to match old API
            return [self._format_saved_property(row) for row in result.data]

        except Exception as e:
            logger.error(f"Error fetching saved properties for user {user_id}: {e}")
            return []

    async def get_kanban_board(
        self,
        user_id: str,
        county_id: Optional[int] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get user's Kanban board with all stages.

        Uses the database function get_user_kanban_board for efficiency.

        Returns:
            Dict mapping stage names to lists of properties
        """
        kanban_enabled = await self.feature_service.is_feature_enabled(
            "kanban_board",
            user_id=user_id,
            county_id=county_id
        )

        if not kanban_enabled:
            # Just return all saved properties in "all" stage
            saved = await self.get_saved_properties(user_id)
            return {"all": saved}

        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            # Call the database function
            result = supabase.rpc("get_user_kanban_board", {"p_user_id": user_id}).execute()

            if result.data:
                return result.data
            else:
                return {stage: [] for stage in self.KANBAN_STAGES}

        except Exception as e:
            logger.error(f"Error getting Kanban board for user {user_id}: {e}")
            # Fallback to manual query
            board = {stage: [] for stage in self.KANBAN_STAGES}
            for stage in self.KANBAN_STAGES:
                stage_properties = await self.get_saved_properties(user_id, kanban_stage=stage)
                board[stage] = stage_properties
            return board

    async def update_notes(
        self,
        user_id: str,
        saved_id: int,
        notes: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update notes for a saved property.

        Updates saved_notes field in user_data table.
        """
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            result = supabase.table("user_data").update({
                "saved_notes": notes,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", saved_id).eq("user_id", user_id).execute()

            if result.data:
                return self._format_saved_property(result.data[0])
            return None

        except Exception as e:
            logger.error(f"Error updating notes for saved property {saved_id}: {e}")
            return None

    async def get_property_stats(
        self,
        user_id: str,
        county_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about user's saved properties.

        Returns:
            Dict with counts by stage, total saved, etc.
        """
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            # Count saved properties by stage
            result = supabase.table("user_data").select(
                "kanban_stage"
            ).eq("user_id", user_id).eq("is_saved", True).execute()

            board = {stage: [] for stage in self.KANBAN_STAGES}
            for row in result.data:
                stage = row.get("kanban_stage", "researching")
                if stage in board:
                    board[stage].append(row)

            stats = {
                "total_saved": len(result.data) if result.data else 0,
                "by_stage": {stage: len(props) for stage, props in board.items()},
                "stages": board
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting property stats for user {user_id}: {e}")
            return {
                "total_saved": 0,
                "by_stage": {stage: 0 for stage in self.KANBAN_STAGES},
                "stages": {stage: [] for stage in self.KANBAN_STAGES}
            }

    async def bulk_update_stages(
        self,
        user_id: str,
        updates: List[Dict[str, Any]],
        county_id: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Bulk update Kanban stages for multiple properties.

        Args:
            user_id: User ID
            updates: List of {"saved_id": int, "new_stage": str}
            county_id: Optional county for feature check

        Returns:
            Dict with success/failed counts
        """
        # Check if Kanban feature is enabled
        kanban_enabled = await self.feature_service.is_feature_enabled(
            "kanban_board",
            user_id=user_id,
            county_id=county_id
        )

        if not kanban_enabled:
            logger.warning("Kanban board feature is disabled")
            return {"success": 0, "failed": 0, "total": len(updates)}

        success = 0
        failed = 0

        for update in updates:
            saved_id = update.get("saved_id")
            new_stage = update.get("new_stage")

            if not saved_id or not new_stage:
                failed += 1
                continue

            result = await self.update_kanban_stage(user_id, saved_id, new_stage)
            if result:
                success += 1
            else:
                failed += 1

        return {"success": success, "failed": failed, "total": len(updates)}

    async def archive_property(self, user_id: str, saved_id: int) -> Optional[Dict[str, Any]]:
        """Archive a saved property (move to archived stage)"""
        return await self.update_kanban_stage(user_id, saved_id, "archived")

    async def get_active_properties(
        self,
        user_id: str,
        county_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active (non-archived) saved properties.

        Returns properties in all stages except 'archived' and 'lost'
        """
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            # Get active stages (not archived, lost, or won)
            active_stages = ["researching", "analyzing", "due_diligence", "bidding"]

            query = supabase.table("user_data").select(
                "*, foreclosure_listings(*)"
            ).eq("user_id", user_id).eq("is_saved", True)

            # Filter by active stages
            kanban_enabled = await self.feature_service.is_feature_enabled(
                "kanban_board",
                user_id=user_id,
                county_id=county_id
            )

            if kanban_enabled:
                query = query.in_("kanban_stage", active_stages)

            query = query.order("created_at", desc=True)

            result = query.execute()

            return [self._format_saved_property(row) for row in result.data]

        except Exception as e:
            logger.error(f"Error fetching active properties for user {user_id}: {e}")
            return []
