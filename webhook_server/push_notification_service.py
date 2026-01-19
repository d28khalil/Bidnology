"""
Push Notification Service

Mobile push notification system for iOS, Android, and Web using:
- Firebase Cloud Messaging (FCM) for Android
- Apple Push Notification Service (APNs) for iOS
- Web Push API for web browsers

Features:
- Device token registry with platform detection
- Notification queue with delivery tracking
- Template system for consistent messaging
- Quiet hours and notification preferences
- Batch sending support
"""

import os
import logging
import json
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from supabase import create_client, Client

# Lazy imports for APNs to avoid Python 3.12 compatibility issues with apns2/hyper
# These will only be imported when actually used
APNsClient = None
Notification = None
Payload = None

try:
    from apns2.client import APNsClient as _APNsClient, Notification as _Notification
    from apns2.payload import Payload as _Payload
    APNsClient = _APNsClient
    Notification = _Notification
    Payload = _Payload
except (ImportError, SyntaxError) as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"APNs2 library not available: {e}. Push notifications for iOS will be disabled.")
    logger = logging.getLogger(__name__)


class PushNotificationService:
    """
    Service for mobile push notifications.

    Supports iOS (APNs), Android (FCM), and Web Push.
    """

    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        # FCM configuration (Android)
        self.fcm_server_key = os.getenv("FCM_SERVER_KEY")
        self.fcm_endpoint = "https://fcm.googleapis.com/fcm/send"

        # APNs configuration (iOS)
        # Use certificate path OR token authentication
        self.apns_cert_path = os.getenv("APNS_CERT_PATH")  # Path to .pem certificate
        self.apns_key_id = os.getenv("APNS_KEY_ID")
        self.apns_team_id = os.getenv("APNS_TEAM_ID")
        self.apns_bundle_id = os.getenv("APNS_BUNDLE_ID", "com.yourapp.bundle")  # iOS Bundle ID
        self.apns_auth_key_path = os.getenv("APNS_AUTH_KEY_PATH")  # Path to .p8 key file
        self.apns_use_sandbox = os.getenv("APNS_USE_SANDBOX", "false").lower() == "true"

        # APNs client (lazy init)
        self._apns_client: Optional[APNsClient] = None

    def _get_apns_client(self) -> Optional[APNsClient]:
        """Get or create APNs client (lazy initialization)"""
        if self._apns_client:
            return self._apns_client

        # Try certificate-based auth first
        if self.apns_cert_path and os.path.exists(self.apns_cert_path):
            self._apns_client = APNsClient(
                self.apns_cert_path,
                use_sandbox=self.apns_use_sandbox
            )
            logger.info("APNs client initialized with certificate")
            return self._apns_client

        # Try token-based auth
        if (self.apns_auth_key_path and os.path.exists(self.apns_auth_key_path) and
            self.apns_key_id and self.apns_team_id):
            self._apns_client = APNsClient(
                self.apns_auth_key_path,
                use_sandbox=self.apns_use_sandbox,
                key_id=self.apns_key_id,
                team_id=self.apns_team_id
            )
            logger.info("APNs client initialized with token auth")
            return self._apns_client

        logger.warning("APNs client cannot be initialized - no credentials configured")
        return None

    async def close(self):
        """Close connections (call when shutting down)"""
        if self._apns_client:
            # APNsClient doesn't have explicit close, but we can clear the reference
            self._apns_client = None

    # ========================================================================
    # DEVICE TOKEN MANAGEMENT
    # ========================================================================

    async def register_device_token(
        self,
        user_id: str,
        device_token: str,
        platform: str,
        device_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a device token for push notifications.

        Args:
            user_id: User ID
            device_token: Device token from FCM/APNs
            platform: 'ios', 'android', or 'web'
            device_info: Optional device metadata

        Returns:
            Created/updated token record
        """
        # Check if token exists
        existing = self.supabase.table("v2_mobile_push_tokens").select(
            "*"
        ).eq("user_id", user_id).eq("device_token", device_token).execute()

        token_data = {
            "user_id": user_id,
            "device_token": device_token,
            "platform": platform.lower(),
            "device_info": device_info or {},
            "last_used_at": datetime.utcnow().isoformat(),
            "is_active": True
        }

        if existing.data:
            # Update existing
            result = self.supabase.table("v2_mobile_push_tokens").update(
                token_data
            ).eq("id", existing.data[0]["id"]).execute()
            logger.info(f"Updated device token for user {user_id} ({platform})")
        else:
            # Insert new
            result = self.supabase.table("v2_mobile_push_tokens").insert(
                token_data
            ).execute()
            logger.info(f"Registered new device token for user {user_id} ({platform})")

        return result.data[0] if result.data else {}

    async def unregister_device_token(
        self,
        token_id: int,
        user_id: str
    ) -> bool:
        """Remove a device token (user opts out)"""
        result = self.supabase.table("v2_mobile_push_tokens").update({
            "is_active": False
        }).eq("id", token_id).eq("user_id", user_id).execute()

        logger.info(f"Unregistered device token {token_id} for user {user_id}")
        return bool(result.data)

    async def get_user_tokens(
        self,
        user_id: str,
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active device tokens for a user"""
        query = self.supabase.table("v2_mobile_push_tokens").select(
            "*"
        ).eq("user_id", user_id).eq("is_active", True)

        if platform:
            query = query.eq("platform", platform.lower())

        result = query.execute()
        return result.data if result.data else []

    # ========================================================================
    # NOTIFICATION CREATION
    # ========================================================================

    async def create_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        body: str,
        property_id: Optional[int] = None,
        deep_link: Optional[str] = None,
        custom_data: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        scheduled_for: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create a push notification in the queue.

        Args:
            user_id: Target user
            notification_type: Type (hot_deal, price_drop, etc.)
            title: Notification title
            body: Notification body
            property_id: Related property (optional)
            deep_link: Deep link for tap action
            custom_data: Additional payload data
            priority: low, normal, high, urgent
            scheduled_for: When to send (None = immediate)

        Returns:
            Created queue record
        """
        # Check quiet hours
        if await self._is_in_quiet_hours(user_id):
            logger.info(f"User {user_id} is in quiet hours, scheduling for later")
            # Schedule for after quiet hours
            scheduled_for = await self._calculate_after_quiet_hours(user_id)

        notification_data = {
            "user_id": user_id,
            "property_id": property_id,
            "notification_type": notification_type,
            "title": title,
            "body": body,
            "deep_link": deep_link,
            "custom_data": custom_data or {},
            "priority": priority,
            "status": "pending",
            "scheduled_for": (scheduled_for or datetime.utcnow()).isoformat()
        }

        result = self.supabase.table("v2_push_notification_queue").insert(
            notification_data
        ).execute()

        logger.info(
            f"Created {notification_type} notification for user {user_id}: "
            f"{title[:50]}..."
        )

        return result.data[0] if result.data else {}

    async def create_from_template(
        self,
        user_id: str,
        template_key: str,
        variables: Dict[str, str],
        property_id: Optional[int] = None,
        priority: str = "normal",
        scheduled_for: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create notification from template using the database function.

        Args:
            user_id: Target user
            template_key: Template identifier
            variables: Variable substitutions
            property_id: Related property
            priority: Priority level
            scheduled_for: When to send

        Returns:
            Created notification or None if template not found
        """
        # Call the database function
        result = self.supabase.rpc(
            "create_notification_from_template",
            params={
                "p_user_id": user_id,
                "p_template_key": template_key,
                "p_property_id": property_id,
                "p_variables": variables,
                "p_priority": priority,
                "p_scheduled_for": (scheduled_for or datetime.utcnow()).isoformat()
            }
        ).execute()

        if result.data:
            logger.info(
                f"Created notification from template '{template_key}' "
                f"for user {user_id}"
            )
            return {"queue_id": result.data, "template_key": template_key}

        logger.warning(f"Template '{template_key}' not found or inactive")
        return None

    async def create_batch_notifications(
        self,
        user_ids: List[str],
        notification_type: str,
        title: str,
        body: str,
        property_id: Optional[int] = None,
        deep_link: Optional[str] = None,
        priority: str = "normal"
    ) -> List[Dict[str, Any]]:
        """
        Create notifications for multiple users (batch).

        Returns list of created notifications.
        """
        import uuid

        batch_id = str(uuid.uuid4())
        results = []

        for user_id in user_ids:
            try:
                result = await self.create_notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    body=body,
                    property_id=property_id,
                    deep_link=deep_link,
                    priority=priority
                )

                # Update with batch ID
                if result.get("id"):
                    self.supabase.table("v2_push_notification_queue").update({
                        "batch_id": batch_id
                    }).eq("id", result["id"]).execute()

                results.append(result)
            except Exception as e:
                logger.error(f"Failed to create notification for user {user_id}: {e}")

        logger.info(f"Created batch {batch_id} with {len(results)} notifications")
        return results

    # ========================================================================
    # NOTIFICATION SENDING
    # ========================================================================

    async def send_pending_notifications(
        self,
        limit: int = 100
    ) -> Dict[str, int]:
        """
        Send pending notifications from the queue.

        This would typically be called by a background worker/cron job.

        Returns:
            Stats on sent/failed notifications
        """
        # Get pending notifications that are due
        now = datetime.utcnow().isoformat()
        result = self.supabase.table("v2_push_notification_queue").select(
            "*"
        ).eq("status", "pending").lte(
            "scheduled_for", now
        ).order("priority", desc=False).limit(limit).execute()

        if not result.data:
            return {"sent": 0, "failed": 0, "skipped": 0}

        stats = {"sent": 0, "failed": 0, "skipped": 0}

        for notification in result.data:
            try:
                success = await self._send_notification(notification)

                if success:
                    stats["sent"] += 1
                else:
                    stats["failed"] += 1

            except Exception as e:
                logger.error(f"Error sending notification {notification['id']}: {e}")
                stats["failed"] += 1

        logger.info(f"Sent {stats['sent']}, failed {stats['failed']}, skipped {stats['skipped']}")
        return stats

    async def _send_notification(
        self,
        notification: Dict[str, Any]
    ) -> bool:
        """Send a single notification to the user's devices"""
        user_id = notification["user_id"]
        notification_id = notification["id"]

        # Get user's active device tokens
        tokens = await self.get_user_tokens(user_id)

        if not tokens:
            logger.warning(f"No active tokens for user {user_id}")
            await self._mark_notification_failed(
                notification_id, "No active device tokens"
            )
            return False

        # Check notification preferences per token
        eligible_tokens = []
        for token in tokens:
            if await self._check_notification_preferences(
                token, notification["notification_type"]
            ):
                eligible_tokens.append(token)

        if not eligible_tokens:
            logger.info(f"No eligible tokens for user {user_id} (preferences)")
            await self._mark_notification_failed(
                notification_id, "No tokens matching notification preferences"
            )
            return False

        # Mark as sending
        self.supabase.table("v2_push_notification_queue").update({
            "status": "sending",
            "sent_at": datetime.utcnow().isoformat()
        }).eq("id", notification_id).execute()

        # Send to each platform
        success_count = 0

        for token in eligible_tokens:
            try:
                if token["platform"] == "android":
                    success = await self._send_fcm(notification, token)
                elif token["platform"] == "ios":
                    success = await self._send_apns(notification, token)
                elif token["platform"] == "web":
                    success = await self._send_web_push(notification, token)
                else:
                    success = False

                if success:
                    success_count += 1

            except Exception as e:
                logger.error(f"Error sending to {token['platform']}: {e}")

        # Update status based on results
        if success_count > 0:
            await self._mark_notification_sent(notification_id)
            return True
        else:
            await self._mark_notification_failed(notification_id, "All sends failed")
            return False

    async def _send_fcm(
        self,
        notification: Dict[str, Any],
        token: Dict[str, Any]
    ) -> bool:
        """Send notification via Firebase Cloud Messaging (Android)"""
        if not self.fcm_server_key:
            logger.warning("FCM server key not configured")
            return False

        headers = {
            "Authorization": f"key={self.fcm_server_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "to": token["device_token"],
            "notification": {
                "title": notification["title"],
                "body": notification["body"],
                "sound": "default"
            },
            "data": {
                "property_id": str(notification.get("property_id", "")),
                "deep_link": notification.get("deep_link", ""),
                "notification_id": str(notification["id"]),
                **notification.get("custom_data", {})
            },
            "priority": "high" if notification.get("priority") in ["high", "urgent"] else "normal"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.fcm_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", 0) > 0:
                        logger.debug(f"FCM sent successfully to {token['device_token'][:20]}...")
                        return True
                    else:
                        error = result.get("results", [{}])[0].get("error", "Unknown")
                        logger.warning(f"FCM error: {error}")
                        return False
                else:
                    logger.error(f"FCM HTTP error: {response.status_code}")
                    return False

            except Exception as e:
                logger.error(f"FCM send error: {e}")
                return False

    async def _send_apns(
        self,
        notification: Dict[str, Any],
        token: Dict[str, Any]
    ) -> bool:
        """Send notification via Apple Push Notification Service (iOS)"""
        client = self._get_apns_client()
        if not client:
            logger.warning("APNs client not configured - skipping iOS notification")
            return False

        try:
            # Build custom data for the notification
            custom_data = {
                "property_id": str(notification.get("property_id", "")),
                "deep_link": notification.get("deep_link", ""),
                "notification_id": str(notification["id"]),
                **notification.get("custom_data", {})
            }

            # Create APNs payload
            payload = Payload(
                alert={
                    "title": notification["title"],
                    "body": notification["body"]
                },
                sound="default",
                badge=1,
                custom=custom_data
            )

            # Create notification
            apns_notification = Notification(
                token=token["device_token"],
                payload=payload
            )

            # Set priority based on notification priority
            priority = 10 if notification.get("priority") in ["high", "urgent"] else 5

            # Send notification
            client.send_notification(
                apns_notification,
                topic=self.apns_bundle_id,  # Bundle ID (iOS app identifier)
                priority=priority
            )

            logger.debug(f"APNs sent successfully to {token['device_token'][:20]}...")
            return True

        except Exception as e:
            error_msg = str(e)
            logger.error(f"APNs send error: {error_msg}")

            # Handle common errors
            if "Unregistered" in error_msg or "BadDeviceToken" in error_msg:
                # Token is no longer valid - mark as inactive
                logger.warning(f"Invalid APNs token - deactivating {token['device_token'][:20]}...")
                self.supabase.table("v2_mobile_push_tokens").update({
                    "is_active": False
                }).eq("device_token", token["device_token"]).execute()

            return False

    async def _send_web_push(
        self,
        notification: Dict[str, Any],
        token: Dict[str, Any]
    ) -> bool:
        """Send notification via Web Push API"""
        # Note: Web Push requires VAPID keys and subscription object
        # This is a simplified placeholder

        logger.info(f"Web Push not yet fully implemented for token {token['device_token'][:20]}...")
        return False

    # ========================================================================
    # NOTIFICATION STATUS UPDATES
    # ========================================================================

    async def _mark_notification_sent(
        self,
        notification_id: int
    ):
        """Mark notification as sent"""
        self.supabase.table("v2_push_notification_queue").update({
            "status": "sent",
            "delivered_at": datetime.utcnow().isoformat()
        }).eq("id", notification_id).execute()

        # Also add to history
        await self._archive_to_history(notification_id, "sent")

    async def _mark_notification_failed(
        self,
        notification_id: int,
        error_message: str
    ):
        """Mark notification as failed"""
        self.supabase.table("v2_push_notification_queue").update({
            "status": "failed",
            "error_message": error_message,
            "retry_count": self.supabase.table("v2_push_notification_queue").select(
                "retry_count"
            ).eq("id", notification_id).execute().data[0]["retry_count"] + 1 if self.supabase.table(
                "v2_push_notification_queue"
            ).select("retry_count").eq("id", notification_id).execute().data else 1
        }).eq("id", notification_id).execute()

    async def _archive_to_history(
        self,
        queue_id: int,
        status: str
    ):
        """Archive notification to history table"""
        # Get queue record
        queue_result = self.supabase.table("v2_push_notification_queue").select(
            "*"
        ).eq("id", queue_id).execute()

        if not queue_result.data:
            return

        queue = queue_result.data[0]
        user_id = queue["user_id"]

        # Count devices
        tokens = await self.get_user_tokens(user_id)
        device_count = len(tokens)

        history = {
            "queue_id": queue_id,
            "user_id": user_id,
            "property_id": queue.get("property_id"),
            "notification_type": queue["notification_type"],
            "title": queue["title"],
            "body": queue["body"],
            "status": status,
            "device_count": device_count,
            "sent_at": queue.get("sent_at"),
            "delivered_at": queue.get("delivered_at")
        }

        self.supabase.table("push_notification_history").insert(
            history
        ).execute()

    # ========================================================================
    # NOTIFICATION PREFERENCES
    # ========================================================================

    async def update_notification_preferences(
        self,
        token_id: int,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update notification preferences for a device"""
        # Validate input
        valid_fields = {
            "enable_hot_deals", "enable_auction_updates",
            "enable_price_drops", "enable_status_changes",
            "enable_watchlist_alerts", "enable_comps_available",
            "enable_marketing_updates",
            "quiet_hours_enabled", "quiet_hours_start",
            "quiet_hours_end", "quiet_timezone"
        }

        update_data = {
            k: v for k, v in preferences.items()
            if k in valid_fields
        }

        result = self.supabase.table("v2_mobile_push_tokens").update(
            update_data
        ).eq("id", token_id).eq("user_id", user_id).execute()

        return result.data[0] if result.data else {}

    async def _check_notification_preferences(
        self,
        token: Dict[str, Any],
        notification_type: str
    ) -> bool:
        """Check if token allows this notification type"""
        mapping = {
            "hot_deal": "enable_hot_deals",
            "auction_reminder": "enable_auction_updates",
            "price_drop": "enable_price_drops",
            "status_change": "enable_status_changes",
            "watchlist_alert": "enable_watchlist_alerts",
            "comps_available": "enable_comps_available",
            "marketing": "enable_marketing_updates"
        }

        field = mapping.get(notification_type)
        if field:
            return token.get(field, True)  # Default to enabled

        return True

    async def _is_in_quiet_hours(
        self,
        user_id: str
    ) -> bool:
        """Check if user is currently in quiet hours"""
        result = self.supabase.rpc(
            "is_in_quiet_hours",
            params={"p_user_id": user_id}
        ).execute()

        return result.data if result.data is not None else False

    async def _calculate_after_quiet_hours(
        self,
        user_id: str
    ) -> datetime:
        """Calculate next time after quiet hours to send notification"""
        tokens = await self.get_user_tokens(user_id)

        if not tokens:
            return datetime.utcnow() + timedelta(hours=1)

        token = tokens[0]
        end_time = token.get("quiet_hours_end")
        timezone = token.get("quiet_timezone", "America/New_York")

        if not end_time:
            return datetime.utcnow() + timedelta(hours=1)

        # Simplified: add 1 hour to current time
        # In production, would properly convert timezones
        return datetime.utcnow() + timedelta(hours=1)

    # ========================================================================
    # NOTIFICATION HISTORY & ANALYTICS
    # ========================================================================

    async def get_notification_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get notification history for a user"""
        result = self.supabase.table("push_notification_history").select(
            "*"
        ).eq("user_id", user_id).order(
            "created_at", desc=True
        ).limit(limit).execute()

        return result.data if result.data else []

    async def mark_notification_opened(
        self,
        notification_id: int,
        user_id: str
    ) -> bool:
        """Mark notification as opened by user"""
        # Update queue
        queue_result = self.supabase.table("v2_push_notification_queue").update({
            "opened_at": datetime.utcnow().isoformat()
        }).eq("id", notification_id).execute()

        # Update history
        history_result = self.supabase.table("push_notification_history").update({
            "opened_at": datetime.utcnow().isoformat()
        }).eq("queue_id", notification_id).execute()

        return bool(queue_result.data or history_result.data)
