"""
Feature Toggle Service - Three-Tier Feature Resolution for Deal Intelligence

Implements feature toggle resolution with lock logic:
Admin Settings (Global) → County Settings (Per-County) → User Preferences (Per-User)

Lock flags prevent overrides at lower levels.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from supabase import create_client, Client

logger = logging.getLogger(__name__)


@dataclass
class ResolvedFeatures:
    """Result of feature resolution"""
    # Feature flags
    features: Dict[str, bool]
    # AI quality thresholds
    ai_thresholds: Dict[str, Any]
    # Metadata
    sources: Dict[str, str] = None  # Track where each value came from


class FeatureToggleService:
    """Service for resolving and managing deal intelligence feature toggles"""

    # All 12 feature names
    FEATURES = [
        "market_anomaly_detection",
        "comparable_sales_analysis",
        "renovation_cost_estimator",
        "investment_strategies",
        "watchlist_alerts",
        "portfolio_tracking",
        "team_collaboration",
        "mobile_notifications",
        "notes_checklist",
        "export_csv",
        "save_property",
        "kanban_board"
    ]

    # AI quality threshold names
    AI_THRESHOLDS = [
        # Market anomaly thresholds
        "anomaly_min_comps",
        "anomaly_min_confidence",
        "anomaly_max_zscore",
        "anomaly_min_price_diff_percent",
        # Comps analysis thresholds
        "comps_analysis_min_samples",
        "comps_analysis_max_distance_miles",
        "comps_analysis_max_age_days",
        "comps_analysis_min_similarity_score",
        # Renovation estimator thresholds
        "renovation_min_photos",
        "renovation_confidence_threshold"
    ]

    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

    # =========================================================================
    # FEATURE RESOLUTION
    # =========================================================================

    async def is_feature_enabled(
        self,
        feature: str,
        user_id: Optional[str] = None,
        county_id: Optional[int] = None,
        state: Optional[str] = None
    ) -> bool:
        """
        Check if a specific feature is enabled.
        Uses three-tier resolution: User > County > Admin
        Respects lock flags at each level.

        Args:
            feature: Feature name (e.g., "market_anomaly_detection")
            user_id: Optional user ID for user-level preferences
            county_id: Optional county ID for county-level overrides
            state: State code (required for county settings)

        Returns:
            True if feature is enabled, False otherwise
        """
        if feature not in self.FEATURES:
            logger.warning(f"Unknown feature requested: {feature}")
            return False

        resolved = await self.resolve_features(user_id, county_id, state)
        return resolved.features.get(feature, False)

    async def resolve_features(
        self,
        user_id: Optional[str] = None,
        county_id: Optional[int] = None,
        state: Optional[str] = None
    ) -> ResolvedFeatures:
        """
        Resolve all feature flags with priority: User > County > Admin
        Respects lock flags at each level.

        Returns:
            ResolvedFeatures with all features and AI thresholds
        """
        # Fetch all three levels
        admin_settings = await self.get_admin_settings()
        county_settings = await self.get_county_settings(county_id) if county_id else None
        user_prefs = await self.get_user_preferences(user_id) if user_id else None

        # Resolve features with lock logic
        features = {}
        sources = {}

        for feature in self.FEATURES:
            feature_key = f"feature_{feature}"
            lock_key = f"feature_lock_{feature}"

            # Check admin lock
            admin_locked = admin_settings.get(lock_key, False)

            if admin_locked:
                # Use admin value, ignore county/user
                features[feature] = admin_settings.get(feature_key, False)
                sources[feature_key] = "admin_locked"

            elif user_prefs:
                # Check county lock
                county_locked = county_settings.get(lock_key, False) if county_settings else False

                if county_locked:
                    # Use county value, ignore user
                    features[feature] = county_settings.get(
                        feature_key,
                        admin_settings.get(feature_key, False)
                    )
                    sources[feature_key] = "county_locked"

                else:
                    # User can override
                    features[feature] = self._coalesce_value(
                        feature_key,
                        user_prefs,
                        county_settings,
                        admin_settings,
                        default=False
                    )
                    if user_prefs.get(feature_key) is not None:
                        sources[feature_key] = "user"
                    elif county_settings and county_settings.get(feature_key) is not None:
                        sources[feature_key] = "county"
                    else:
                        sources[feature_key] = "admin"

            elif county_settings:
                # County can override admin (unless locked)
                features[feature] = county_settings.get(
                    feature_key,
                    admin_settings.get(feature_key, False)
                )
                sources[feature_key] = "county" if county_settings.get(feature_key) is not None else "admin"

            else:
                # Use admin default
                features[feature] = admin_settings.get(feature_key, False)
                sources[feature_key] = "admin"

        # Resolve AI thresholds (from admin only - these are global quality controls)
        ai_thresholds = {}
        for threshold in self.AI_THRESHOLDS:
            ai_thresholds[threshold] = admin_settings.get(threshold)

        return ResolvedFeatures(
            features=features,
            ai_thresholds=ai_thresholds,
            sources=sources
        )

    def _coalesce_value(
        self,
        field: str,
        user_prefs: Optional[Dict],
        county_settings: Optional[Dict],
        admin_settings: Dict,
        default: Any = None
    ) -> Any:
        """Get value with priority: user > county > admin > default"""
        if user_prefs and user_prefs.get(field) is not None:
            return user_prefs[field]
        if county_settings and county_settings.get(field) is not None:
            return county_settings[field]
        if admin_settings.get(field) is not None:
            return admin_settings[field]
        return default

    # =========================================================================
    # FETCH SETTINGS
    # =========================================================================

    async def get_admin_settings(self) -> Dict:
        """Get admin settings (singleton row with id=1)"""
        result = self.supabase.table("deal_features_admin_settings").select("*").eq("id", 1).execute()

        if not result.data:
            logger.warning("Admin settings not found, using defaults")
            return self._get_default_admin_settings()

        return result.data[0]

    async def get_county_settings(self, county_id: int) -> Optional[Dict]:
        """Get county settings or None if not configured"""
        result = self.supabase.table("v2_deal_features_county_settings").select("*").eq("county_id", county_id).execute()
        return result.data[0] if result.data else None

    async def get_user_preferences(self, user_id: str) -> Optional[Dict]:
        """Get user preferences or None if not configured"""
        result = self.supabase.table("v2_deal_features_user_preferences").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None

    def _get_default_admin_settings(self) -> Dict:
        """Default admin settings if database row missing"""
        return {
            "id": 1,
            # Feature flags (export_csv, save_property, market_anomaly_detection enabled by default)
            **{f"feature_{f}": False for f in self.FEATURES},
            "feature_export_csv": True,
            "feature_save_property": True,
            "feature_market_anomaly_detection": True,
            # No locks
            **{f"feature_lock_{f}": False for f in self.FEATURES},
            # AI thresholds defaults
            "anomaly_min_comps": 3,
            "anomaly_min_confidence": 0.700,
            "anomaly_max_zscore": 2.50,
            "anomaly_min_price_diff_percent": 15.00,
            "comps_analysis_min_samples": 3,
            "comps_analysis_max_distance_miles": 1.0,
            "comps_analysis_max_age_days": 365,
            "comps_analysis_min_similarity_score": 0.600,
            "renovation_min_photos": 1,
            "renovation_confidence_threshold": 0.500
        }

    # =========================================================================
    # AI QUALITY THRESHOLDS
    # =========================================================================

    async def get_ai_quality_thresholds(self) -> Dict[str, Any]:
        """
        Get AI quality thresholds for validation.
        These are global settings from admin that control when AI analysis
        is considered safe to show to users.

        Returns:
            Dict of threshold values
        """
        admin_settings = await self.get_admin_settings()
        return {
            "anomaly": {
                "min_comps": admin_settings.get("anomaly_min_comps", 3),
                "min_confidence": admin_settings.get("anomaly_min_confidence", 0.700),
                "max_zscore": admin_settings.get("anomaly_max_zscore", 2.50),
                "min_price_diff_percent": admin_settings.get("anomaly_min_price_diff_percent", 15.00)
            },
            "comps": {
                "min_samples": admin_settings.get("comps_analysis_min_samples", 3),
                "max_distance_miles": admin_settings.get("comps_analysis_max_distance_miles", 1.0),
                "max_age_days": admin_settings.get("comps_analysis_max_age_days", 365),
                "min_similarity_score": admin_settings.get("comps_analysis_min_similarity_score", 0.600)
            },
            "renovation": {
                "min_photos": admin_settings.get("renovation_min_photos", 1),
                "confidence_threshold": admin_settings.get("renovation_confidence_threshold", 0.500)
            }
        }

    # =========================================================================
    # ADMIN SETTINGS CRUD
    # =========================================================================

    async def update_admin_settings(self, updates: Dict) -> Dict:
        """Update admin settings (id=1)"""
        result = self.supabase.table("deal_features_admin_settings").update(updates).eq("id", 1).execute()
        return result.data[0] if result.data else {}

    async def get_admin_settings_detailed(self) -> Dict:
        """Get admin settings with computed metadata"""
        settings = await self.get_admin_settings()
        thresholds = await self.get_ai_quality_thresholds()
        return {
            **settings,
            "computed": {
                "total_features": len(self.FEATURES),
                "enabled_features": sum(1 for f in self.FEATURES if settings.get(f"feature_{f}", False)),
                "locked_features": sum(1 for f in self.FEATURES if settings.get(f"feature_lock_{f}", False))
            },
            "ai_thresholds": thresholds
        }

    # =========================================================================
    # COUNTY SETTINGS CRUD
    # =========================================================================

    async def create_county_settings(
        self,
        county_id: int,
        settings: Dict
    ) -> Dict:
        """Create or upsert county settings"""
        # Check if exists first
        existing = await self.get_county_settings(county_id)
        if existing:
            # Update existing
            return await self.update_county_settings(county_id, settings)

        data = {
            "county_id": county_id,
            **settings
        }
        result = self.supabase.table("v2_deal_features_county_settings").insert(data).execute()
        return result.data[0]

    async def update_county_settings(
        self,
        county_id: int,
        updates: Dict
    ) -> Dict:
        """Update county settings"""
        result = self.supabase.table("v2_deal_features_county_settings").update(updates).eq("county_id", county_id).execute()
        return result.data[0] if result.data else {}

    async def delete_county_settings(self, county_id: int) -> None:
        """Delete county settings (revert to admin defaults)"""
        self.supabase.table("v2_deal_features_county_settings").delete().eq("county_id", county_id).execute()

    async def list_all_county_settings(self) -> List[Dict]:
        """List all county settings"""
        result = self.supabase.table("v2_deal_features_county_settings").select("*").execute()
        return result.data

    # =========================================================================
    # USER PREFERENCES CRUD
    # =========================================================================

    async def create_user_preferences(
        self,
        user_id: str,
        county_id: int,
        preferences: Dict
    ) -> Dict:
        """Create or upsert user preferences"""
        # Check if exists first
        existing = await self.get_user_preferences(user_id)
        if existing:
            # Update existing - merge with county_id in preferences
            update_data = {**preferences, "county_id": county_id}
            return await self.update_user_preferences(user_id, update_data)

        data = {
            "user_id": user_id,
            "county_id": county_id,
            **preferences
        }
        result = self.supabase.table("v2_deal_features_user_preferences").insert(data).execute()
        return result.data[0]

    async def update_user_preferences(
        self,
        user_id: str,
        updates: Dict
    ) -> Dict:
        """Update user preferences"""
        result = self.supabase.table("v2_deal_features_user_preferences").update(updates).eq("user_id", user_id).execute()
        return result.data[0] if result.data else {}

    async def delete_user_preferences(self, user_id: str) -> None:
        """Delete user preferences"""
        self.supabase.table("v2_deal_features_user_preferences").delete().eq("user_id", user_id).execute()

    async def list_user_preferences(self, user_id: str) -> List[Dict]:
        """List all user preferences"""
        result = self.supabase.table("v2_deal_features_user_preferences").select("*").eq("user_id", user_id).execute()
        return result.data

    # =========================================================================
    # LOCK CHECKING
    # =========================================================================

    def is_locked_at_admin(
        self,
        feature: str,
        admin_settings: Optional[Dict] = None
    ) -> bool:
        """Check if feature is locked at admin level"""
        if admin_settings is None:
            return False
        return admin_settings.get(f"feature_lock_{feature}", False)

    def is_locked_at_county(
        self,
        feature: str,
        county_settings: Optional[Dict]
    ) -> bool:
        """Check if feature is locked at county level"""
        if county_settings is None:
            return False
        return county_settings.get(f"feature_lock_{feature}", False)

    def can_user_override(
        self,
        feature: str,
        admin_settings: Dict,
        county_settings: Optional[Dict] = None
    ) -> bool:
        """Check if user can override feature"""
        # Check admin lock
        if admin_settings.get(f"feature_lock_{feature}", False):
            return False

        # Check county lock
        if county_settings and county_settings.get(f"feature_lock_{feature}", False):
            return False

        return True

    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================

    async def enable_features_batch(
        self,
        features: List[str],
        level: str = "admin",
        level_id: Any = None
    ) -> Dict:
        """
        Enable multiple features at once.

        Args:
            features: List of feature names to enable
            level: "admin", "county", or "user"
            level_id: county_id for county level, user_id for user level
        """
        if level == "admin":
            updates = {f"feature_{f}": True for f in features if f in self.FEATURES}
            return await self.update_admin_settings(updates)

        elif level == "county":
            updates = {f"override_{f}": True for f in features if f in self.FEATURES}
            return await self.update_county_settings(level_id, updates)

        elif level == "user":
            updates = {f"pref_{f}": True for f in features if f in self.FEATURES}
            return await self.update_user_preferences(level_id, updates)

        else:
            raise ValueError(f"Invalid level: {level}")

    async def disable_features_batch(
        self,
        features: List[str],
        level: str = "admin",
        level_id: Any = None
    ) -> Dict:
        """
        Disable multiple features at once.

        Args:
            features: List of feature names to disable
            level: "admin", "county", or "user"
            level_id: county_id for county level, user_id for user level
        """
        if level == "admin":
            updates = {f"feature_{f}": False for f in features if f in self.FEATURES}
            return await self.update_admin_settings(updates)

        elif level == "county":
            updates = {f"override_{f}": False for f in features if f in self.FEATURES}
            return await self.update_county_settings(level_id, updates)

        elif level == "user":
            updates = {f"pref_{f}": False for f in features if f in self.FEATURES}
            return await self.update_user_preferences(level_id, updates)

        else:
            raise ValueError(f"Invalid level: {level}")
