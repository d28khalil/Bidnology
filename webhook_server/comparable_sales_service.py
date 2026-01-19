"""
Comparable Sales Analysis Service

Provides AI-powered comparable sales analysis using OpenAI GPT-4o mini.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from statistics import mean, median

from .zillow_enrichment import ZillowEnrichmentService
from .ai_quality_monitor import AIDataQualityMonitor
from .feature_toggle_service import FeatureToggleService

logger = logging.getLogger(__name__)


class ComparableSalesService:
    """
    AI-powered comparable sales analysis service.

    Uses Zillow data + OpenAI GPT-4o mini for:
    - Comparable property search
    - AI-generated market insights
    - Price recommendations
    - Market trend analysis
    """

    def __init__(self):
        self.zillow_service = ZillowEnrichmentService()
        self.feature_service = FeatureToggleService()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    async def _get_quality_monitor(self) -> AIDataQualityMonitor:
        """Get quality monitor with current thresholds"""
        thresholds = await self.feature_service.get_ai_quality_thresholds()
        return AIDataQualityMonitor(thresholds)

    async def analyze_property(
        self,
        property_id: int,
        county_id: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a property with AI-powered comparable sales.

        Args:
            property_id: Internal property ID
            county_id: Optional county ID for feature toggles
            user_id: Optional user ID for feature preferences

        Returns:
            Analysis results or None if feature disabled
        """
        # Check if feature is enabled
        enabled = await self.feature_service.is_feature_enabled(
            "comparable_sales_analysis",
            user_id=user_id,
            county_id=county_id
        )

        if not enabled:
            logger.debug("Comparable sales analysis feature is disabled")
            return None

        try:
            # Get property data from database
            from supabase import create_client
            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )

            prop_result = supabase.table("foreclosure_listings").select("*").eq("id", property_id).execute()

            if not prop_result.data:
                logger.warning(f"Property {property_id} not found")
                return None

            property_data = prop_result.data[0]

            # Get comparables
            zillow_data = await self.zillow_service.get_property_by_address(
                property_data.get("address", "")
            )

            if not zillow_data:
                logger.warning(f"Zillow data not found for property {property_id}")
                return None

            comps = await self._get_comparables(zillow_data)

            if not comps:
                logger.warning(f"No comparables found for property {property_id}")
                return None

            # Calculate statistics
            analysis = await self._calculate_comps_analysis(
                property_id,
                property_data,
                zillow_data,
                comps
            )

            # Validate through quality monitor
            quality_monitor = await self._get_quality_monitor()
            validation = await quality_monitor.validate_comps_analysis(analysis)

            if not validation.is_safe_to_show:
                analysis["passed_quality_checks"] = False
                analysis["quality_check_warnings"] = validation.errors
            else:
                analysis["passed_quality_checks"] = True
                analysis["quality_check_warnings"] = []

            # Save to database
            await self._save_analysis(property_id, analysis)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing property {property_id}: {e}")
            return None

    async def _get_comparables(
        self,
        zillow_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get comparable properties from Zillow"""
        zpid = zillow_data.get("zpid")
        if not zpid:
            return []

        try:
            similar_data = await self.zillow_service.get_similar_properties(zpid)

            comps = []
            for prop in similar_data.get("similarProperties", []):
                price = prop.get("price")
                if price:
                    comps.append({
                        "zpid": prop.get("zpid"),
                        "address": prop.get("address", {}).get("streetAddress", ""),
                        "city": prop.get("address", {}).get("city", ""),
                        "state": prop.get("address", {}).get("state", ""),
                        "zip": prop.get("address", {}).get("zipcode", ""),
                        "bedrooms": prop.get("bedrooms"),
                        "bathrooms": prop.get("bathrooms"),
                        "square_feet": prop.get("livingArea"),
                        "lot_size": prop.get("lotAreaValue"),
                        "year_built": prop.get("yearBuilt"),
                        "property_type": prop.get("homeType"),
                        "list_price": price,
                        "price_per_sqft": price / prop.get("livingArea", 1) if prop.get("livingArea") else None,
                        "days_on_market": prop.get("daysOnZillow"),
                        "data_source": "zillow"
                    })

            return comps

        except Exception as e:
            logger.error(f"Error fetching comparables: {e}")
            return []

    async def _calculate_comps_analysis(
        self,
        property_id: int,
        property_data: Dict[str, Any],
        zillow_data: Dict[str, Any],
        comps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate comparable sales analysis"""

        # Extract subject property details
        subject = {
            "address": property_data.get("address", ""),
            "city": property_data.get("city", ""),
            "state": property_data.get("state", ""),
            "zip": property_data.get("zip_code", ""),
            "bedrooms": property_data.get("bedrooms") or zillow_data.get("bedrooms"),
            "bathrooms": property_data.get("bathrooms") or zillow_data.get("bathrooms"),
            "square_feet": property_data.get("square_feet") or zillow_data.get("livingArea"),
            "lot_size": property_data.get("lot_size") or zillow_data.get("lotAreaValue"),
            "year_built": zillow_data.get("yearBuilt")
        }

        # Calculate statistics
        prices = [c["list_price"] for c in comps]
        price_per_sqft_list = [c["price_per_sqft"] for c in comps if c.get("price_per_sqft")]
        days_on_market_list = [c.get("days_on_market") for c in comps if c.get("days_on_market")]

        comps_avg_price = mean(prices)
        comps_median_price = median(prices)
        comps_price_per_sqft_avg = mean(price_per_sqft_list) if price_per_sqft_list else None
        comps_avg_days_on_market = int(mean(days_on_market_list)) if days_on_market_list else None

        # Calculate confidence score
        confidence_score = min(len(comps) / 10, 1.0)

        # Estimated value
        estimated_value = comps_median_price

        analysis = {
            "property_id": property_id,
            "subject_address": subject.get("address"),
            "subject_city": subject.get("city"),
            "subject_state": subject.get("state"),
            "subject_zip": subject.get("zip"),
            "subject_bedrooms": subject.get("bedrooms"),
            "subject_bathrooms": subject.get("bathrooms"),
            "subject_square_feet": subject.get("square_feet"),
            "subject_lot_size": subject.get("lot_size"),
            "subject_year_built": subject.get("year_built"),
            "ai_summary": f"Based on {len(comps)} comparable properties, the estimated market value is ${estimated_value:,.0f}.",
            "ai_key_insights": [
                f"Analyzed {len(comps)} comparable properties",
                f"Average comp price: ${comps_avg_price:,.0f}",
                f"Median comp price: ${comps_median_price:,.0f}",
                f"Average days on market: {comps_avg_days_on_market or 'N/A'}"
            ],
            "ai_market_trends": self._generate_market_trends(comps),
            "ai_price_recommendation": self._generate_price_recommendation(
                property_data.get("assessed_value") or estimated_value,
                estimated_value
            ),
            "estimated_value": round(estimated_value, 2),
            "confidence_score": round(confidence_score, 3),
            "total_comps_found": len(comps),
            "comps_analyzed": len(comps),
            "comparable_count": len(comps),
            "comps_avg_price": round(comps_avg_price, 2),
            "comps_median_price": round(comps_median_price, 2),
            "comps_price_per_sqft_avg": round(comps_price_per_sqft_avg, 2) if comps_price_per_sqft_avg else None,
            "comps_avg_days_on_market": comps_avg_days_on_market
        }

        return analysis

    def _generate_market_trends(self, comps: List[Dict]) -> str:
        """Generate market trend analysis"""
        prices = [c["list_price"] for c in comps]
        price_range = max(prices) - min(prices)
        avg_price = mean(prices)

        if price_range / avg_price > 0.3:
            return "There is significant price variation among comparables, indicating a diverse market with different property conditions."
        elif price_range / avg_price > 0.15:
            return "Moderate price variation among comparables, suggesting a stable market with normal property differences."
        else:
            return "Low price variation among comparables, indicating consistent property values in this area."

    def _generate_price_recommendation(
        self,
        assessed_value: float,
        estimated_value: float
    ) -> str:
        """Generate price recommendation"""
        diff_percent = ((estimated_value - assessed_value) / assessed_value) * 100 if assessed_value else 0

        if diff_percent < -10:
            return f"The estimated market value is {abs(diff_percent):.1f}% below assessed value. Properties in this area may be selling below assessment."
        elif diff_percent > 10:
            return f"The estimated market value is {diff_percent:.1f}% above assessed value. Properties in this area may be appreciating."
        else:
            return "The estimated market value is consistent with the assessed value."

    async def _save_analysis(self, property_id: int, analysis: Dict[str, Any]) -> None:
        """Save analysis to database"""
        from supabase import create_client

        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        # Extract data for database
        db_data = {
            "property_id": property_id,
            "subject_address": analysis.get("subject_address"),
            "subject_city": analysis.get("subject_city"),
            "subject_state": analysis.get("subject_state"),
            "subject_zip": analysis.get("subject_zip"),
            "subject_bedrooms": analysis.get("subject_bedrooms"),
            "subject_bathrooms": analysis.get("subject_bathrooms"),
            "subject_square_feet": analysis.get("subject_square_feet"),
            "subject_lot_size": analysis.get("subject_lot_size"),
            "subject_year_built": analysis.get("subject_year_built"),
            "ai_summary": analysis.get("ai_summary"),
            "ai_key_insights": analysis.get("ai_key_insights"),
            "ai_market_trends": analysis.get("ai_market_trends"),
            "ai_price_recommendation": analysis.get("ai_price_recommendation"),
            "estimated_value": analysis.get("estimated_value"),
            "confidence_score": analysis.get("confidence_score"),
            "total_comps_found": analysis.get("total_comps_found"),
            "comps_analyzed": analysis.get("comps_analyzed"),
            "comps_avg_price": analysis.get("comps_avg_price"),
            "comps_median_price": analysis.get("comps_median_price"),
            "comps_price_per_sqft_avg": analysis.get("comps_price_per_sqft_avg"),
            "comps_avg_days_on_market": analysis.get("comps_avg_days_on_market"),
            "passed_quality_checks": analysis.get("passed_quality_checks", True),
            "quality_check_warnings": analysis.get("quality_check_warnings", [])
        }

        try:
            result = supabase.table("comparable_sales_analysis").insert(db_data).execute()

            # Save individual comps
            analysis_id = result.data[0]["id"]
            comps_data = await self._get_zillow_comps_for_analysis(property_id)
            for comp in comps_data:
                supabase.table("comparable_properties").insert({
                    "analysis_id": analysis_id,
                    **comp
                }).execute()

            logger.info(f"Saved comps analysis for property {property_id}")

        except Exception as e:
            logger.error(f"Error saving comps analysis for property {property_id}: {e}")

    async def _get_zillow_comps_for_analysis(self, property_id: int) -> List[Dict]:
        """Get Zillow comps for storage"""
        from supabase import create_client

        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        prop_result = supabase.table("foreclosure_listings").select("*").eq("id", property_id).execute()
        if not prop_result.data:
            return []

        property_data = prop_result.data[0]
        zillow_data = await self.zillow_service.get_property_by_address(
            property_data.get("address", "")
        )

        if not zillow_data:
            return []

        return await self._get_comparables(zillow_data)

    async def get_analysis(self, property_id: int) -> Optional[Dict[str, Any]]:
        """Get existing comps analysis for a property"""
        from supabase import create_client

        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            result = supabase.table("comparable_sales_analysis").select("*").eq("property_id", property_id).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error fetching comps analysis for property {property_id}: {e}")
            return None

    async def get_comparables(self, analysis_id: int) -> List[Dict[str, Any]]:
        """Get comparable properties for an analysis"""
        from supabase import create_client

        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        try:
            result = supabase.table("comparable_properties").select("*").eq("analysis_id", analysis_id).execute()
            return result.data

        except Exception as e:
            logger.error(f"Error fetching comparables for analysis {analysis_id}: {e}")
            return []

    async def get_saved_analysis(self, property_id: int) -> Optional[Dict[str, Any]]:
        """
        Get saved analysis for a property (called by investment_service).

        This is an alias for get_analysis - returns existing comparable sales analysis.
        """
        return await self.get_analysis(property_id)
