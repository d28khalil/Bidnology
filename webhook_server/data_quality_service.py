"""
Data Quality Scoring Service

Analyzes enrichment data completeness and calculates quality scores
for foreclosure properties to help users assess data reliability.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

from supabase import create_client

logger = logging.getLogger(__name__)


# Quality thresholds
HIGH_QUALITY_THRESHOLD = 0.80
MEDIUM_QUALITY_THRESHOLD = 0.50


class DataQualityService:
    """
    Service for analyzing and scoring property data quality.

    Features:
    - Calculate overall data quality scores
    - Analyze enrichment completeness
    - Identify missing or incomplete data fields
    - Provide quality recommendations
    """

    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        self.supabase = create_client(supabase_url, supabase_key)

    # =========================================================================
    # QUALITY SCORING
    # =========================================================================

    async def calculate_quality_score(
        self,
        property_id: int,
        property_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate comprehensive data quality score for a property.

        Args:
            property_id: Property ID
            property_data: Optional property data (if None, will fetch)

        Returns:
            Quality score dict with breakdown and recommendations
        """
        try:
            # Fetch property if not provided
            if property_data is None:
                result = self.supabase.table("foreclosure_listings").select("*").eq("id", property_id).execute()
                if not result.data:
                    return None
                property_data = result.data[0]

            # Calculate individual category scores
            base_data_score = self._score_base_data(property_data)
            enrichment_score = self._score_enrichment_data(property_data)
            comps_score = self._score_comparable_data(property_data)
            media_score = self._score_media_data(property_data)
            market_score = self._score_market_data(property_data)

            # Calculate weighted overall score
            weights = {
                "base": 0.25,
                "enrichment": 0.30,
                "comps": 0.25,
                "media": 0.10,
                "market": 0.10
            }

            overall_score = (
                base_data_score * weights["base"] +
                enrichment_score * weights["enrichment"] +
                comps_score * weights["comps"] +
                media_score * weights["media"] +
                market_score * weights["market"]
            )

            # Determine quality tier
            if overall_score >= HIGH_QUALITY_THRESHOLD:
                quality_tier = "high"
            elif overall_score >= MEDIUM_QUALITY_THRESHOLD:
                quality_tier = "medium"
            else:
                quality_tier = "low"

            # Build score breakdown
            score_breakdown = {
                "overall_score": round(overall_score, 4),
                "quality_tier": quality_tier,
                "base_data_score": round(base_data_score, 4),
                "enrichment_score": round(enrichment_score, 4),
                "comps_score": round(comps_score, 4),
                "media_score": round(media_score, 4),
                "market_score": round(market_score, 4),
                "weights": weights
            }

            # Identify missing fields and recommendations
            missing_fields = self._identify_missing_fields(property_data)
            recommendations = self._generate_recommendations(
                base_data_score, enrichment_score, comps_score,
                media_score, market_score, missing_fields
            )

            # Build result
            result = {
                "property_id": property_id,
                "calculated_at": datetime.utcnow().isoformat(),
                "score_breakdown": score_breakdown,
                "overall_quality_score": round(overall_score, 4),
                "quality_tier": quality_tier,
                "is_safe_to_show": overall_score >= MEDIUM_QUALITY_THRESHOLD,
                "missing_fields": missing_fields,
                "recommendations": recommendations,
                "data_completeness": {
                    "base_fields_complete": round(base_data_score * 100, 1),
                    "enrichment_fields_complete": round(enrichment_score * 100, 1),
                    "comps_available": self._has_comparable_data(property_data),
                    "photos_available": self._has_photos(property_data),
                    "market_data_available": self._has_market_data(property_data)
                }
            }

            # Store in enrichment data
            await self._store_quality_score(property_id, result)

            return result

        except Exception as e:
            logger.error(f"Error calculating quality score for property {property_id}: {e}")
            return None

    def _score_base_data(self, property_data: Dict) -> float:
        """Score core property data completeness"""
        required_fields = [
            "property_address", "city", "state", "zip",
            "upset_price", "attorney", "plaintiff",
            "auction_date", "county_id"
        ]

        present = sum(1 for field in required_fields if property_data.get(field))
        return present / len(required_fields)

    def _score_enrichment_data(self, property_data: Dict) -> float:
        """Score Zillow enrichment data completeness"""
        zillow_fields = [
            "zpid", "bedrooms", "bathrooms", "sqft",
            "year_built", "lot_size", "zestimate", "rent_zestimate",
            "property_type"
        ]

        present = sum(1 for field in zillow_fields if property_data.get(field))
        return present / len(zillow_fields)

    def _score_comparable_data(self, property_data: Dict) -> float:
        """Score comparable sales data"""
        comps = property_data.get("comps")

        if not comps:
            return 0.0

        if len(comps) >= 5:
            return 1.0
        elif len(comps) >= 3:
            return 0.75
        elif len(comps) >= 1:
            return 0.5
        else:
            return 0.0

    def _score_media_data(self, property_data: Dict) -> float:
        """Score photos and media availability"""
        image_count = property_data.get("image_count", 0)
        images = property_data.get("images", [])

        if images:
            image_count = len(images)

        if image_count >= 10:
            return 1.0
        elif image_count >= 5:
            return 0.75
        elif image_count >= 1:
            return 0.5
        else:
            return 0.0

    def _score_market_data(self, property_data: Dict) -> float:
        """Score market data availability"""
        market_fields = [
            "housing_market", "rental_market",
            "climate_data", "location_scores",
            "price_history", "tax_history"
        ]

        present = sum(1 for field in market_fields if property_data.get(field))
        return present / len(market_fields)

    def _identify_missing_fields(self, property_data: Dict) -> Dict[str, List[str]]:
        """Identify missing fields by category"""
        missing = {
            "base": [],
            "enrichment": [],
            "comps": [],
            "media": [],
            "market": []
        }

        # Base fields
        base_fields = ["property_address", "city", "state", "zip", "upset_price", "auction_date"]
        for field in base_fields:
            if not property_data.get(field):
                missing["base"].append(field)

        # Enrichment fields
        enrichment_fields = ["zpid", "bedrooms", "bathrooms", "sqft", "zestimate"]
        for field in enrichment_fields:
            if not property_data.get(field):
                missing["enrichment"].append(field)

        # Comps
        if not property_data.get("comps"):
            missing["comps"].append("comparable_properties")

        # Media
        if not property_data.get("images") or property_data.get("image_count", 0) == 0:
            missing["media"].append("photos")

        # Market
        market_fields = ["housing_market", "rental_market", "climate_data"]
        for field in market_fields:
            if not property_data.get(field):
                missing["market"].append(field)

        return {k: v for k, v in missing.items() if v}  # Remove empty lists

    def _generate_recommendations(
        self,
        base_score: float,
        enrichment_score: float,
        comps_score: float,
        media_score: float,
        market_score: float,
        missing_fields: Dict[str, List[str]]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if base_score < 0.8:
            recommendations.append("Complete base property information for better analysis")

        if enrichment_score < 0.8:
            recommendations.append("Refresh Zillow enrichment data to get complete property details")

        if comps_score < 0.5:
            recommendations.append("Comparable sales data is limited - ARV estimates may be less accurate")

        if media_score < 0.5:
            recommendations.append("Property photos are not available - consider requesting visual inspection")

        if market_score < 0.5:
            recommendations.append("Market data is incomplete - local trends may be unavailable")

        if enrichment_score < MEDIUM_QUALITY_THRESHOLD:
            recommendations.append("Data quality is below threshold - verify key information before making decisions")

        return recommendations if recommendations else ["Data quality is good - no major issues detected"]

    def _has_comparable_data(self, property_data: Dict) -> bool:
        """Check if property has comparable sales data"""
        comps = property_data.get("comps")
        return bool(comps and len(comps) > 0)

    def _has_photos(self, property_data: Dict) -> bool:
        """Check if property has photos"""
        images = property_data.get("images")
        image_count = property_data.get("image_count", 0)
        return bool(images or image_count > 0)

    def _has_market_data(self, property_data: Dict) -> bool:
        """Check if property has market data"""
        return bool(
            property_data.get("housing_market") or
            property_data.get("rental_market") or
            property_data.get("climate_data")
        )

    async def _store_quality_score(self, property_id: int, quality_data: Dict) -> bool:
        """Store quality score in property enrichment data"""
        try:
            # Store quality score in foreclosure_listings
            self.supabase.table("foreclosure_listings").update({
                "data_quality_score": quality_data["overall_quality_score"],
                "data_quality_tier": quality_data["quality_tier"],
                "data_quality_checked_at": quality_data["calculated_at"]
            }).eq("id", property_id).execute()
            return True

        except Exception as e:
            logger.error(f"Error storing quality score: {e}")
            return False

    # =========================================================================
    # BATCH SCORING
    # =========================================================================

    async def score_properties_batch(
        self,
        property_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Calculate quality scores for multiple properties.

        Args:
            property_ids: List of property IDs

        Returns:
            Summary of batch scoring results
        """
        high_quality = 0
        medium_quality = 0
        low_quality = 0
        errors = 0

        results = []

        for prop_id in property_ids:
            quality = await self.calculate_quality_score(prop_id)
            if quality:
                results.append({
                    "property_id": prop_id,
                    "score": quality["overall_quality_score"],
                    "tier": quality["quality_tier"]
                })

                if quality["quality_tier"] == "high":
                    high_quality += 1
                elif quality["quality_tier"] == "medium":
                    medium_quality += 1
                else:
                    low_quality += 1
            else:
                errors += 1

        return {
            "total_processed": len(property_ids),
            "high_quality": high_quality,
            "medium_quality": medium_quality,
            "low_quality": low_quality,
            "errors": errors,
            "results": results
        }

    # =========================================================================
    # QUERY METHODS
    # =========================================================================

    async def get_quality_score(self, property_id: int) -> Optional[Dict[str, Any]]:
        """
        Get stored quality score for a property.

        Args:
            property_id: Property ID

        Returns:
            Stored quality data or None
        """
        try:
            result = self.supabase.table("foreclosure_listings").select(
                "data_quality_score", "data_quality_tier", "data_quality_checked_at"
            ).eq("id", property_id).execute()

            if result.data:
                data = result.data[0]
                if data.get("data_quality_score") is not None:
                    return {
                        "property_id": property_id,
                        "overall_quality_score": data["data_quality_score"],
                        "quality_tier": data.get("data_quality_tier"),
                        "calculated_at": data.get("data_quality_checked_at")
                    }
            return None

        except Exception as e:
            logger.error(f"Error getting quality score for property {property_id}: {e}")
            return None

    async def get_properties_by_quality(
        self,
        min_score: Optional[float] = None,
        quality_tier: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get properties filtered by quality score.

        Args:
            min_score: Minimum quality score
            quality_tier: Filter by quality tier (high, medium, low)
            limit: Maximum results

        Returns:
            List of properties matching quality criteria
        """
        try:
            query = self.supabase.table("foreclosure_listings").select("*")

            if min_score is not None:
                query = query.gte("data_quality_score", min_score)

            if quality_tier:
                query = query.eq("data_quality_tier", quality_tier)

            result = query.order("data_quality_score", desc=True).limit(limit).execute()

            return result.data

        except Exception as e:
            logger.error(f"Error getting properties by quality: {e}")
            return []

    async def refresh_quality_score(self, property_id: int) -> Optional[Dict[str, Any]]:
        """
        Force refresh of quality score for a property.

        Args:
            property_id: Property ID

        Returns:
            Updated quality score
        """
        return await self.calculate_quality_score(property_id)

    # =========================================================================
    # VALIDATION CHECKS
    # =========================================================================

    async def validate_property_for_display(self, property_id: int) -> Dict[str, Any]:
        """
        Validate if property has sufficient data for display.

        Returns validation checks suitable for UI warnings.
        """
        quality = await self.calculate_quality_score(property_id)
        if not quality:
            return {
                "is_safe_to_show": False,
                "reason": "Could not calculate quality score",
                "checks": []
            }

        checks = []
        score_breakdown = quality["score_breakdown"]

        # Base data check
        checks.append({
            "name": "Basic Property Information",
            "passed": score_breakdown["base_data_score"] >= 0.8,
            "score": score_breakdown["base_data_score"],
            "message": f"Core data {score_breakdown['base_data_score'] * 100:.0f}% complete"
        })

        # Enrichment check
        checks.append({
            "name": "Zillow Enrichment",
            "passed": score_breakdown["enrichment_score"] >= 0.5,
            "score": score_breakdown["enrichment_score"],
            "message": f"Enrichment {score_breakdown['enrichment_score'] * 100:.0f}% complete"
        })

        # Comps check
        checks.append({
            "name": "Comparable Sales",
            "passed": score_breakdown["comps_score"] >= 0.5,
            "score": score_breakdown["comps_score"],
            "message": f"{score_breakdown['comps_score'] * 100:.0f}% comps available"
        })

        return {
            "is_safe_to_show": quality["is_safe_to_show"],
            "overall_score": quality["overall_quality_score"],
            "quality_tier": quality["quality_tier"],
            "checks": checks,
            "warnings": quality["recommendations"] if not quality["is_safe_to_show"] else []
        }
