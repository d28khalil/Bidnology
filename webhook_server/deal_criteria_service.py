"""
Deal Criteria Service

Manages user deal criteria for automatic property matching.
Calculates match scores between properties and user preferences.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

from supabase import create_client

logger = logging.getLogger(__name__)


# Match categories based on score
HOT_MATCH_THRESHOLD = 0.80
WARM_MATCH_THRESHOLD = 0.60


class DealCriteriaService:
    """
    Service for managing user deal criteria and matching properties.

    Features:
    - Create/update user deal criteria
    - Calculate match scores for properties
    - Get matching properties for users
    - Track and alert on new matches
    """

    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        self.supabase = create_client(supabase_url, supabase_key)

    # =========================================================================
    # CRITERIA MANAGEMENT
    # =========================================================================

    async def get_criteria(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's deal criteria.

        Args:
            user_id: User ID

        Returns:
            User's deal criteria or None
        """
        try:
            result = self.supabase.table("user_deal_criteria").select("*").eq("user_id", user_id).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting criteria for user {user_id}: {e}")
            return None

    async def upsert_criteria(
        self,
        user_id: str,
        min_upset_price: Optional[float] = None,
        max_upset_price: Optional[float] = None,
        min_arv_percentage: Optional[float] = None,
        minimum_profit_margin: Optional[float] = None,
        max_rehab_budget: Optional[float] = None,
        max_rehab_percentage: Optional[float] = None,
        preferred_property_types: Optional[List[str]] = None,
        preferred_counties: Optional[List[int]] = None,
        preferred_cities: Optional[List[str]] = None,
        exclude_areas: Optional[List[str]] = None,
        ideal_days_to_auction: Optional[int] = None,
        avoid_pending_litigation: Optional[bool] = None,
        min_data_quality_score: Optional[float] = None,
        investment_strategy: Optional[str] = None,
        custom_weights: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
        enable_alerts: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create or update user's deal criteria.

        Args:
            user_id: User ID
            min_upset_price: Minimum upset price
            max_upset_price: Maximum upset price
            min_arv_percentage: Minimum ARV as percentage of upset price
            minimum_profit_margin: Minimum profit margin percentage
            max_rehab_budget: Maximum rehab budget
            max_rehab_percentage: Maximum rehab as percentage of ARV
            preferred_property_types: List of preferred property types
            preferred_counties: List of preferred county IDs
            preferred_cities: List of preferred cities
            exclude_areas: Areas to exclude
            ideal_days_to_auction: Ideal days until auction
            avoid_pending_litigation: Avoid properties with pending litigation
            min_data_quality_score: Minimum data quality score
            investment_strategy: Investment strategy preference
            custom_weights: Custom scoring weights
            is_active: Whether criteria is active
            enable_alerts: Whether to enable match alerts

        Returns:
            Created or updated criteria
        """
        try:
            # Build update data with only non-None values
            data = {"user_id": user_id}

            if min_upset_price is not None:
                data["min_upset_price"] = min_upset_price
            if max_upset_price is not None:
                data["max_upset_price"] = max_upset_price
            if min_arv_percentage is not None:
                data["min_arv_percentage"] = min_arv_percentage
            if minimum_profit_margin is not None:
                data["minimum_profit_margin"] = minimum_profit_margin
            if max_rehab_budget is not None:
                data["max_rehab_budget"] = max_rehab_budget
            if max_rehab_percentage is not None:
                data["max_rehab_percentage"] = max_rehab_percentage
            if preferred_property_types is not None:
                data["preferred_property_types"] = preferred_property_types
            if preferred_counties is not None:
                data["preferred_counties"] = preferred_counties
            if preferred_cities is not None:
                data["preferred_cities"] = preferred_cities
            if exclude_areas is not None:
                data["exclude_areas"] = exclude_areas
            if ideal_days_to_auction is not None:
                data["ideal_days_to_auction"] = ideal_days_to_auction
            if avoid_pending_litigation is not None:
                data["avoid_pending_litigation"] = avoid_pending_litigation
            if min_data_quality_score is not None:
                data["min_data_quality_score"] = min_data_quality_score
            if investment_strategy is not None:
                data["investment_strategy"] = investment_strategy
            if custom_weights is not None:
                data["custom_weights"] = custom_weights
            if is_active is not None:
                data["is_active"] = is_active
            if enable_alerts is not None:
                data["enable_alerts"] = enable_alerts

            # Upsert
            result = self.supabase.table("user_deal_criteria").upsert(
                data,
                on_conflict="user_id"
            ).execute()

            if result.data:
                logger.info(f"Upserted criteria for user {user_id}")
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error upserting criteria for user {user_id}: {e}")
            return None

    async def delete_criteria(self, user_id: str) -> bool:
        """
        Delete user's deal criteria.

        Args:
            user_id: User ID

        Returns:
            True if deleted
        """
        try:
            self.supabase.table("user_deal_criteria").delete().eq("user_id", user_id).execute()
            logger.info(f"Deleted criteria for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting criteria for user {user_id}: {e}")
            return False

    # =========================================================================
    # MATCH SCORING
    # =========================================================================

    async def calculate_match_score(
        self,
        user_id: str,
        property_id: int,
        property_data: Optional[Dict[str, Any]] = None,
        criteria: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate match score for a property against user's criteria.

        Args:
            user_id: User ID
            property_id: Property ID
            property_data: Optional property data (if None, will fetch from DB)
            criteria: Optional criteria (if None, will fetch from DB)

        Returns:
            Match score dict with breakdown
        """
        # Fetch criteria if not provided
        if criteria is None:
            criteria = await self.get_criteria(user_id)
            if not criteria:
                return None

        # Check if criteria is active
        if not criteria.get("is_active"):
            return None

        # Fetch property data if not provided
        if property_data is None:
            result = self.supabase.table("foreclosure_listings").select("*").eq("id", property_id).execute()
            if not result.data:
                return None
            property_data = result.data[0]

        # Get custom weights
        custom_weights = criteria.get("custom_weights", {})

        # Calculate individual scores
        price_score = self._score_price(property_data, criteria)
        arv_score = self._score_arv(property_data, criteria)
        location_score = self._score_location(property_data, criteria)
        condition_score = self._score_condition(property_data, criteria)
        time_score = self._score_time(property_data, criteria)

        # Calculate weighted total
        weights = {
            "price_weight": custom_weights.get("price_weight", 0.25),
            "arv_weight": custom_weights.get("arv_weight", 0.25),
            "location_weight": custom_weights.get("location_weight", 0.20),
            "condition_weight": custom_weights.get("condition_weight", 0.15),
            "time_weight": custom_weights.get("time_weight", 0.15)
        }

        total_score = (
            price_score * weights["price_weight"] +
            arv_score * weights["arv_weight"] +
            location_score * weights["location_weight"] +
            condition_score * weights["condition_weight"] +
            time_score * weights["time_weight"]
        )

        # Determine category
        if total_score >= HOT_MATCH_THRESHOLD:
            category = "hot"
        elif total_score >= WARM_MATCH_THRESHOLD:
            category = "warm"
        else:
            category = "cold"

        # Build match reasons and disqualifications
        match_reasons, disqualifications = self._build_match_reasons(
            property_data, criteria,
            price_score, arv_score, location_score, condition_score, time_score
        )

        # Build score breakdown
        score_breakdown = {
            "price_score": round(price_score, 4),
            "arv_score": round(arv_score, 4),
            "location_score": round(location_score, 4),
            "condition_score": round(condition_score, 4),
            "time_score": round(time_score, 4),
            "weights": weights
        }

        result = {
            "user_id": user_id,
            "property_id": property_id,
            "criteria_id": criteria.get("id"),
            "match_score": round(total_score, 4),
            "match_category": category,
            "score_breakdown": score_breakdown,
            "match_reasons": match_reasons,
            "disqualification_reasons": disqualifications,
            "property_snapshot": {
                "id": property_data.get("id"),
                "property_address": property_data.get("property_address"),
                "upset_price": property_data.get("upset_price"),
                "city": property_data.get("city"),
                "county_id": property_data.get("county_id"),
                "property_type": property_data.get("property_type"),
                "attorney_status": property_data.get("attorney_status")
            },
            "calculated_at": datetime.utcnow().isoformat()
        }

        # Store the match score
        await self._store_match_score(result)

        return result

    def _score_price(self, property_data: Dict, criteria: Dict) -> float:
        """Score property based on price criteria"""
        upset_price = property_data.get("upset_price")
        if not upset_price:
            return 0.0

        min_price = criteria.get("min_upset_price")
        max_price = criteria.get("max_upset_price")

        if min_price and upset_price < min_price:
            return 0.0
        if max_price and upset_price > max_price:
            return 0.0

        # If within range, give higher score for lower price
        if max_price and min_price:
            range_size = max_price - min_price
            if range_size > 0:
                # Lower is better - score decreases as price increases
                return max(0.0, 1.0 - ((upset_price - min_price) / range_size) * 0.5)

        return 1.0

    def _score_arv(self, property_data: Dict, criteria: Dict) -> float:
        """Score property based on ARV potential"""
        upset_price = property_data.get("upset_price")
        if not upset_price:
            return 0.0

        # Check enrichment data for ARV
        arv = property_data.get("arv_high") or property_data.get("arv_low") or property_data.get("avg_comp_price")
        if not arv:
            return 0.5  # Neutral score if no ARV data

        arv_percentage = (arv / upset_price * 100) if upset_price > 0 else 0
        min_arv_pct = criteria.get("min_arv_percentage", 70)

        if arv_percentage >= min_arv_pct:
            # Bonus for higher ARV percentage
            return min(1.0, 0.5 + (arv_percentage - min_arv_pct) / 100)
        else:
            # Linear penalty
            return max(0.0, arv_percentage / min_arv_pct * 0.5)

    def _score_location(self, property_data: Dict, criteria: Dict) -> float:
        """Score property based on location preferences"""
        score = 0.0
        possible_scores = 0

        # Check county preference
        preferred_counties = criteria.get("preferred_counties", [])
        county_id = property_data.get("county_id")
        if preferred_counties:
            possible_scores += 1
            if county_id in preferred_counties:
                score += 1

        # Check city preference
        preferred_cities = criteria.get("preferred_cities", [])
        city = property_data.get("city")
        if preferred_cities:
            possible_scores += 1
            if city and city in preferred_cities:
                score += 1

        # Check exclusion areas
        exclude_areas = criteria.get("exclude_areas", [])
        if exclude_areas:
            possible_scores += 1
            if city and city not in exclude_areas:
                score += 1

        # Default to 1.0 if no location preferences set
        if possible_scores == 0:
            return 1.0

        return score / possible_scores if possible_scores > 0 else 1.0

    def _score_condition(self, property_data: Dict, criteria: Dict) -> float:
        """Score property based on condition factors"""
        score = 1.0

        # Check for pending litigation
        avoid_litigation = criteria.get("avoid_pending_litigation", True)
        if avoid_litigation:
            attorney_status = property_data.get("attorney_status", "").lower()
            if "pending" in attorney_status or "litigation" in attorney_status:
                score = 0.0

        # Check data quality
        min_quality = criteria.get("min_data_quality_score", 0.5)
        property_quality = property_data.get("data_quality_score", min_quality)
        if property_quality < min_quality:
            score *= 0.5

        return score

    def _score_time(self, property_data: Dict, criteria: Dict) -> float:
        """Score property based on auction timing"""
        auction_date = property_data.get("auction_date")
        ideal_days = criteria.get("ideal_days_to_auction", 7)

        if not auction_date:
            return 0.5

        try:
            if isinstance(auction_date, str):
                auction_date = datetime.fromisoformat(auction_date.replace("Z", "+00:00"))

            days_until = (auction_date - datetime.utcnow()).days

            if days_until < 0:
                return 0.0  # Past auction
            elif days_until <= ideal_days:
                # Ideal range - highest score
                return 1.0
            elif days_until <= ideal_days * 2:
                # Still acceptable - declining score
                return 1.0 - ((days_until - ideal_days) / ideal_days) * 0.5
            else:
                # Too far out - lower score
                return max(0.0, 1.0 - (days_until / (ideal_days * 4)))

        except (ValueError, TypeError) as date_err:
            logger.warning(f"Invalid auction_date format for property scoring: {date_err}")
            return 0.5

    def _build_match_reasons(
        self,
        property_data: Dict,
        criteria: Dict,
        price_score: float,
        arv_score: float,
        location_score: float,
        condition_score: float,
        time_score: float
    ) -> tuple[List[str], List[str]]:
        """Build list of match reasons and disqualifications"""
        match_reasons = []
        disqualifications = []

        # Price reasons
        if price_score >= 0.8:
            match_reasons.append("Excellent price range")
        elif price_score < 0.3:
            disqualifications.append("Price out of range")

        # ARV reasons
        if arv_score >= 0.8:
            match_reasons.append("High ARV potential")
        elif arv_score < 0.3:
            disqualifications.append("Low ARV potential")

        # Location reasons
        if location_score >= 0.8:
            match_reasons.append("Preferred location")
        elif location_score < 0.3:
            disqualifications.append("Location not preferred")

        # Condition reasons
        if condition_score >= 0.8:
            match_reasons.append("Good property condition")
        elif condition_score < 0.3:
            disqualifications.append("Property has issues")

        # Time reasons
        if time_score >= 0.8:
            match_reasons.append("Good auction timing")

        return match_reasons, disqualifications

    async def _store_match_score(self, match_data: Dict[str, Any]) -> bool:
        """Store match score in database"""
        try:
            self.supabase.table("property_match_scores").upsert(
                {
                    "user_id": match_data["user_id"],
                    "property_id": match_data["property_id"],
                    "criteria_id": match_data.get("criteria_id"),
                    "match_score": match_data["match_score"],
                    "match_category": match_data["match_category"],
                    "score_breakdown": match_data["score_breakdown"],
                    "match_reasons": match_data.get("match_reasons", []),
                    "disqualification_reasons": match_data.get("disqualification_reasons", []),
                    "property_snapshot": match_data.get("property_snapshot", {})
                },
                on_conflict="user_id,property_id"
            ).execute()
            return True

        except Exception as e:
            logger.error(f"Error storing match score: {e}")
            return False

    # =========================================================================
    # MATCHING QUERIES
    # =========================================================================

    async def get_matching_properties(
        self,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get properties matching user's criteria.

        Args:
            user_id: User ID
            category: Filter by match category (hot, warm, cold)
            limit: Maximum number of results

        Returns:
            List of matching properties with scores
        """
        try:
            query = self.supabase.table("property_match_scores").select(
                "*, foreclosure_listings(*)"
            ).eq("user_id", user_id)

            if category:
                query = query.eq("match_category", category)

            result = query.order("match_score", desc=True).limit(limit).execute()

            return result.data

        except Exception as e:
            logger.error(f"Error getting matches for user {user_id}: {e}")
            return []

    async def get_hot_matches(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get hot matches for a user"""
        return await self.get_matching_properties(user_id, category="hot", limit=limit)

    async def get_warm_matches(self, user_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get warm matches for a user"""
        return await self.get_matching_properties(user_id, category="warm", limit=limit)

    async def get_match_by_property(self, user_id: str, property_id: int) -> Optional[Dict[str, Any]]:
        """Get match score for a specific property"""
        try:
            result = self.supabase.table("property_match_scores").select(
                "*, foreclosure_listings(*)"
            ).eq("user_id", user_id).eq("property_id", property_id).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting match for property {property_id}: {e}")
            return None

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================

    async def score_properties_batch(
        self,
        user_id: str,
        property_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Score multiple properties against user's criteria.

        Args:
            user_id: User ID
            property_ids: List of property IDs to score (if None, scores all active properties)

        Returns:
            Summary of batch scoring results
        """
        criteria = await self.get_criteria(user_id)
        if not criteria or not criteria.get("is_active"):
            return {"error": "No active criteria found"}

        # Get properties to score
        if property_ids is None:
            # Get recent properties (last 30 days)
            cutoff = datetime.utcnow() - timedelta(days=30)
            result = self.supabase.table("foreclosure_listings").select("id").gte(
                "listed_date", cutoff.isoformat()
            ).execute()
            property_ids = [p["id"] for p in result.data]

        scored = 0
        hot = 0
        warm = 0
        cold = 0
        errors = 0

        for prop_id in property_ids:
            match = await self.calculate_match_score(user_id, prop_id, criteria=criteria)
            if match:
                scored += 1
                if match["match_category"] == "hot":
                    hot += 1
                elif match["match_category"] == "warm":
                    warm += 1
                else:
                    cold += 1
            else:
                errors += 1

        return {
            "user_id": user_id,
            "total_processed": len(property_ids),
            "scored": scored,
            "hot_matches": hot,
            "warm_matches": warm,
            "cold_matches": cold,
            "errors": errors
        }

    # =========================================================================
    # ALERTS
    # =========================================================================

    async def create_match_alert(self, user_id: str, property_id: int) -> Optional[Dict[str, Any]]:
        """
        Create an alert for a matching property.

        Args:
            user_id: User ID
            property_id: Property ID

        Returns:
            Created alert or None
        """
        try:
            # Get match score
            match = await self.get_match_by_property(user_id, property_id)
            if not match:
                return None

            # Check if user has alerts enabled
            criteria = await self.get_criteria(user_id)
            if not criteria or not criteria.get("enable_alerts"):
                return None

            # Create alert
            alert_data = {
                "user_id": user_id,
                "property_id": property_id,
                "match_id": match.get("id"),
                "match_score": match.get("match_score"),
                "match_category": match.get("match_category")
            }

            result = self.supabase.table("deal_match_alerts").insert(alert_data).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error creating match alert: {e}")
            return None

    async def get_match_alerts(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get match alerts for a user"""
        try:
            query = self.supabase.table("deal_match_alerts").select(
                "*, foreclosure_listings(*)"
            ).eq("user_id", user_id)

            if unread_only:
                query = query.eq("is_read", False)

            result = query.order("created_at", desc=True).limit(limit).execute()

            return result.data

        except Exception as e:
            logger.error(f"Error getting alerts for user {user_id}: {e}")
            return []

    async def mark_alert_read(self, alert_id: int, user_id: str) -> bool:
        """Mark an alert as read"""
        try:
            self.supabase.table("deal_match_alerts").update(
                {"is_read": True, "read_at": datetime.utcnow().isoformat()}
            ).eq("id", alert_id).eq("user_id", user_id).execute()
            return True

        except Exception as e:
            logger.error(f"Error marking alert {alert_id} as read: {e}")
            return False

    # =========================================================================
    # METRICS
    # =========================================================================

    async def get_match_stats(self, user_id: str) -> Dict[str, Any]:
        """Get match statistics for a user"""
        try:
            # Get counts by category
            hot_result = self.supabase.table("property_match_scores").select(
                "id"
            ).eq("user_id", user_id).eq("match_category", "hot").execute()

            warm_result = self.supabase.table("property_match_scores").select(
                "id"
            ).eq("user_id", user_id).eq("match_category", "warm").execute()

            cold_result = self.supabase.table("property_match_scores").select(
                "id"
            ).eq("user_id", user_id).eq("match_category", "cold").execute()

            # Get unread alerts
            unread_result = self.supabase.table("deal_match_alerts").select(
                "id"
            ).eq("user_id", user_id).eq("is_read", False).execute()

            return {
                "hot_matches": len(hot_result.data),
                "warm_matches": len(warm_result.data),
                "cold_matches": len(cold_result.data),
                "total_matches": len(hot_result.data) + len(warm_result.data) + len(cold_result.data),
                "unread_alerts": len(unread_result.data)
            }

        except Exception as e:
            logger.error(f"Error getting match stats for user {user_id}: {e}")
            return {}
