"""
Collaboration Service

Manages team collaboration features:
- Property sharing between team members
- Comments on properties
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from .feature_toggle_service import FeatureToggleService

logger = logging.getLogger(__name__)

# Share types
SHARE_TYPES = ["view", "edit", "comment"]


class CollaborationService:
    """Service for team collaboration on properties"""

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
        """Check if team collaboration feature is enabled"""
        return await self.feature_service.is_feature_enabled(
            "team_collaboration",
            user_id=user_id,
            county_id=county_id,
            state=state
        )

    # ========================================================================
    # PROPERTY SHARING
    # ========================================================================

    async def share_property(
        self,
        property_id: int,
        shared_by_user_id: str,
        shared_with_user_id: str,
        share_type: str = "view",
        share_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Share a property with another user"""
        if not await self.is_feature_enabled(shared_by_user_id):
            raise PermissionError("Team collaboration feature not enabled")

        if share_type not in SHARE_TYPES:
            raise ValueError(f"Invalid share_type: {share_type}")

        # Check if already shared
        existing = await self._get_share(property_id, shared_by_user_id, shared_with_user_id)
        if existing:
            # Update share type (using correct column names)
            result = self.supabase.table("v2_shared_properties").update({
                "share_type": share_type,
                "share_message": share_message
            }).eq("id", existing["id"]).execute()
            if result.data:
                return result.data[0]

        share_data = {
            "property_id": property_id,
            "shared_by_user_id": shared_by_user_id,  # Database column is 'shared_by_user_id'
            "shared_with_user_id": shared_with_user_id,  # Database column is 'shared_with_user_id'
            "share_type": share_type,
            "share_message": share_message,
            "shared_at": datetime.utcnow().isoformat()
        }

        result = self.supabase.table("v2_shared_properties").insert(
            share_data
        ).execute()

        if not result.data:
            raise Exception("Failed to share property")

        logger.info(
            f"User {shared_by_user_id} shared property {property_id} "
            f"with user {shared_with_user_id} ({share_type})"
        )

        return result.data[0]

    async def unshare_property(
        self,
        share_id: int,
        user_id: str
    ) -> bool:
        """Remove a property share"""
        # Must be the original sharer to unshare
        existing = self.supabase.table("v2_shared_properties").select(
            "*"
        ).eq("id", share_id).eq("shared_by_user_id", user_id).execute()

        if not existing.data:
            raise PermissionError("Not authorized to unshare this property")

        result = self.supabase.table("v2_shared_properties").delete().eq(
            "id", share_id
        ).execute()

        deleted = len(result.data) > 0 if result.data else False

        if deleted:
            logger.info(f"User {user_id} unshared property (share_id: {share_id})")

        return deleted

    async def get_shared_with_me(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get properties shared with the user"""
        result = self.supabase.table("v2_shared_properties").select(
            "*, foreclosure_listings(*)"
        ).eq("shared_with_user_id", user_id).order("shared_at", desc=True).execute()

        return result.data if result.data else []

    async def get_shared_by_me(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get properties the user has shared with others"""
        result = self.supabase.table("v2_shared_properties").select(
            "*, foreclosure_listings(*)"
        ).eq("shared_by_user_id", user_id).order("shared_at", desc=True).execute()

        return result.data if result.data else []

    # ========================================================================
    # PROPERTY COMMENTS
    # ========================================================================

    async def add_comment(
        self,
        property_id: int,
        user_id: str,
        comment_text: str,
        parent_comment_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add a comment to a property"""
        if not await self.is_feature_enabled(user_id):
            raise PermissionError("Team collaboration feature not enabled")

        comment_data = {
            "property_id": property_id,
            "user_id": user_id,
            "comment_text": comment_text,
            "parent_comment_id": parent_comment_id,
            "is_deleted": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        result = self.supabase.table("v2_property_comments").insert(
            comment_data
        ).execute()

        if not result.data:
            raise Exception("Failed to add comment")

        logger.info(f"User {user_id} added comment to property {property_id}")
        return result.data[0]

    async def get_comments(
        self,
        property_id: int,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all comments for a property"""
        query = self.supabase.table("v2_property_comments").select(
            "*"
        ).eq("property_id", property_id).order("created_at", desc=True)

        if not include_deleted:
            query = query.eq("is_deleted", False)

        result = query.execute()
        return result.data if result.data else []

    async def update_comment(
        self,
        comment_id: int,
        user_id: str,
        comment_text: str
    ) -> Dict[str, Any]:
        """Update a comment"""
        # Verify ownership
        existing = self.supabase.table("v2_property_comments").select(
            "*"
        ).eq("id", comment_id).eq("user_id", user_id).execute()

        if not existing.data:
            raise PermissionError("Not authorized to update this comment")

        result = self.supabase.table("v2_property_comments").update({
            "comment_text": comment_text,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", comment_id).execute()

        if not result.data:
            raise Exception("Failed to update comment")

        logger.info(f"User {user_id} updated comment {comment_id}")
        return result.data[0]

    async def delete_comment(
        self,
        comment_id: int,
        user_id: str
    ) -> bool:
        """Soft delete a comment"""
        # Verify ownership
        existing = self.supabase.table("v2_property_comments").select(
            "*"
        ).eq("id", comment_id).eq("user_id", user_id).execute()

        if not existing.data:
            raise PermissionError("Not authorized to delete this comment")

        result = self.supabase.table("v2_property_comments").update({
            "is_deleted": True,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", comment_id).execute()

        deleted = len(result.data) > 0 if result.data else False

        if deleted:
            logger.info(f"User {user_id} deleted comment {comment_id}")

        return deleted

    async def _get_share(
        self,
        property_id: int,
        shared_by: str,
        shared_with: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing share record if exists"""
        result = self.supabase.table("v2_shared_properties").select(
            "*"
        ).eq("property_id", property_id).eq("shared_by_user_id", shared_by).eq(
            "shared_with_user_id", shared_with
        ).execute()

        return result.data[0] if result.data else None
