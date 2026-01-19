"""
Watchlist & Alerts Service

Manages property watchlists and creates alerts when properties change.
Now uses the consolidated user_data table.

The user_data table watchlist fields:
- is_watched: Boolean flag
- watch_priority: low, normal, high, urgent
- alert_on_price_change, alert_on_status_change, alert_on_new_comps, alert_on_auction_near
- auction_alert_days: Days before auction to alert
- watch_notes: Optional notes

Users can watch properties and receive notifications for:
- Price changes
- Status changes
- New comparable properties
- Auction date approaching
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from supabase import create_client, Client
from .feature_toggle_service import FeatureToggleService

logger = logging.getLogger(__name__)


class WatchlistService:
    """Service for managing property watchlists and alerts using user_data table"""

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
        """Check if watchlist feature is enabled"""
        return await self.feature_service.is_feature_enabled(
            "watchlist_alerts",
            user_id=user_id,
            county_id=county_id,
            state=state
        )

    # ========================================================================
    # WATCHLIST MANAGEMENT
    # ========================================================================

    async def add_to_watchlist(
        self,
        user_id: str,
        property_id: int,
        alert_on_price_change: bool = True,
        alert_on_status_change: bool = True,
        alert_on_new_comps: bool = False,
        alert_on_auction_near: bool = False,
        auction_alert_days: int = 7,
        watch_notes: Optional[str] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Add a property to user's watchlist.

        Args:
            user_id: User ID
            property_id: Property ID
            alert_on_price_change: Alert when price changes
            alert_on_status_change: Alert when status changes
            alert_on_new_comps: Alert when new comps available
            alert_on_auction_near: Alert before auction date
            auction_alert_days: Days before auction to alert
            watch_notes: Optional notes about this watch
            priority: Priority level (low, normal, high, urgent)

        Returns:
            Created or updated watchlist entry
        """
        # Validate feature is enabled
        if not await self.is_feature_enabled(user_id):
            raise PermissionError("Watchlist feature is not enabled")

        # Validate priority
        valid_priorities = ["low", "normal", "high", "urgent"]
        if priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {priority}. Must be one of {valid_priorities}")

        # Check if already watching (by checking user_data entry)
        existing = await self._get_watchlist_entry(user_id, property_id)

        current_time = datetime.utcnow().isoformat()

        if existing:
            # Update existing user_data entry
            update_data = {
                "is_watched": True,
                "watch_priority": priority,
                "alert_on_price_change": alert_on_price_change,
                "alert_on_status_change": alert_on_status_change,
                "alert_on_new_comps": alert_on_new_comps,
                "alert_on_auction_near": alert_on_auction_near,
                "auction_alert_days": auction_alert_days,
                "watch_notes": watch_notes,
                "updated_at": current_time
            }

            result = self.supabase.table("user_data").update(
                update_data
            ).eq("id", existing["id"]).execute()

            logger.info(f"Updated watchlist entry for user {user_id}, property {property_id}")
            return result.data[0] if result.data else existing

        # Create new user_data entry
        insert_data = {
            "user_id": user_id,
            "property_id": property_id,
            "is_watched": True,
            "watch_priority": priority,
            "alert_on_price_change": alert_on_price_change,
            "alert_on_status_change": alert_on_status_change,
            "alert_on_new_comps": alert_on_new_comps,
            "alert_on_auction_near": alert_on_auction_near,
            "auction_alert_days": auction_alert_days,
            "watch_notes": watch_notes,
            "created_at": current_time,
            "updated_at": current_time
        }

        result = self.supabase.table("user_data").insert(insert_data).execute()

        if not result.data:
            raise Exception("Failed to add to watchlist")

        logger.info(f"User {user_id} added property {property_id} to watchlist")
        return result.data[0]

    async def remove_from_watchlist(
        self,
        user_id: str,
        property_id: int
    ) -> bool:
        """
        Remove a property from user's watchlist.

        Instead of deleting, sets is_watched to False to preserve other data.

        Args:
            user_id: User ID
            property_id: Property ID

        Returns:
            True if removed, False if not found
        """
        result = self.supabase.table("user_data").update({
            "is_watched": False,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).eq("property_id", property_id).execute()

        deleted = len(result.data) > 0 if result.data else False

        if deleted:
            logger.info(f"User {user_id} removed property {property_id} from watchlist")

        return deleted

    async def get_watchlist(
        self,
        user_id: str,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's watchlist with property details.

        Args:
            user_id: User ID
            priority: Optional priority filter

        Returns:
            List of watchlist entries with full property details
        """
        # Query user_data with property details
        query = self.supabase.table("user_data").select(
            "*, foreclosure_listings(*)"
        ).eq("user_id", user_id).eq("is_watched", True).order("created_at", desc=True)

        if priority:
            query = query.eq("watch_priority", priority)

        result = query.execute()

        return result.data if result.data else []

    async def update_watchlist_entry(
        self,
        user_id: str,
        property_id: int,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a watchlist entry.

        Args:
            user_id: User ID
            property_id: Property ID
            updates: Fields to update

        Returns:
            Updated watchlist entry or None if not found
        """
        existing = await self._get_watchlist_entry(user_id, property_id)
        if not existing:
            return None

        # Add updated_at timestamp
        updates["updated_at"] = datetime.utcnow().isoformat()

        result = self.supabase.table("user_data").update(
            updates
        ).eq("id", existing["id"]).execute()

        return result.data[0] if result.data else None

    # ========================================================================
    # ALERTS
    # ========================================================================

    async def get_alerts(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get alerts for a user.

        Args:
            user_id: User ID
            unread_only: Only return unread alerts
            limit: Maximum number of alerts

        Returns:
            List of alerts
        """
        query = self.supabase.table("user_alerts").select(
            "*, foreclosure_listings(*)"
        ).eq("user_id", user_id).order("created_at", desc=True).limit(limit)

        if unread_only:
            query = query.eq("is_read", False)

        result = query.execute()

        return result.data if result.data else []

    async def mark_alert_read(
        self,
        alert_id: int,
        user_id: str
    ) -> bool:
        """
        Mark an alert as read.

        Args:
            alert_id: Alert ID
            user_id: User ID (for authorization)

        Returns:
            True if marked read, False if not found
        """
        result = self.supabase.table("user_alerts").update({
            "is_read": True,
            "read_at": datetime.utcnow().isoformat()
        }).eq("id", alert_id).eq("user_id", user_id).execute()

        return len(result.data) > 0 if result.data else False

    async def mark_all_alerts_read(
        self,
        user_id: str
    ) -> int:
        """
        Mark all alerts as read for a user.

        Args:
            user_id: User ID

        Returns:
            Number of alerts marked as read
        """
        result = self.supabase.table("user_alerts").update({
            "is_read": True,
            "read_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).eq("is_read", False).execute()

        return len(result.data) if result.data else 0

    async def delete_alert(
        self,
        alert_id: int,
        user_id: str
    ) -> bool:
        """
        Delete an alert.

        Args:
            alert_id: Alert ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        result = self.supabase.table("user_alerts").delete().eq(
            "id", alert_id
        ).eq("user_id", user_id).execute()

        return len(result.data) > 0 if result.data else False

    # ========================================================================
    # ALERT TRIGGERING (Called by other services)
    # ========================================================================

    async def trigger_price_change_alert(
        self,
        property_id: int,
        old_price: float,
        new_price: float
    ):
        """
        Trigger alerts for watchlisted users when price changes.

        This should be called when a property's price is updated.
        """
        # Get all watchlist entries for this property
        watchlist_entries = await self._get_watchlist_for_property(property_id)

        for entry in watchlist_entries:
            if not entry.get("alert_on_price_change"):
                continue

            price_diff = new_price - old_price
            price_diff_percent = (price_diff / old_price * 100) if old_price > 0 else 0

            direction = "increased" if price_diff > 0 else "decreased"
            title = f"Price {'Increased' if price_diff > 0 else 'Decreased'} for Property"

            message = (
                f"The price for this property has {direction} by "
                f"${abs(price_diff):,.0f} ({abs(price_diff_percent):.1f}%). "
                f"Old price: ${old_price:,.0f}, New price: ${new_price:,.0f}"
            )

            await self._create_alert(
                user_id=entry["user_id"],
                property_id=property_id,
                alert_type="price_change",
                title=title,
                message=message,
                action_url=f"/property/{property_id}"
            )

        logger.info(
            f"Triggered price change alerts for property {property_id}: "
            f"{old_price:,.0f} -> {new_price:,.0f} ({len(watchlist_entries)} watchers)"
        )

    async def trigger_status_change_alert(
        self,
        property_id: int,
        old_status: str,
        new_status: str
    ):
        """
        Trigger alerts for watchlisted users when status changes.

        This should be called when a property's status is updated.
        """
        watchlist_entries = await self._get_watchlist_for_property(property_id)

        for entry in watchlist_entries:
            if not entry.get("alert_on_status_change"):
                continue

            title = f"Status Update: {new_status.replace('_', ' ').title()}"
            message = (
                f"Property status has changed from {old_status.replace('_', ' ')} "
                f"to {new_status.replace('_', ' ')}"
            )

            await self._create_alert(
                user_id=entry["user_id"],
                property_id=property_id,
                alert_type="status_change",
                title=title,
                message=message,
                action_url=f"/property/{property_id}"
            )

        logger.info(
            f"Triggered status change alerts for property {property_id}: "
            f"{old_status} -> {new_status} ({len(watchlist_entries)} watchers)"
        )

    async def trigger_auction_reminder_alert(
        self,
        property_id: int,
        sale_date: str
    ):
        """
        Trigger alerts for watchlisted users when auction is approaching.

        This should be called periodically (e.g., daily) to check for
        upcoming auctions.
        """
        from datetime import datetime

        try:
            sale_datetime = datetime.fromisoformat(sale_date.replace("Z", "+00:00"))
            days_until = (sale_datetime - datetime.now()).days

            if days_until <= 0:
                return  # Auction has passed

        except (ValueError, TypeError) as date_err:
            logger.error(f"Invalid sale_date format for property {property_id}: {sale_date} - {date_err}")
            return

        watchlist_entries = await self._get_watchlist_for_property(property_id)

        for entry in watchlist_entries:
            if not entry.get("alert_on_auction_near"):
                continue

            alert_days = entry.get("auction_alert_days", 7)

            if days_until <= alert_days:
                title = f"Auction in {days_until} Day{'s' if days_until != 1 else ''}"
                message = (
                    f"This property's sheriff sale auction is scheduled for "
                    f"{sale_datetime.strftime('%B %d, %Y')} ({days_until} days from now)"
                )

                await self._create_alert(
                    user_id=entry["user_id"],
                    property_id=property_id,
                    alert_type="auction_reminder",
                    title=title,
                    message=message,
                    action_url=f"/property/{property_id}"
                )

        logger.info(
            f"Triggered auction reminder alerts for property {property_id}: "
            f"{days_until} days until auction ({len(watchlist_entries)} watchers)"
        )

    async def trigger_new_comps_alert(
        self,
        property_id: int,
        comp_count: int
    ):
        """
        Trigger alerts for watchlisted users when new comps are available.

        This should be called when comparable properties analysis is updated.
        """
        watchlist_entries = await self._get_watchlist_for_property(property_id)

        for entry in watchlist_entries:
            if not entry.get("alert_on_new_comps"):
                continue

            title = f"{comp_count} New Comparable Properties"
            message = f"New comparable sales data is available for this property ({comp_count} comps)"

            await self._create_alert(
                user_id=entry["user_id"],
                property_id=property_id,
                alert_type="new_comps",
                title=title,
                message=message,
                action_url=f"/property/{property_id}/comps"
            )

        logger.info(
            f"Triggered new comps alerts for property {property_id}: "
            f"{comp_count} comps ({len(watchlist_entries)} watchers)"
        )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _get_watchlist_entry(
        self,
        user_id: str,
        property_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get a watchlist entry from user_data or None"""
        result = self.supabase.table("user_data").select("*").eq(
            "user_id", user_id
        ).eq("property_id", property_id).execute()

        return result.data[0] if result.data else None

    async def _get_watchlist_for_property(
        self,
        property_id: int
    ) -> List[Dict[str, Any]]:
        """Get all watchlist entries for a property from user_data"""
        result = self.supabase.table("user_data").select("*").eq(
            "property_id", property_id
        ).eq("is_watched", True).execute()

        return result.data if result.data else []

    async def _is_watching(
        self,
        user_id: str,
        property_id: int
    ) -> bool:
        """Check if user is watching a property"""
        existing = await self._get_watchlist_entry(user_id, property_id)
        return existing is not None and existing.get("is_watched", False)

    async def _create_alert(
        self,
        user_id: str,
        property_id: int,
        alert_type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None
    ):
        """Create an alert for a user in user_alerts table (unchanged)"""
        insert_data = {
            "user_id": user_id,
            "property_id": property_id,
            "alert_type": alert_type,
            "alert_title": title,
            "alert_message": message,
            "action_url": action_url,
            "created_at": datetime.utcnow().isoformat()
        }

        result = self.supabase.table("user_alerts").insert(insert_data).execute()

        if result.data:
            logger.info(f"Created alert for user {user_id}: {title}")
        else:
            logger.error(f"Failed to create alert for user {user_id}: {title}")
