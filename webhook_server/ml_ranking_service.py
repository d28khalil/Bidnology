"""
ML-Based Property Ranking Service

Personalized property ranking for foreclosure investors using:
- Per-user investment criteria
- Feature extraction from property data
- Confidence-weighted scoring (handles incomplete Zillow data)
- Human feedback loop for continuous improvement
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from statistics import mean
from decimal import Decimal
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class MLRankingService:
    """
    Service for ML-based property ranking with personalization.

    Calculates property scores based on:
    - Price-to-value ratio (upset price vs estimated value)
    - Market anomaly detection (Z-score)
    - Urgency (days to auction)
    - Property type preferences
    - Price range preferences
    - Location preferences

    Uses confidence-weighted scoring to gracefully handle incomplete data.
    """

    # Feature weights (will be overridden by model_weights table)
    DEFAULT_WEIGHTS = {
        "price_to_value": 0.35,
        "anomaly": 0.20,
        "urgency": 0.15,
        "property_type": 0.10,
        "price_range": 0.10,
        "location_score": 0.10
    }

    # Scoring thresholds
    PRICE_TO_VALUE_EXCELLENT = 0.60  # 60% or below = excellent
    PRICE_TO_VALUE_GOOD = 0.70
    PRICE_TO_VALUE_FAIR = 0.85

    ANOMALY_EXCELLENT_ZSCORE = -2.5
    ANOMALY_GOOD_ZSCORE = -2.0
    ANOMALY_FAIR_ZSCORE = -1.5

    URGENCY_URGENT_DAYS = 7
    URGENCY_SOON_DAYS = 14
    URGENCY_NORMAL_DAYS = 30

    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

    # ========================================================================
    # USER CRITERIA MANAGEMENT
    # ========================================================================

    async def get_investor_criteria(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user's investment criteria for personalization"""
        result = self.supabase.table("deal_intelligence_investor_criteria").select(
            "*"
        ).eq("user_id", user_id).eq("is_active", True).execute()

        if result.data:
            return result.data[0]
        return None

    async def upsert_investor_criteria(
        self,
        user_id: str,
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create or update user's investment criteria"""
        # Check if exists
        existing = await self.get_investor_criteria(user_id)

        criteria["user_id"] = user_id
        criteria["updated_at"] = datetime.utcnow().isoformat()

        if existing:
            # Update
            result = self.supabase.table("deal_intelligence_investor_criteria").update(
                criteria
            ).eq("user_id", user_id).execute()
        else:
            # Insert
            criteria["created_at"] = datetime.utcnow().isoformat()
            result = self.supabase.table("deal_intelligence_investor_criteria").insert(
                criteria
            ).execute()

        return result.data[0] if result.data else {}

    # ========================================================================
    # RANKING CALCULATION
    # ========================================================================

    async def calculate_property_score(
        self,
        property_id: int,
        user_id: str,
        model_weights_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate personalized ranking score for a property.

        Returns:
            Score breakdown with confidence, or None if property not found
        """
        # Get property data
        property_result = self.supabase.table("foreclosure_listings").select(
            "*"
        ).eq("id", property_id).execute()

        if not property_result.data:
            logger.warning(f"Property {property_id} not found")
            return None

        property_data = property_result.data[0]

        # Get user criteria
        user_criteria = await self.get_investor_criteria(user_id)

        # Get model weights
        weights = await self._get_model_weights(model_weights_id)

        # Extract features and calculate scores
        scoring_result = await self._calculate_feature_scores(
            property_data, user_criteria, weights
        )

        # Store ranking history
        await self._store_ranking_history(
            user_id, property_id, scoring_result, model_weights_id
        )

        return scoring_result

    async def rank_properties_for_user(
        self,
        user_id: str,
        property_ids: Optional[List[int]] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank multiple properties for a user.

        Args:
            user_id: User ID
            property_ids: Specific properties to rank (None = all active)
            limit: Max results
            filters: Optional filters (county, price range, etc.)

        Returns:
            Ranked list of properties with scores
        """
        # Get properties to rank
        if property_ids:
            # Use provided list
            properties = []
            for pid in property_ids:
                result = self.supabase.table("foreclosure_listings").select(
                    "*"
                ).eq("id", pid).execute()
                if result.data:
                    properties.append(result.data[0])
        else:
            # Query all active properties with optional filters
            query = self.supabase.table("foreclosure_listings").select("*")

            if filters:
                if "county_id" in filters:
                    query = query.eq("county_id", filters["county_id"])
                if "min_price" in filters:
                    query = query.gte("opening_bid", filters["min_price"])
                if "max_price" in filters:
                    query = query.lte("opening_bid", filters["max_price"])

            result = query.limit(limit * 2).execute()  # Get more than needed
            properties = result.data if result.data else []

        # Get user criteria and model weights
        user_criteria = await self.get_investor_criteria(user_id)
        weights = await self._get_model_weights()

        # Score each property
        scored_properties = []
        for prop in properties[:limit]:
            scoring_result = await self._calculate_feature_scores(
                prop, user_criteria, weights
            )

            # Add property details
            scoring_result["property"] = {
                "id": prop.get("id"),
                "address": prop.get("address"),
                "city": prop.get("city"),
                "county": prop.get("county"),
                "opening_bid": prop.get("opening_bid"),
                "sale_date": prop.get("sale_date"),
                "zillow_data": prop.get("zillow_data", {})
            }

            scored_properties.append(scoring_result)

        # Sort by score descending
        scored_properties.sort(
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        # Update attention scores for implicit feedback
        await self._update_attention_scores(user_id, scored_properties)

        return scored_properties

    # ========================================================================
    # FEATURE EXTRACTION & SCORING
    # ========================================================================

    async def _calculate_feature_scores(
        self,
        property_data: Dict,
        user_criteria: Optional[Dict],
        model_weights: Dict
    ) -> Dict[str, Any]:
        """
        Calculate individual feature scores and overall ranking score.

        Returns comprehensive scoring with confidence metrics.
        """
        features = {}
        feature_confidence = {}

        # 1. Price-to-Value Score
        price_to_value, p_conf = self._score_price_to_value(
            property_data, user_criteria
        )
        features["price_to_value"] = price_to_value
        feature_confidence["price_to_value"] = p_conf

        # 2. Anomaly Score
        anomaly, a_conf = self._score_anomaly(property_data)
        features["anomaly"] = anomaly
        feature_confidence["anomaly"] = a_conf

        # 3. Urgency Score
        urgency, u_conf = self._score_urgency(
            property_data, user_criteria
        )
        features["urgency"] = urgency
        feature_confidence["urgency"] = u_conf

        # 4. Property Type Score
        prop_type, pt_conf = self._score_property_type(
            property_data, user_criteria
        )
        features["property_type"] = prop_type
        feature_confidence["property_type"] = pt_conf

        # 5. Price Range Score
        price_range, pr_conf = self._score_price_range(
            property_data, user_criteria
        )
        features["price_range"] = price_range
        feature_confidence["price_range"] = pr_conf

        # 6. Location Score
        location, l_conf = self._score_location(
            property_data, user_criteria
        )
        features["location_score"] = location
        feature_confidence["location_score"] = l_conf

        # Calculate weighted score
        weights = model_weights.get("weights", self.DEFAULT_WEIGHTS)
        overall_score = 0.0
        total_weight = 0.0

        for feature_name, weight in weights.items():
            if feature_name in features:
                overall_score += features[feature_name] * weight
                total_weight += weight

        # Normalize score
        if total_weight > 0:
            overall_score = overall_score / total_weight
        else:
            overall_score = 0.0

        # Calculate confidence (weighted average of feature confidence)
        overall_confidence = 0.0
        conf_weight = 0.0
        for feature_name, weight in weights.items():
            if feature_name in feature_confidence:
                overall_confidence += feature_confidence[feature_name] * weight
                conf_weight += weight

        if conf_weight > 0:
            overall_confidence = overall_confidence / conf_weight
        else:
            overall_confidence = 0.0

        # Determine data quality level
        data_quality = self._determine_data_quality(overall_confidence, features)

        # Identify missing features
        missing_features = [
            fn for fn, fc in feature_confidence.items()
            if fc == 0.0
        ]

        return {
            "property_id": property_data.get("id"),
            "score": round(overall_score, 2),
            "confidence": round(overall_confidence, 3),
            "data_quality": data_quality,
            "breakdown": {
                "price_to_value": {
                    "score": round(price_to_value, 2),
                    "confidence": round(p_conf, 3)
                },
                "anomaly": {
                    "score": round(anomaly, 2),
                    "confidence": round(a_conf, 3)
                },
                "urgency": {
                    "score": round(urgency, 2),
                    "confidence": round(u_conf, 3)
                },
                "property_type": {
                    "score": round(prop_type, 2),
                    "confidence": round(pt_conf, 3)
                },
                "price_range": {
                    "score": round(price_range, 2),
                    "confidence": round(pr_conf, 3)
                },
                "location_score": {
                    "score": round(location, 2),
                    "confidence": round(l_conf, 3)
                }
            },
            "missing_features": missing_features,
            "calculated_at": datetime.utcnow().isoformat()
        }

    def _score_price_to_value(
        self,
        property_data: Dict,
        user_criteria: Optional[Dict]
    ) -> Tuple[float, float]:
        """
        Calculate price-to-value score (0-100).

        Higher is better - lower upset price relative to estimated value.
        """
        upset_price = (
            property_data.get("opening_bid") or
            property_data.get("approx_upset") or
            property_data.get("judgment_amount")
        )

        zillow_data = property_data.get("zillow_data", {})
        zestimate = zillow_data.get("zestimate") or zillow_data.get("price")

        if not upset_price or not zestimate:
            return 0.0, 0.0  # No confidence without data

        # Calculate ratio
        ratio = upset_price / zestimate if zestimate > 0 else 1.0

        # Score based on thresholds
        if ratio <= self.PRICE_TO_VALUE_EXCELLENT:
            score = 100.0
        elif ratio <= self.PRICE_TO_VALUE_GOOD:
            # Interpolate between excellent and good
            score = 85.0 - (ratio - self.PRICE_TO_VALUE_EXCELLENT) / (
                self.PRICE_TO_VALUE_GOOD - self.PRICE_TO_VALUE_EXCELLENT
            ) * 15.0
        elif ratio <= self.PRICE_TO_VALUE_FAIR:
            # Interpolate between good and fair
            score = 70.0 - (ratio - self.PRICE_TO_VALUE_GOOD) / (
                self.PRICE_TO_VALUE_FAIR - self.PRICE_TO_VALUE_GOOD
            ) * 25.0
        elif ratio <= 1.0:
            # Below market value
            score = 50.0 - (ratio - self.PRICE_TO_VALUE_FAIR) / (
                1.0 - self.PRICE_TO_VALUE_FAIR
            ) * 20.0
        else:
            # Over market value
            score = max(0.0, 30.0 - (ratio - 1.0) * 50.0)

        # Apply user criteria if available
        if user_criteria:
            min_arv_pct = user_criteria.get("min_arv_percentage")
            if min_arv_pct:
                # User wants minimum ARV as % of upset price
                required_ratio = 100.0 / min_arv_pct
                if ratio > required_ratio:
                    score *= 0.5  # Penalize if doesn't meet ARV target

        return round(score, 2), 0.95  # High confidence with zestimate

    def _score_anomaly(self, property_data: Dict) -> Tuple[float, float]:
        """
        Calculate anomaly score based on market anomaly detection.

        Uses pre-calculated anomaly data if available.
        """
        property_id = property_data.get("id")

        # Get existing anomaly detection
        result = self.supabase.table("market_anomalies").select(
            "*"
        ).eq("property_id", property_id).order(
            "detected_at", desc=True
        ).limit(1).execute()

        confidence = 0.5  # Default confidence without anomaly data

        if result.data:
            anomaly = result.data[0]
            z_score = anomaly.get("z_score", 0)
            anomaly_confidence = anomaly.get("confidence_score", 0)

            if anomaly.get("anomaly_type") == "insufficient_data":
                return 0.0, 0.0

            # Score based on Z-score (negative is good - underpriced)
            if z_score <= self.ANOMALY_EXCELLENT_ZSCORE:
                score = 100.0
            elif z_score <= self.ANOMALY_GOOD_ZSCORE:
                score = 85.0
            elif z_score <= self.ANOMALY_FAIR_ZSCORE:
                score = 70.0
            elif z_score < 0:
                score = 50.0
            else:
                score = max(0.0, 50.0 - z_score * 10.0)

            # Boost by anomaly detection confidence
            confidence = max(0.3, anomaly_confidence)

            return round(score, 2), round(confidence, 3)

        return 0.0, 0.0

    def _score_urgency(
        self,
        property_data: Dict,
        user_criteria: Optional[Dict]
    ) -> Tuple[float, float]:
        """
        Calculate urgency score based on days to auction.

        Higher score = more urgent (sooner auction).
        """
        sale_date_str = property_data.get("sale_date")

        if not sale_date_str:
            return 0.0, 0.0

        try:
            sale_date = datetime.fromisoformat(
                sale_date_str.replace("Z", "+00:00")
            )
        except (ValueError, TypeError) as date_err:
            logger.warning(f"Invalid sale_date format '{sale_date_str}' for urgency scoring: {date_err}")
            return 0.0, 0.0

        days_to_auction = (sale_date - datetime.utcnow()).days

        if days_to_auction < 0:
            return 0.0, 1.0  # Past auction, no urgency

        # Get user's preferred urgency
        preferred_days = None
        if user_criteria:
            preferred_days = user_criteria.get("ideal_days_to_auction")

        # Score based on days remaining
        if days_to_auction <= self.URGENCY_URGENT_DAYS:
            score = 100.0
        elif days_to_auction <= self.URGENCY_SOON_DAYS:
            score = 85.0
        elif days_to_auction <= self.URGENCY_NORMAL_DAYS:
            score = 70.0
        else:
            # Less urgent as days increase
            score = max(40.0, 70.0 - (days_to_auction - 30) * 0.5)

        # Adjust based on user preference
        if preferred_days:
            diff = abs(days_to_auction - preferred_days)
            if diff <= 3:
                score = min(100.0, score + 20.0)  # Bonus for matching preference
            elif diff > 14:
                score *= 0.7  # Penalize if far from preference

        return round(min(score, 100.0), 2), 1.0

    def _score_property_type(
        self,
        property_data: Dict,
        user_criteria: Optional[Dict]
    ) -> Tuple[float, float]:
        """
        Calculate property type preference match score.
        """
        property_type = property_data.get("property_type", "").lower()

        if not property_type or not user_criteria:
            return 50.0, 0.5  # Neutral score without data

        preferred_types = user_criteria.get("preferred_property_types", [])

        if not preferred_types:
            return 50.0, 0.5  # No preference set

        # Normalize to lower case for comparison
        preferred_types = [t.lower() for t in preferred_types]

        if property_type in preferred_types:
            return 100.0, 1.0
        else:
            # Check if similar types
            type_mapping = {
                "single_family": ["single", "sfr", "house"],
                "multi_family": ["multi", "duplex", "triplex", "fourplex"],
                "condo": ["condominium", "unit"],
                "townhouse": ["townhome"]
            }

            for pref_type, aliases in type_mapping.items():
                if pref_type in preferred_types:
                    if property_type in aliases or any(
                        alias in property_type for alias in aliases
                    ):
                        return 75.0, 0.7

            return 30.0, 0.3  # Not preferred

    def _score_price_range(
        self,
        property_data: Dict,
        user_criteria: Optional[Dict]
    ) -> Tuple[float, float]:
        """
        Calculate price range preference match score.
        """
        price = (
            property_data.get("opening_bid") or
            property_data.get("approx_upset")
        )

        if not price or not user_criteria:
            return 50.0, 0.5

        min_price = user_criteria.get("min_upset_price")
        max_price = user_criteria.get("max_upset_price")

        if not min_price and not max_price:
            return 50.0, 0.5  # No preference

        # Check if in range
        in_range = True
        if min_price and price < min_price:
            in_range = False
        if max_price and price > max_price:
            in_range = False

        if in_range:
            # Bonus for being in "sweet spot" (middle of range)
            if min_price and max_price:
                range_mid = (min_price + max_price) / 2
                distance_from_mid = abs(price - range_mid) / (max_price - min_price)
                score = 100.0 - distance_from_mid * 20.0
                return round(score, 2), 1.0
            return 100.0, 1.0
        else:
            # Calculate how far outside range
            if min_price and price < min_price:
                diff_pct = (min_price - price) / min_price
            elif max_price and price > max_price:
                diff_pct = (price - max_price) / max_price
            else:
                diff_pct = 0.1

            score = max(0.0, 50.0 - diff_pct * 100.0)
            return round(score, 2), 0.5

    def _score_location(
        self,
        property_data: Dict,
        user_criteria: Optional[Dict]
    ) -> Tuple[float, float]:
        """
        Calculate location preference match score.
        """
        county_id = property_data.get("county_id")
        city = property_data.get("city", "").lower()

        if not user_criteria:
            return 50.0, 0.5

        preferred_counties = user_criteria.get("preferred_counties", [])
        preferred_cities = user_criteria.get("preferred_cities", [])
        exclude_areas = user_criteria.get("exclude_areas", [])

        # Check excluded areas first
        if exclude_areas:
            if city in [e.lower() for e in exclude_areas]:
                return 0.0, 1.0  # Definitely excluded

        # Check county preference
        if preferred_counties and county_id:
            if county_id in preferred_counties:
                return 100.0, 1.0

        # Check city preference
        if preferred_cities and city:
            if city in [c.lower() for c in preferred_cities]:
                return 100.0, 1.0

        # No strong preference match
        if preferred_counties or preferred_cities:
            return 40.0, 0.5

        return 50.0, 0.5

    def _determine_data_quality(
        self,
        confidence: float,
        features: Dict[str, float]
    ) -> str:
        """Determine data quality level based on confidence and features."""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        elif confidence >= 0.2:
            return "low"
        else:
            return "incomplete"

    # ========================================================================
    # MODEL WEIGHTS MANAGEMENT
    # ========================================================================

    async def _get_model_weights(
        self,
        weights_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get active model weights"""
        if weights_id:
            result = self.supabase.table("deal_intelligence_model_weights").select(
                "*"
            ).eq("id", weights_id).execute()
        else:
            result = self.supabase.table("deal_intelligence_model_weights").select(
                "*"
            ).eq("is_active", True).order(
                "created_at", desc=True
            ).limit(1).execute()

        if result.data:
            return result.data[0]
        return {"weights": self.DEFAULT_WEIGHTS}

    # ========================================================================
    # FEEDBACK & LEARNING
    # ========================================================================

    async def record_feedback(
        self,
        user_id: str,
        property_id: int,
        is_positive: bool,
        feedback_type: str,
        ranking_position: Optional[int] = None,
        user_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record user feedback for continuous learning.

        Used to improve ranking model over time.
        """
        # Get current model version
        model_weights = await self._get_model_weights()
        model_version = model_weights.get("model_version", "1.0")

        # Get property snapshot at time of feedback
        property_result = self.supabase.table("foreclosure_listings").select(
            "id, address, city, county, opening_bid, sale_date, zillow_data"
        ).eq("id", property_id).execute()

        property_snapshot = property_result.data[0] if property_result.data else {}

        feedback = {
            "user_id": user_id,
            "property_id": property_id,
            "is_positive": is_positive,
            "ranking_position_at_feedback": ranking_position,
            "feedback_type": feedback_type,
            "user_action": user_action,
            "model_version": model_version,
            "property_snapshot": property_snapshot
        }

        result = self.supabase.table("deal_intelligence_feedback").insert(
            feedback
        ).execute()

        # Update feature importance based on feedback
        await self._update_feature_importance(feedback, property_snapshot)

        return result.data[0] if result.data else {}

    async def _update_feature_importance(
        self,
        feedback: Dict[str, Any],
        property_snapshot: Dict[str, Any]
    ):
        """Update feature importance based on feedback"""
        # This would analyze which features correlated with positive feedback
        # For now, placeholder for future implementation
        pass

    # ========================================================================
    # ATTENTION SCORING (IMPLICIT FEEDBACK)
    # ========================================================================

    async def _update_attention_scores(
        self,
        user_id: str,
        scored_properties: List[Dict]
    ):
        """Update attention scores for implicit feedback tracking"""
        for idx, prop in enumerate(scored_properties):
            property_id = prop.get("property_id")
            score = prop.get("score", 0)

            # Check if exists
            result = self.supabase.table("deal_intelligence_attention_scores").select(
                "*"
            ).eq("user_id", user_id).eq("property_id", property_id).execute()

            if result.data:
                # Update
                existing = result.data[0]
                new_score = existing.get("attention_score", 0) + score / 100.0

                self.supabase.table("deal_intelligence_attention_scores").update({
                    "view_count": existing.get("view_count", 0) + 1,
                    "last_viewed_at": datetime.utcnow().isoformat(),
                    "attention_score": round(new_score, 2),
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", existing["id"]).execute()
            else:
                # Insert
                self.supabase.table("deal_intelligence_attention_scores").insert({
                    "user_id": user_id,
                    "property_id": property_id,
                    "view_count": 1,
                    "first_viewed_at": datetime.utcnow().isoformat(),
                    "last_viewed_at": datetime.utcnow().isoformat(),
                    "first_seen_ranking_position": idx + 1,
                    "attention_score": round(score / 100.0, 2)
                }).execute()

    # ========================================================================
    # HISTORY TRACKING
    # ========================================================================

    async def _store_ranking_history(
        self,
        user_id: str,
        property_id: int,
        scoring_result: Dict,
        model_weights_id: Optional[int]
    ):
        """Store ranking calculation for analytics"""
        history = {
            "user_id": user_id,
            "property_id": property_id,
            "score": scoring_result.get("score"),
            "confidence": scoring_result.get("confidence"),
            "data_quality": scoring_result.get("data_quality"),
            "breakdown": scoring_result.get("breakdown"),
            "missing_features": scoring_result.get("missing_features", []),
            "model_weights_id": model_weights_id
        }

        self.supabase.table("deal_intelligence_ranking_history").insert(
            history
        ).execute()

    async def get_ranking_history(
        self,
        user_id: str,
        property_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get ranking history for analytics"""
        query = self.supabase.table("deal_intelligence_ranking_history").select(
            "*"
        ).eq("user_id", user_id)

        if property_id:
            query = query.eq("property_id", property_id)

        result = query.order("calculated_at", desc=True).limit(limit).execute()

        return result.data if result.data else []
