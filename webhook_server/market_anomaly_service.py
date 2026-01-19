"""
Market Anomaly Detection Service

Analyzes properties for price anomalies using comparable sales data.
Validates results through AI quality monitor before flagging as "hot deals".
"""

import os
import logging
from typing import Dict, List, Optional, Any
from statistics import mean, median, stdev

from .zillow_enrichment import ZillowEnrichmentService
from .ai_quality_monitor import AIDataQualityMonitor, ValidationResult
from .feature_toggle_service import FeatureToggleService

logger = logging.getLogger(__name__)


class MarketAnomalyService:
    """
    Analyzes properties for price anomalies.

    Uses Zillow comparable sales to:
    1. Calculate z-score for price deviation
    2. Estimate market value
    3. Flag potential "hot deals" (underpriced properties)
    4. Validate results through quality monitor
    """

    def __init__(self):
        self.zillow_service = ZillowEnrichmentService()
        self.feature_service = FeatureToggleService()

    async def _get_quality_monitor(self) -> AIDataQualityMonitor:
        """Get quality monitor with current thresholds"""
        thresholds = await self.feature_service.get_ai_quality_thresholds()
        return AIDataQualityMonitor(thresholds)

    async def analyze_property(
        self,
        property_id: int,
        address: str,
        list_price: float,
        county_id: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a property for price anomaly.

        Args:
            property_id: Internal property ID
            address: Property address (for Zillow lookup)
            list_price: Current listing price
            county_id: Optional county ID for feature toggles
            user_id: Optional user ID for feature preferences

        Returns:
            Analysis results or None if feature disabled or validation fails
        """
        # Check if feature is enabled
        enabled = await self.feature_service.is_feature_enabled(
            "market_anomaly_detection",
            user_id=user_id,
            county_id=county_id
        )

        if not enabled:
            logger.debug("Market anomaly detection feature is disabled")
            return None

        try:
            # Get Zillow property data
            zillow_data = await self.zillow_service.get_property_by_address(address)

            # Get comparable properties
            comps = await self._get_comparables(zillow_data)

            if not comps:
                logger.warning(f"No comparables found for property {property_id}")
                return None

            # Calculate statistics
            analysis = await self._calculate_anomaly(
                property_id,
                zillow_data,
                comps,
                list_price
            )

            # Validate through quality monitor
            quality_monitor = await self._get_quality_monitor()
            validation = await quality_monitor.validate_market_anomaly(analysis)

            if not validation.is_safe_to_show:
                logger.info(
                    f"Property {property_id} analysis did not pass quality checks: "
                    f"{validation.errors}"
                )
                # Still return analysis but mark as failed validation
                analysis["passed_quality_checks"] = False
                analysis["quality_check_warnings"] = validation.errors
            else:
                analysis["passed_quality_checks"] = True
                analysis["quality_check_warnings"] = []

            # Store in database
            await self._save_analysis(property_id, analysis)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing property {property_id}: {e}")
            return None

    async def _get_comparables(
        self,
        zillow_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get comparable properties from Zillow.

        Uses /similar endpoint to find nearby similar properties.
        """
        zpid = zillow_data.get("zpid")
        if not zpid:
            return []

        try:
            similar_data = await self.zillow_service.get_similar_properties(zpid)

            # Filter for sold/comparable properties with prices
            comps = []
            for prop in similar_data.get("similarProperties", []):
                price = prop.get("price")
                if price:
                    comps.append({
                        "zpid": prop.get("zpid"),
                        "address": prop.get("address"),
                        "price": price,
                        "bedrooms": prop.get("bedrooms"),
                        "bathrooms": prop.get("bathrooms"),
                        "square_feet": prop.get("livingArea"),
                        "distance": prop.get("distance")  # if available
                    })

            return comps

        except Exception as e:
            logger.error(f"Error fetching comparables: {e}")
            return []

    async def _calculate_anomaly(
        self,
        property_id: int,
        zillow_data: Dict[str, Any],
        comps: List[Dict[str, Any]],
        list_price: float
    ) -> Dict[str, Any]:
        """
        Calculate price anomaly statistics.

        Returns analysis dictionary with:
        - is_anomaly: bool
        - anomaly_type: 'underpriced' | 'overpriced' | 'within_range'
        - z_score: float
        - confidence_score: float (0-1)
        - price_difference_percent: float
        - estimated_market_value: float
        - comparable_count: int
        """
        if len(comps) < 3:
            # Not enough data for meaningful analysis
            return {
                "property_id": property_id,
                "is_anomaly": False,
                "anomaly_type": "insufficient_data",
                "z_score": 0,
                "confidence_score": 0,
                "price_difference_percent": 0,
                "comparable_count": len(comps),
                "comparable_prices": [],
                "comparable_avg_price": list_price,
                "comparable_median_price": list_price,
                "comparable_price_std_dev": 0,
                "estimated_market_value": list_price,
                "ai_reasoning": "Insufficient comparable properties for analysis"
            }

        # Extract prices
        comp_prices = [c["price"] for c in comps]

        # Calculate statistics
        avg_price = mean(comp_prices)
        median_price = median(comp_prices)

        if len(comp_prices) > 1:
            price_std_dev = stdev(comp_prices)
        else:
            price_std_dev = 0

        # Calculate z-score
        if price_std_dev > 0:
            z_score = (list_price - avg_price) / price_std_dev
        else:
            z_score = 0

        # Determine anomaly type
        # Under z-score threshold = underpriced (potential hot deal)
        # Above z-score threshold = overpriced
        quality_monitor = await self._get_quality_monitor()
        thresholds = await self.feature_service.get_ai_quality_thresholds()
        anomaly_thresholds = thresholds.get("anomaly", {})
        max_zscore = anomaly_thresholds.get("max_zscore", 2.50)
        min_diff_percent = anomaly_thresholds.get("min_price_diff_percent", 15.00)

        # Calculate price difference percentage
        price_diff_percent = ((list_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0

        if z_score <= -max_zscore and abs(price_diff_percent) >= min_diff_percent:
            anomaly_type = "underpriced"
            is_anomaly = True
        elif z_score >= max_zscore and abs(price_diff_percent) >= min_diff_percent:
            anomaly_type = "overpriced"
            is_anomaly = True
        else:
            anomaly_type = "within_range"
            is_anomaly = False

        # Calculate confidence score
        # More comps = higher confidence
        # Lower std dev = higher confidence
        base_confidence = min(len(comps) / 10, 1.0)  # Max at 10 comps
        consistency_adjustment = max(1 - (price_std_dev / avg_price), 0) if avg_price > 0 else 0
        confidence_score = base_confidence * 0.7 + consistency_adjustment * 0.3

        # Estimated market value (using median as more robust to outliers)
        estimated_value = median_price

        # Calculate value range (95% confidence interval ≈ 2 std dev)
        value_range_low = max(avg_price - 2 * price_std_dev, 0)
        value_range_high = avg_price + 2 * price_std_dev

        return {
            "property_id": property_id,
            "is_anomaly": is_anomaly,
            "anomaly_type": anomaly_type,
            "z_score": round(z_score, 3),
            "confidence_score": round(confidence_score, 3),
            "price_difference_percent": round(price_diff_percent, 2),
            "estimated_market_value": round(estimated_value, 2),
            "estimated_value_range_low": round(value_range_low, 2),
            "estimated_value_range_high": round(value_range_high, 2),
            "comparable_count": len(comps),
            "comparable_avg_price": round(avg_price, 2),
            "comparable_median_price": round(median_price, 2),
            "comparable_price_std_dev": round(price_std_dev, 2),
            "comparable_prices": comp_prices,
            "ai_reasoning": self._generate_reasoning(
                anomaly_type,
                price_diff_percent,
                len(comps),
                confidence_score
            ),
            "ai_disclaimer": "This analysis is based on available comparable properties "
                            "and should be used for informational purposes only. "
                            "Always conduct your own due diligence."
        }

    def _generate_reasoning(
        self,
        anomaly_type: str,
        price_diff_percent: float,
        comp_count: int,
        confidence_score: float
    ) -> str:
        """Generate human-readable reasoning for the analysis"""
        if anomaly_type == "insufficient_data":
            return "Insufficient comparable properties for reliable analysis."

        if anomaly_type == "underpriced":
            return (f"This property is listed {abs(price_diff_percent):.1f}% below the "
                   f"average of {comp_count} comparable properties. This may indicate "
                   f"a potential opportunity. Analysis confidence: {confidence_score:.1%}.")
        elif anomaly_type == "overpriced":
            return (f"This property is listed {price_diff_percent:.1f}% above the "
                   f"average of {comp_count} comparable properties. This may indicate "
                   f"pricing above market value.")
        else:
            return (f"This property is priced within the normal range compared to "
                   f"{comp_count} comparable properties ({price_diff_percent:+.1f}% "
                   f"difference from average).")

    async def _save_analysis(self, property_id: int, analysis: Dict[str, Any]) -> None:
        """Save analysis to database - mapping to actual DB schema"""
        from supabase import create_client

        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        # Map anomaly_type to database enum values
        # DB enum: 'below_market', 'above_market', 'price_drop', 'rapid_appreciation'
        anomaly_type_map = {
            "underpriced": "below_market",
            "overpriced": "above_market",
            "within_range": "below_market",  # Default for non-anomalies
            "insufficient_data": "below_market"
        }
        db_anomaly_type = anomaly_type_map.get(analysis.get("anomaly_type", "within_range"), "below_market")

        # Prepare data for database (matching actual schema)
        db_data = {
            "property_id": property_id,
            "anomaly_type": db_anomaly_type,
            "expected_price": analysis.get("estimated_market_value"),
            "actual_price": analysis.get("list_price"),
            "price_diff_percent": analysis.get("price_difference_percent"),
            "z_score": analysis.get("z_score"),
            "comp_count": analysis.get("comparable_count"),
            "comp_avg_price": analysis.get("comparable_avg_price"),
            "comp_median_price": analysis.get("comparable_median_price"),
            "comp_std_dev": analysis.get("comparable_price_std_dev"),
            "comp_zpids": analysis.get("comparable_prices", []),
            "confidence_score": analysis.get("confidence_score"),
            "data_quality_flags": {
                "passed_quality_checks": analysis.get("passed_quality_checks", True),
                "warnings": analysis.get("quality_check_warnings", []),
                "ai_reasoning": analysis.get("ai_reasoning"),
                "ai_disclaimer": analysis.get("ai_disclaimer")
            }
        }

        try:
            supabase.table("market_anomalies").insert(db_data).execute()
            logger.info(f"Saved market anomaly analysis for property {property_id}")
        except Exception as e:
            logger.error(f"Error saving analysis for property {property_id}: {e}")

    async def get_property_anomaly(
        self,
        property_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get existing anomaly analysis for a property"""
        from supabase import create_client

        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            result = supabase.table("market_anomalies").select("*").eq("property_id", property_id).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error fetching anomaly analysis for property {property_id}: {e}")
            return None

    async def get_anomalies_batch(
        self,
        county_id: Optional[int] = None,
        limit: int = 50,
        only_anomalies: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get batch of market anomalies for listing.

        Args:
            county_id: Optional county filter
            limit: Maximum results
            only_anomalies: If True, only return properties flagged as anomalies

        Returns:
            List of anomaly analyses
        """
        from supabase import create_client

        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            query = supabase.table("market_anomalies").select("*")

            if only_anomalies:
                query = query.eq("is_anomaly", True)

            if county_id:
                # Join with properties table
                query = query.select("*, properties(*)")

            query = query.order("created_at", desc=True).limit(limit)

            result = query.execute()
            return result.data

        except Exception as e:
            logger.error(f"Error fetching anomalies batch: {e}")
            return []

    async def update_verification(
        self,
        anomaly_id: int,
        user_id: str,
        is_verified: Optional[bool] = None,
        feedback: Optional[str] = None
    ) -> bool:
        """
        Update human verification of an anomaly.

        Used for feedback loop to improve detection accuracy.
        """
        from supabase import create_client
        from datetime import datetime

        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            updates = {
                "verified_by_user_id": user_id,
                "verified_at": datetime.utcnow().isoformat()
            }

            if is_verified is not None:
                updates["is_verified"] = is_verified

            if feedback:
                updates["user_feedback"] = feedback

            supabase.table("market_anomalies").update(updates).eq("id", anomaly_id).execute()
            logger.info(f"Updated verification for anomaly {anomaly_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating verification for anomaly {anomaly_id}: {e}")
            return False

    async def get_anomalies_for_property(
        self,
        property_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all anomaly analyses for a property (called by investment_service).

        Returns list of all anomaly records for the property.
        """
        from supabase import create_client

        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            result = supabase.table("market_anomalies").select("*").eq("property_id", property_id).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error fetching anomalies for property {property_id}: {e}")
            return []
