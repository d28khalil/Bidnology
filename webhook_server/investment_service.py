"""
Investment Strategy Service

Manages user investment strategies for property evaluation.
Allows users to define criteria that match their investment goals.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from .feature_toggle_service import FeatureToggleService

logger = logging.getLogger(__name__)

# Strategy type definitions
STRATEGY_TYPES = [
    "fix_and_flip",
    "buy_and_hold",
    "wholesale",
    "brrrr",
    "value_add",
    "rental",
    "multi_family",
    "commercial"
]


class InvestmentStrategyService:
    """Service for managing user investment strategies"""

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
        """Check if investment strategies feature is enabled"""
        return await self.feature_service.is_feature_enabled(
            "v2_investment_strategies",
            user_id=user_id,
            county_id=county_id,
            state=state
        )

    async def create_strategy(
        self,
        user_id: str,
        strategy_name: str,
        strategy_type: str,
        min_fix_and_flip_profit: Optional[float] = None,
        max_purchase_price: Optional[float] = None,
        min_arv_spread: Optional[float] = None,
        max_repair_cost: Optional[float] = None,
        max_holding_months: Optional[int] = None,
        min_cash_flow: Optional[float] = None,
        custom_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new investment strategy"""
        if not await self.is_feature_enabled(user_id):
            raise PermissionError("Investment strategies feature not enabled")

        if strategy_type not in STRATEGY_TYPES:
            raise ValueError(f"Invalid strategy_type: {strategy_type}")

        # Check if this should be default (first strategy for user)
        existing = await self.get_strategies(user_id)
        is_default = len(existing) == 0

        strategy_data = {
            "user_id": user_id,
            "name": strategy_name,  # Database column is 'name', not 'strategy_name'
            "strategy_type": strategy_type,
            "min_fix_and_flip_profit": min_fix_and_flip_profit,  # Database column
            "max_purchase_price": max_purchase_price,
            "min_arv_spread": min_arv_spread,
            "max_repair_cost": max_repair_cost,  # Database column (not max_rehab_cost)
            "max_holding_months": max_holding_months,
            "min_cash_flow": min_cash_flow,
            "custom_criteria": custom_criteria or {},
            "is_active": True,
            "is_default": is_default,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        result = self.supabase.table("v2_investment_strategies").insert(
            strategy_data
        ).execute()

        if not result.data:
            raise Exception("Failed to create strategy")

        logger.info(f"Created investment strategy '{strategy_name}' for user {user_id}")
        return result.data[0]

    async def get_strategies(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get strategies for a user"""
        query = self.supabase.table("v2_investment_strategies").select(
            "*"
        ).eq("user_id", user_id).order("is_default", desc=True).order("created_at", desc=True)

        if active_only:
            query = query.eq("is_active", True)

        result = query.execute()
        return result.data if result.data else []

    async def get_strategy(
        self,
        strategy_id: int,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific strategy"""
        result = self.supabase.table("v2_investment_strategies").select(
            "*"
        ).eq("id", strategy_id).eq("user_id", user_id).execute()

        return result.data[0] if result.data else None

    async def update_strategy(
        self,
        strategy_id: int,
        user_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update a strategy"""
        # Validate strategy exists and belongs to user
        existing = await self.get_strategy(strategy_id, user_id)
        if not existing:
            raise ValueError(f"Strategy {strategy_id} not found")

        # Remove restricted fields and map strategy_name -> name
        updates.pop("id", None)
        updates.pop("user_id", None)
        updates.pop("created_at", None)

        # Map strategy_name to name (database column)
        if "strategy_name" in updates:
            updates["name"] = updates.pop("strategy_name")

        updates["updated_at"] = datetime.utcnow().isoformat()

        result = self.supabase.table("v2_investment_strategies").update(
            updates
        ).eq("id", strategy_id).execute()

        if not result.data:
            raise Exception("Failed to update strategy")

        logger.info(f"Updated investment strategy {strategy_id}")
        return result.data[0]

    async def delete_strategy(
        self,
        strategy_id: int,
        user_id: str
    ) -> bool:
        """Delete a strategy"""
        # Can't delete default strategy - must set another as default first
        existing = await self.get_strategy(strategy_id, user_id)
        if not existing:
            raise ValueError(f"Strategy {strategy_id} not found")

        if existing.get("is_default"):
            # Check if user has other strategies
            others = await self.get_strategies(user_id, active_only=False)
            if len(others) > 1:
                raise ValueError("Cannot delete default strategy. Set another as default first.")

        result = self.supabase.table("v2_investment_strategies").delete().eq(
            "id", strategy_id
        ).eq("user_id", user_id).execute()

        deleted = len(result.data) > 0 if result.data else False

        if deleted:
            logger.info(f"Deleted investment strategy {strategy_id}")

        return deleted

    async def set_default_strategy(
        self,
        strategy_id: int,
        user_id: str
    ) -> Dict[str, Any]:
        """Set a strategy as the default for a user"""
        # Unset existing default
        self.supabase.table("v2_investment_strategies").update({
            "is_default": False
        }).eq("user_id", user_id).eq("is_default", True).execute()

        # Set new default
        result = self.supabase.table("v2_investment_strategies").update({
            "is_default": True,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", strategy_id).eq("user_id", user_id).execute()

        if not result.data:
            raise ValueError(f"Strategy {strategy_id} not found")

        logger.info(f"Set strategy {strategy_id} as default for user {user_id}")
        return result.data[0]

    async def evaluate_property_against_strategy(
        self,
        property_id: int,
        strategy_id: int,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate if a property meets strategy criteria.

        Returns match score and details.
        """
        strategy = await self.get_strategy(strategy_id, user_id)
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        # Get property data
        property_result = self.supabase.table("foreclosure_listings").select(
            "*"
        ).eq("id", property_id).execute()

        if not property_result.data:
            raise ValueError(f"Property {property_id} not found")

        property_data = property_result.data[0]

        # Get enriched data
        from .market_anomaly_service import MarketAnomalyService
        from .comparable_sales_service import ComparableSalesService
        from .renovation_service import RenovationEstimatorService

        anomaly_service = MarketAnomalyService()
        comps_service = ComparableSalesService()
        reno_service = RenovationEstimatorService()

        # Get analysis data
        anomaly = await anomaly_service.get_anomalies_for_property(property_id)
        comps = await comps_service.get_saved_analysis(property_id)
        reno = await reno_service.get_saved_estimate(property_id)

        # Evaluate against criteria
        evaluation = {
            "strategy_id": strategy_id,
            "strategy_name": strategy["name"],  # Database column is 'name'
            "property_id": property_id,
            "match_score": 0.0,
            "criteria_results": {}
        }

        # Price check
        if strategy.get("max_purchase_price"):
            purchase_price = (
                property_data.get("opening_bid") or
                property_data.get("approx_upset")
            )
            if purchase_price:
                price_match = purchase_price <= strategy["max_purchase_price"]
                evaluation["criteria_results"]["max_purchase_price"] = {
                    "passed": price_match,
                    "actual": purchase_price,
                    "required": strategy["max_purchase_price"]
                }

        # ROI check - use min_fix_and_flip_profit column
        if strategy.get("min_fix_and_flip_profit") and anomaly:
            price_diff = anomaly[0].get("price_difference_percent", 0) if anomaly else 0
            roi_match = price_diff >= strategy["min_fix_and_flip_profit"] * 100
            evaluation["criteria_results"]["min_fix_and_flip_profit"] = {
                "passed": roi_match,
                "actual": price_diff,
                "required": strategy["min_fix_and_flip_profit"] * 100
            }

        # Rehab cost check - use max_repair_cost column
        if strategy.get("max_repair_cost") and reno:
            reno_cost = reno.get("total_estimated_cost")
            if reno_cost:
                rehab_match = reno_cost <= strategy["max_repair_cost"]
                evaluation["criteria_results"]["max_repair_cost"] = {
                    "passed": rehab_match,
                    "actual": reno_cost,
                    "required": strategy["max_repair_cost"]
                }

        # Calculate overall match score
        passed = sum(
            1 for c in evaluation["criteria_results"].values()
            if c.get("passed", False)
        )
        total = len(evaluation["criteria_results"])
        evaluation["match_score"] = round(passed / total, 3) if total > 0 else 0.0

        return evaluation
