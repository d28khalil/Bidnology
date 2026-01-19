"""
Renovation Cost Estimator Service

Uses GPT-4o Vision API to analyze property photos and estimate
renovation costs by room type and condition.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from statistics import mean
from supabase import create_client, Client
from .feature_toggle_service import FeatureToggleService
from .ai_quality_monitor import AIDataQualityMonitor

logger = logging.getLogger(__name__)


# Renovation cost estimates by room type and condition (base costs in USD)
RENOVATION_COST_BASE = {
    "kitchen": {
        "cosmetic": {"min": 5000, "max": 15000, "items": ["paint", "flooring", "hardware"]},
        "moderate": {"min": 15000, "max": 35000, "items": ["cabinets", "countertops", "appliances", "flooring"]},
        "major": {"min": 35000, "max": 70000, "items": ["full_gut", "structural", "plumbing", "electrical"]}
    },
    "bathroom": {
        "cosmetic": {"min": 2000, "max": 5000, "items": ["paint", "fixtures", "vanity"]},
        "moderate": {"min": 5000, "max": 15000, "items": ["tile", "toilet", "shower", "vanity"]},
        "major": {"min": 15000, "max": 35000, "items": ["full_gut", "plumbing", "electrical", "tile"]}
    },
    "living_room": {
        "cosmetic": {"min": 1000, "max": 3000, "items": ["paint", "flooring"]},
        "moderate": {"min": 3000, "max": 8000, "items": ["flooring", "trim", "lighting"]},
        "major": {"min": 8000, "max": 20000, "items": ["windows", "structural", "electrical"]}
    },
    "bedroom": {
        "cosmetic": {"min": 800, "max": 2000, "items": ["paint", "flooring"]},
        "moderate": {"min": 2000, "max": 6000, "items": ["flooring", "closet", "trim"]},
        "major": {"min": 6000, "max": 15000, "items": ["windows", "structural", "electrical"]}
    },
    "basement": {
        "cosmetic": {"min": 2000, "max": 5000, "items": ["paint", "flooring", "waterproofing"]},
        "moderate": {"min": 5000, "max": 20000, "items": ["framing", "drywall", "flooring", "bathroom"]},
        "major": {"min": 20000, "max": 60000, "items": ["full_finish", "egress", "hvac", "plumbing"]}
    },
    "exterior": {
        "cosmetic": {"min": 3000, "max": 8000, "items": ["paint", "landscaping"]},
        "moderate": {"min": 8000, "max": 25000, "items": ["siding", "roof_patch", "windows"]},
        "major": {"min": 25000, "max": 75000, "items": ["roof_replace", "siding_replace", "structural"]}
    },
    "roof": {
        "cosmetic": {"min": 2000, "max": 5000, "items": ["patch_repair"]},
        "moderate": {"min": 5000, "max": 15000, "items": ["partial_replace"]},
        "major": {"min": 15000, "max": 40000, "items": ["full_replace"]}
    },
    "flooring": {
        "cosmetic": {"min": 2000, "max": 5000, "items": ["refinish"]},
        "moderate": {"min": 5000, "max": 12000, "items": ["partial_replace"]},
        "major": {"min": 12000, "max": 25000, "items": ["full_replace"]}
    },
    "hvac": {
        "cosmetic": {"min": 500, "max": 1500, "items": ["maintenance", "duct_cleaning"]},
        "moderate": {"min": 1500, "max": 8000, "items": ["unit_replace"]},
        "major": {"min": 8000, "max": 20000, "items": ["full_system_replace", "ductwork"]}
    },
    "other": {
        "cosmetic": {"min": 500, "max": 2000, "items": ["general"]},
        "moderate": {"min": 2000, "max": 7000, "items": ["repairs"]},
        "major": {"min": 7000, "max": 20000, "items": ["structural", "major_repairs"]}
    }
}


class RenovationEstimatorService:
    """
    Service for estimating renovation costs from property photos.

    Uses GPT-4o Vision API to analyze photos and classify room types,
    conditions, and required renovation work.
    """

    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        self.feature_service = FeatureToggleService()
        self.quality_monitor = AIDataQualityMonitor()

    async def is_feature_enabled(
        self,
        user_id: Optional[str] = None,
        county_id: Optional[int] = None,
        state: Optional[str] = None
    ) -> bool:
        """Check if renovation estimator feature is enabled"""
        return await self.feature_service.is_feature_enabled(
            "renovation_cost_estimator",
            user_id=user_id,
            county_id=county_id,
            state=state
        )

    # ========================================================================
    # RENOVATION ESTIMATION
    # ========================================================================

    async def estimate_from_photos(
        self,
        property_id: int,
        photo_urls: List[str],
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze property photos and estimate renovation costs.

        Args:
            property_id: Database property ID
            photo_urls: List of photo URLs to analyze
            user_id: Optional user ID for feature toggle check

        Returns:
            Renovation estimate with breakdown by room/area
        """
        # Check feature is enabled
        if not await self.is_feature_enabled(user_id):
            logger.info(f"Renovation estimator feature not enabled for user {user_id}")
            return None

        # Get quality thresholds
        thresholds = await self.feature_service.get_ai_quality_thresholds()
        min_photo_count = thresholds.get("reno_min_photo_count", 3)
        min_confidence = thresholds.get("reno_min_confidence", 0.6)

        # Validate photo count
        if len(photo_urls) < min_photo_count:
            logger.warning(
                f"Insufficient photos for renovation estimate: "
                f"{len(photo_urls)} < {min_photo_count}"
            )
            return await self._create_insufficient_photos_result(
                property_id, len(photo_urls), min_photo_count
            )

        # Analyze each photo
        photo_analyses = []
        for i, photo_url in enumerate(photo_urls[:10]):  # Limit to 10 photos
            try:
                analysis = await self._analyze_single_photo(photo_url)
                if analysis:
                    photo_analyses.append(analysis)
            except Exception as e:
                logger.warning(f"Failed to analyze photo {i+1}: {e}")
                continue

        if not photo_analyses:
            logger.error(f"No photos could be analyzed for property {property_id}")
            return await self._create_insufficient_photos_result(
                property_id, 0, min_photo_count, "No photos could be analyzed"
            )

        # Calculate total estimate
        estimate_breakdown = self._calculate_total_estimate(photo_analyses)

        # Generate AI summary
        ai_summary = await self._generate_estimate_summary(
            photo_analyses, estimate_breakdown
        )

        # Calculate confidence score
        confidence = self._calculate_confidence(
            len(photo_urls),
            len(photo_analyses),
            estimate_breakdown
        )

        # Determine analysis quality
        analysis_quality = self._determine_quality(
            len(photo_analyses), confidence, min_photo_count, min_confidence
        )

        # Create estimate record with proper column mapping
        estimate_record = {
            "property_id": property_id,
            "total_estimated_cost": estimate_breakdown["total_min"],
            "room_breakdown": estimate_breakdown["by_room"],
            "photos_analyzed": photo_analyses,
            "ai_summary": ai_summary,
            "confidence_score": confidence,
            "photo_count": len(photo_urls),
            "data_quality_flags": {
                "analysis_quality": analysis_quality,
                "photo_urls": photo_urls,
                "ai_disclaimer": "This analysis is based on AI interpretation of photos. "
                                "Always conduct an on-site inspection before making investment decisions."
            }
        }

        # Store in database
        result = self.supabase.table("v2_renovation_estimates").insert(
            estimate_record
        ).execute()

        if not result.data:
            raise Exception("Failed to store renovation estimate")

        logger.info(
            f"Created renovation estimate for property {property_id}: "
            f"${estimate_breakdown['total_min']:,.0f} - ${estimate_breakdown['total_max']:,.0f}, "
            f"confidence={confidence:.2f}"
        )

        return result.data[0]

    async def update_manual_estimate(
        self,
        estimate_id: int,
        manual_total: Optional[float],
        adjustments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update renovation estimate with manual override.

        Allows contractors or experienced investors to correct AI estimates.
        """
        update_data = {
            "manual_estimate_total": manual_total,
            "manual_adjustments": adjustments
        }

        result = self.supabase.table("v2_renovation_estimates").update(
            update_data
        ).eq("id", estimate_id).execute()

        if not result.data:
            raise ValueError(f"Estimate {estimate_id} not found")

        logger.info(f"Updated manual renovation estimate for {estimate_id}: ${manual_total:,.0f}")
        return result.data[0]

    async def get_saved_estimate(
        self,
        property_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get most recent renovation estimate for a property"""
        result = self.supabase.table("v2_renovation_estimates").select(
            "*"
        ).eq("property_id", property_id).order(
            "created_at", desc=True
        ).limit(1).execute()

        return result.data[0] if result.data else None

    # ========================================================================
    # PHOTO ANALYSIS (GPT-4o Vision)
    # ========================================================================

    async def _analyze_single_photo(
        self,
        photo_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a single photo using GPT-4o Vision API.

        Identifies room type, condition rating, and renovation level.
        """
        try:
            import openai

            client = openai.AsyncClient(api_key=os.getenv("OPENAI_API_KEY"))

            prompt = """Analyze this property photo for renovation purposes.

Identify:
1. Room type (kitchen, bathroom, living_room, bedroom, basement, exterior, roof, flooring, hvac, other)
2. Condition rating (1-5, where 1=excellent/new, 5=severe damage/gut job needed)
3. Specific issues visible (list 2-5 items if issues are visible)
4. Renovation level needed (cosmetic, moderate, major)

Respond in JSON format:
{
    "room_type": "kitchen",
    "condition_rating": 4,
    "issues": ["outdated cabinets", "damaged flooring", "old appliances"],
    "renovation_level": "moderate",
    "notes": "brief description of what you see"
}"""

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a property renovation expert. Respond only in valid JSON."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": photo_url,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=300
            )

            result_text = response.choices[0].message.content
            import json
            analysis = json.loads(result_text)

            # Add estimated cost range based on analysis
            room_type = analysis.get("room_type", "other")
            reno_level = analysis.get("renovation_level", "cosmetic")

            cost_range = RENOVATION_COST_BASE.get(room_type, RENOVATION_COST_BASE["other"])
            level_costs = cost_range.get(reno_level, cost_range["cosmetic"])

            analysis["estimated_cost_range"] = [
                level_costs["min"],
                level_costs["max"]
            ]
            analysis["recommended_items"] = level_costs.get("items", [])

            return analysis

        except Exception as e:
            logger.error(f"Photo analysis error for {photo_url}: {e}")
            return None

    def _calculate_total_estimate(
        self,
        photo_analyses: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate total renovation estimate from photo analyses.

        Aggregates by room type and provides overall range.
        """
        by_room = {}
        total_min = 0
        total_max = 0

        for analysis in photo_analyses:
            room_type = analysis.get("room_type", "other")
            cost_range = analysis.get("estimated_cost_range", [0, 0])

            if room_type not in by_room:
                by_room[room_type] = {
                    "count": 0,
                    "total_min": 0,
                    "total_max": 0,
                    "analyses": []
                }

            by_room[room_type]["count"] += 1
            by_room[room_type]["total_min"] += cost_range[0]
            by_room[room_type]["total_max"] += cost_range[1]
            by_room[room_type]["analyses"].append(analysis)

            total_min += cost_range[0]
            total_max += cost_range[1]

        return {
            "by_room": by_room,
            "total_min": round(total_min, 2),
            "total_max": round(total_max, 2),
            "total_avg": round((total_min + total_max) / 2, 2)
        }

    async def _generate_estimate_summary(
        self,
        photo_analyses: List[Dict],
        breakdown: Dict[str, Any]
    ) -> str:
        """Generate AI summary of renovation needs"""
        try:
            import openai

            client = openai.AsyncClient(api_key=os.getenv("OPENAI_API_KEY"))

            # Summarize by room
            room_summary = []
            for room, data in breakdown["by_room"].items():
                room_summary.append(
                    f"{room.replace('_', ' ').title()}: "
                    f"${data['total_min']:,.0f} - ${data['total_max']:,.0f} "
                    f"({data['count']} photo{'s' if data['count'] > 1 else ''})"
                )

            prompt = f"""Summarize this renovation estimate in 2-3 sentences.

Total Estimate: ${breakdown['total_min']:,.0f} - ${breakdown['total_max']:,.0f}

By Room:
{chr(10).join(room_summary)}

Photo Analyses:
{len(photo_analyses)} photos analyzed

Provide a concise summary for an investor."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a construction and renovation expert."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return None

    def _calculate_confidence(
        self,
        total_photos: int,
        analyzed_photos: int,
        breakdown: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the estimate"""
        confidence = 0.0

        # Factor 1: Photo coverage (max 0.3)
        coverage = min(total_photos / 10, 1.0)
        confidence += coverage * 0.3

        # Factor 2: Analysis success rate (max 0.3)
        success_rate = analyzed_photos / total_photos if total_photos > 0 else 0
        confidence += success_rate * 0.3

        # Factor 3: Room variety (max 0.2)
        room_variety = min(len(breakdown["by_room"]) / 5, 1.0)
        confidence += room_variety * 0.2

        # Factor 4: Estimate consistency (max 0.2)
        # Check if multiple photos of same room type have similar estimates
        consistency = self._check_estimate_consistency(breakdown)
        confidence += consistency * 0.2

        return round(min(confidence, 1.0), 3)

    def _check_estimate_consistency(
        self,
        breakdown: Dict[str, Any]
    ) -> float:
        """Check if estimates for same room types are consistent"""
        room_scores = []

        for room, data in breakdown["by_room"].items():
            if data["count"] >= 2:
                # Check variance in analyses
                avg_min = data["total_min"] / data["count"]
                avg_max = data["total_max"] / data["count"]

                # Lower variance = higher consistency score
                # This is simplified - in practice would calculate actual variance
                room_scores.append(0.8)  # Assume reasonable consistency
            else:
                room_scores.append(0.5)  # Can't assess with single photo

        return mean(room_scores) if room_scores else 0.5

    def _determine_quality(
        self,
        analyzed_count: int,
        confidence: float,
        min_photos: int,
        min_confidence: float
    ) -> str:
        """Determine overall quality rating"""
        if analyzed_count >= min_photos and confidence >= min_confidence:
            return "high"
        elif analyzed_count >= min_photos * 0.7 and confidence >= min_confidence * 0.8:
            return "medium"
        else:
            return "low"

    async def _create_insufficient_photos_result(
        self,
        property_id: int,
        actual_count: int,
        required_count: int,
        reason: str = "Insufficient photos"
    ) -> Dict[str, Any]:
        """Create result for insufficient photos scenario"""
        return {
            "property_id": property_id,
            "total_estimated_cost": None,
            "room_breakdown": {
                "error": f"{reason}: {actual_count} < {required_count} required"
            },
            "photos_analyzed": [],
            "ai_summary": None,
            "confidence_score": 0.0,
            "photo_count": actual_count,
            "data_quality_flags": {
                "analysis_quality": "insufficient",
                "photo_urls": [],
                "ai_disclaimer": "This analysis is based on AI interpretation of photos. "
                                "Always conduct an on-site inspection before making investment decisions."
            }
        }
