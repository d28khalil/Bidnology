"""
Settings Service - Three-Tier Enrichment Settings Resolution

Implements settings resolution with lock logic:
Admin Settings (Global) → County Settings (Per-County) → User Preferences (Per-User)

Lock flags prevent overrides at lower levels.
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from supabase import create_client, Client


@dataclass
class ResolvedSettings:
    """Result of settings resolution"""
    # Endpoint settings
    endpoints: Dict[str, bool]
    # Investment parameters
    investment_params: Dict[str, Any]
    # Permissions
    permissions: Dict[str, bool]
    # Metadata
    template_preset: Optional[str] = None
    sources: Dict[str, str] = None  # Track where each value came from


class SettingsService:
    """Service for resolving and managing enrichment settings"""

    # All 13 Zillow endpoint names
    ENDPOINTS = [
        "pro_byaddress",
        "custom_ad_byzpid",
        "similar",
        "nearby",
        "pricehistory",
        "graph_listing_price",
        "taxinfo",
        "climate",
        "walk_transit_bike",
        "housing_market",
        "rental_market",
        "ownerinfo",
        "custom_ae_searchbyaddress"
    ]

    # All investment parameter names
    INVESTMENT_PARAMS = [
        "annual_appreciation",
        "mortgage_rate",
        "down_payment_rate",
        "loan_term_months",
        "insurance_rate",
        "property_tax_rate",
        "maintenance_rate",
        "property_mgmt_rate",
        "vacancy_rate",
        "closing_costs_rate",
        "target_profit_margin",
        "renovation_cost_default"
    ]

    # Template preset definitions
    TEMPLATES = {
        "minimal": {
            "pro_byaddress": True,
            "custom_ad_byzpid": True,
            "pricehistory": True,
        },
        "standard": {
            "pro_byaddress": True,
            "custom_ad_byzpid": True,
            "similar": True,
            "pricehistory": True,
            "taxinfo": True,
            "ownerinfo": True,
        },
        "flipper": {
            "pro_byaddress": True,
            "custom_ad_byzpid": True,
            "similar": True,
            "nearby": True,
            "pricehistory": True,
            "taxinfo": True,
            "ownerinfo": True,
        },
        "landlord": {
            "pro_byaddress": True,
            "custom_ad_byzpid": True,
            "similar": True,
            "pricehistory": True,
            "taxinfo": True,
            "climate": True,
            "walk_transit_bike": True,
            "housing_market": True,
            "rental_market": True,
        },
        "thorough": {
            "pro_byaddress": True,
            "custom_ad_byzpid": True,
            "similar": True,
            "nearby": True,
            "pricehistory": True,
            "graph_listing_price": True,
            "taxinfo": True,
            "climate": True,
            "walk_transit_bike": True,
            "housing_market": True,
            "rental_market": True,
            "ownerinfo": True,
        }
    }

    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

    # =========================================================================
    # SETTINGS RESOLUTION
    # =========================================================================

    async def resolve_settings(
        self,
        county_id: int,
        state: str,
        user_id: Optional[str] = None
    ) -> ResolvedSettings:
        """
        Resolve settings with priority: User > County > Admin
        Respects lock flags at each level.
        """
        # Fetch all three levels
        admin_settings = await self.get_admin_settings()
        county_settings = await self.get_county_settings(county_id, state)
        user_prefs = await self.get_user_preferences(user_id, county_id, state) if user_id else None

        # Get permissions from admin
        permissions = {
            "allow_user_overrides": admin_settings.get("allow_user_overrides", True),
            "allow_user_templates": admin_settings.get("allow_user_templates", True),
            "allow_custom_investment_params": admin_settings.get("allow_custom_investment_params", False)
        }

        # Resolve endpoints with lock logic
        endpoints = {}
        sources = {}

        for endpoint in self.ENDPOINTS:
            endpoint_key = f"endpoint_{endpoint}"
            lock_key = f"endpoint_lock_{endpoint}"

            # Check admin lock
            admin_locked = admin_settings.get(lock_key, False)

            if admin_locked:
                # Use admin value, ignore county/user
                endpoints[endpoint] = admin_settings.get(endpoint_key, True)
                sources[endpoint_key] = "admin_locked"

            elif permissions["allow_user_overrides"] and user_prefs:
                # Check county lock
                county_locked = county_settings.get(lock_key, False) if county_settings else False

                if county_locked:
                    # Use county value, ignore user
                    endpoints[endpoint] = county_settings.get(endpoint_key, admin_settings.get(endpoint_key, True))
                    sources[endpoint_key] = "county_locked"

                else:
                    # User can override
                    endpoints[endpoint] = self._coalesce_value(
                        endpoint_key,
                        user_prefs,
                        county_settings,
                        admin_settings,
                        default=True
                    )
                    sources[endpoint_key] = "user" if user_prefs.get(endpoint_key) is not None else "inherited"

            elif county_settings:
                # County can override admin (unless locked)
                endpoints[endpoint] = county_settings.get(
                    endpoint_key,
                    admin_settings.get(endpoint_key, True)
                )
                sources[endpoint_key] = "county" if county_settings.get(endpoint_key) is not None else "admin"

            else:
                # Use admin default
                endpoints[endpoint] = admin_settings.get(endpoint_key, True)
                sources[endpoint_key] = "admin"

        # Resolve investment parameters (no lock, just coalesce)
        investment_params = {}
        for param in self.INVESTMENT_PARAMS:
            inv_key = f"inv_{param}"

            if permissions["allow_custom_investment_params"] and user_prefs:
                investment_params[param] = self._coalesce_value(
                    inv_key,
                    user_prefs,
                    county_settings,
                    admin_settings
                )
            elif county_settings:
                investment_params[param] = self._coalesce_value(
                    inv_key,
                    None,  # No user
                    county_settings,
                    admin_settings
                )
            else:
                investment_params[param] = admin_settings.get(inv_key)

        # Get template preset
        template_preset = (
            user_prefs.get("template_preset") if user_prefs else None
        ) or county_settings.get("template_preset") if county_settings else None

        # If template is set, apply it to endpoints
        if template_preset and template_preset in self.TEMPLATES:
            template_endpoints = self.TEMPLATES[template_preset]
            for endpoint, enabled in template_endpoints.items():
                # Only override if not locked
                lock_key = f"endpoint_lock_{endpoint}"
                if not admin_settings.get(lock_key, False):
                    endpoints[endpoint] = enabled
                    sources[f"endpoint_{endpoint}"] = f"template_{template_preset}"

        return ResolvedSettings(
            endpoints=endpoints,
            investment_params=investment_params,
            permissions=permissions,
            template_preset=template_preset,
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
        result = self.supabase.table("enrichment_admin_settings").select("*").eq("id", 1).execute()

        if not result.data:
            # Create default if missing
            return self._get_default_admin_settings()

        return result.data[0]

    async def get_county_settings(
        self,
        county_id: int,
        state: str
    ) -> Optional[Dict]:
        """Get county settings or None if not configured"""
        result = self.supabase.table("county_enrichment_settings").select("*").eq("county_id", county_id).eq("state", state).execute()
        return result.data[0] if result.data else None

    async def get_user_preferences(
        self,
        user_id: str,
        county_id: int,
        state: str
    ) -> Optional[Dict]:
        """Get user preferences or None if not configured"""
        result = self.supabase.table("user_enrichment_preferences").select("*").eq("user_id", user_id).eq("county_id", county_id).eq("state", state).execute()
        return result.data[0] if result.data else None

    def _get_default_admin_settings(self) -> Dict:
        """Default admin settings if database row missing"""
        return {
            "id": 1,
            # Endpoints enabled
            "endpoint_pro_byaddress": True,
            "endpoint_custom_ad_byzpid": True,
            "endpoint_similar": True,
            "endpoint_nearby": False,
            "endpoint_pricehistory": True,
            "endpoint_graph_listing_price": False,
            "endpoint_taxinfo": False,
            "endpoint_climate": False,
            "endpoint_walk_transit_bike": False,
            "endpoint_housing_market": False,
            "endpoint_rental_market": False,
            "endpoint_ownerinfo": False,
            "endpoint_custom_ae_searchbyaddress": False,
            # No locks
            **{f"endpoint_lock_{ep}": False for ep in self.ENDPOINTS},
            # Investment defaults
            "inv_annual_appreciation": 0.03,
            "inv_mortgage_rate": 0.065,
            "inv_down_payment_rate": 0.20,
            "inv_loan_term_months": 360,
            "inv_insurance_rate": 0.015,
            "inv_property_tax_rate": 0.012,
            "inv_maintenance_rate": 0.01,
            "inv_property_mgmt_rate": 0.08,
            "inv_vacancy_rate": 0.05,
            "inv_closing_costs_rate": 0.03,
            "inv_target_profit_margin": 0.30,
            "inv_renovation_cost_default": 25000,
            # Permissions
            "allow_user_overrides": True,
            "allow_user_templates": True,
            "allow_custom_investment_params": False
        }

    # =========================================================================
    # TEMPLATE MANAGEMENT
    # =========================================================================

    def get_template(self, template_name: str) -> Optional[Dict[str, bool]]:
        """Get template endpoint configuration"""
        return self.TEMPLATES.get(template_name)

    def list_templates(self) -> List[str]:
        """List available template names"""
        return list(self.TEMPLATES.keys())

    async def apply_template(
        self,
        level: str,  # "county" or "user"
        level_id: Any,  # county_id or user_id
        template: str,
        state: str = None,
        county_id: int = None
    ) -> Dict:
        """
        Apply template preset to settings level.

        Args:
            level: "county" or "user"
            level_id: county_id (int) or user_id (str)
            template: Template name (minimal, standard, flipper, landlord, thorough)
            state: Required for county/user
            county_id: Required for user level

        Returns:
            Updated settings
        """
        if template not in self.TEMPLATES:
            raise ValueError(f"Unknown template: {template}")

        template_config = self.TEMPLATES[template]

        if level == "county":
            # Apply to county settings
            table = "county_enrichment_settings"
            update_data = {
                "template_preset": template,
                **{f"endpoint_{ep}": enabled for ep, enabled in template_config.items()}
            }

            result = self.supabase.table(table).upsert({
                "county_id": level_id,
                "state": state,
                **update_data
            }).execute()

        elif level == "user":
            # Apply to user preferences
            if not county_id or not state:
                raise ValueError("county_id and state required for user template application")

            table = "user_enrichment_preferences"
            update_data = {
                "template_preset": template,
                **{f"endpoint_{ep}": enabled for ep, enabled in template_config.items()}
            }

            result = self.supabase.table(table).upsert({
                "user_id": level_id,
                "county_id": county_id,
                "state": state,
                **update_data
            }).execute()

        else:
            raise ValueError(f"Invalid level: {level}")

        return result.data[0] if result.data else {}

    # =========================================================================
    # COUNTY SETTINGS CRUD
    # =========================================================================

    async def create_county_settings(
        self,
        county_id: int,
        county_name: str,
        state: str,
        settings: Dict
    ) -> Dict:
        """Create county settings"""
        data = {
            "county_id": county_id,
            "county_name": county_name,
            "state": state,
            **settings
        }
        result = self.supabase.table("county_enrichment_settings").insert(data).execute()
        return result.data[0]

    async def update_county_settings(
        self,
        county_id: int,
        state: str,
        updates: Dict
    ) -> Dict:
        """Update county settings"""
        result = self.supabase.table("county_enrichment_settings").update(updates).eq("county_id", county_id).eq("state", state).execute()
        return result.data[0] if result.data else {}

    async def delete_county_settings(
        self,
        county_id: int,
        state: str
    ) -> None:
        """Delete county settings (revert to admin defaults)"""
        self.supabase.table("county_enrichment_settings").delete().eq("county_id", county_id).eq("state", state).execute()

    async def list_all_county_settings(self) -> List[Dict]:
        """List all county settings"""
        result = self.supabase.table("county_enrichment_settings").select("*").execute()
        return result.data

    # =========================================================================
    # USER PREFERENCES CRUD
    # =========================================================================

    async def create_user_preferences(
        self,
        user_id: str,
        county_id: int,
        state: str,
        preferences: Dict
    ) -> Dict:
        """Create user preferences"""
        data = {
            "user_id": user_id,
            "county_id": county_id,
            "state": state,
            **preferences
        }
        result = self.supabase.table("user_enrichment_preferences").insert(data).execute()
        return result.data[0]

    async def update_user_preferences(
        self,
        user_id: str,
        county_id: int,
        state: str,
        updates: Dict
    ) -> Dict:
        """Update user preferences"""
        result = self.supabase.table("user_enrichment_preferences").update(updates).eq("user_id", user_id).eq("county_id", county_id).eq("state", state).execute()
        return result.data[0] if result.data else {}

    async def delete_user_preferences(
        self,
        user_id: str,
        county_id: int,
        state: str
    ) -> None:
        """Delete user preferences"""
        self.supabase.table("user_enrichment_preferences").delete().eq("user_id", user_id).eq("county_id", county_id).eq("state", state).execute()

    async def list_user_preferences(
        self,
        user_id: str
    ) -> List[Dict]:
        """List all user preferences"""
        result = self.supabase.table("user_enrichment_preferences").select("*").eq("user_id", user_id).execute()
        return result.data

    # =========================================================================
    # ADMIN SETTINGS CRUD
    # =========================================================================

    async def update_admin_settings(
        self,
        updates: Dict
    ) -> Dict:
        """Update admin settings (id=1)"""
        result = self.supabase.table("enrichment_admin_settings").update(updates).eq("id", 1).execute()
        return result.data[0] if result.data else {}

    # =========================================================================
    # LOCK CHECKING
    # =========================================================================

    def is_locked_at_admin(
        self,
        endpoint: str,
        admin_settings: Optional[Dict] = None
    ) -> bool:
        """Check if endpoint is locked at admin level"""
        if admin_settings is None:
            return False
        return admin_settings.get(f"endpoint_lock_{endpoint}", False)

    def is_locked_at_county(
        self,
        endpoint: str,
        county_settings: Optional[Dict]
    ) -> bool:
        """Check if endpoint is locked at county level"""
        if county_settings is None:
            return False
        return county_settings.get(f"endpoint_lock_{endpoint}", False)

    def can_user_override(
        self,
        endpoint: str,
        admin_settings: Dict,
        county_settings: Optional[Dict] = None
    ) -> bool:
        """Check if user can override endpoint"""
        # Check admin permission
        if not admin_settings.get("allow_user_overrides", True):
            return False

        # Check admin lock
        if admin_settings.get(f"endpoint_lock_{endpoint}", False):
            return False

        # Check county lock
        if county_settings and county_settings.get(f"endpoint_lock_{endpoint}", False):
            return False

        return True
