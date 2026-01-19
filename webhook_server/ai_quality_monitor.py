"""
AI Data Quality Monitor

Validates AI analysis results before showing them to users.
Prevents false positives from minimal/insufficient data.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from statistics import mean, stdev

logger = logging.getLogger(__name__)


@dataclass
class QualityCheck:
    """Single quality check result"""
    name: str
    passed: bool
    message: str
    threshold: Any = None
    actual_value: Any = None


@dataclass
class ValidationResult:
    """Result of quality validation"""
    is_safe_to_show: bool
    checks: List[QualityCheck] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_check(self, check: QualityCheck):
        """Add a check result"""
        self.checks.append(check)
        if not check.passed:
            self.errors.append(check.message)
        else:
            self.warnings.append(check.message)

    def has_critical_failure(self) -> bool:
        """Check if any critical checks failed"""
        return any(not c.passed for c in self.checks if "critical" in c.name.lower())


class AIDataQualityMonitor:
    """
    Validates AI analysis results before showing to users.

    This prevents false positives from:
    - Insufficient comparable properties
    - Low confidence scores
    - Outlier prices
    - Stale data
    """

    def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
        """
        Initialize quality monitor with thresholds.

        Args:
            thresholds: AI quality thresholds from FeatureToggleService
        """
        self.thresholds = thresholds or self._get_default_thresholds()

    def _get_default_thresholds(self) -> Dict[str, Any]:
        """Default thresholds if none provided"""
        return {
            "anomaly": {
                "min_comps": 3,
                "min_confidence": 0.700,
                "max_zscore": 2.50,
                "min_price_diff_percent": 15.00
            },
            "comps": {
                "min_samples": 3,
                "max_distance_miles": 1.0,
                "max_age_days": 365,
                "min_similarity_score": 0.600
            },
            "renovation": {
                "min_photos": 1,
                "confidence_threshold": 0.500
            }
        }

    # =========================================================================
    # MARKET ANOMALY VALIDATION
    # =========================================================================

    async def validate_market_anomaly(
        self,
        analysis_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate market anomaly analysis before flagging as "hot deal".

        Critical checks:
        - Minimum number of comparable properties
        - Minimum confidence score
        - Price difference is significant enough

        Args:
            analysis_data: Dictionary containing:
                - comparable_count: int
                - confidence_score: float (0-1)
                - price_difference_percent: float
                - z_score: float (optional)
                - comparable_prices: list of floats (optional)

        Returns:
            ValidationResult with is_safe_to_show flag
        """
        result = ValidationResult(is_safe_to_show=True)
        thresholds = self.thresholds.get("anomaly", {})

        # Check 1: Minimum comparable properties
        comp_count = analysis_data.get("comparable_count", 0)
        min_comps = thresholds.get("min_comps", 3)
        check1 = QualityCheck(
            name="Comparable Count (Critical)",
            passed=comp_count >= min_comps,
            message=f"Comparable properties: {comp_count} (minimum: {min_comps})",
            threshold=min_comps,
            actual_value=comp_count
        )
        result.add_check(check1)

        # Check 2: Minimum confidence score
        confidence = analysis_data.get("confidence_score", 0)
        min_confidence = thresholds.get("min_confidence", 0.700)
        check2 = QualityCheck(
            name="Confidence Score (Critical)",
            passed=confidence >= min_confidence,
            message=f"Confidence: {confidence:.3f} (minimum: {min_confidence:.3f})",
            threshold=min_confidence,
            actual_value=confidence
        )
        result.add_check(check2)

        # Check 3: Z-score within reasonable range
        z_score = analysis_data.get("z_score")
        if z_score is not None:
            max_zscore = thresholds.get("max_zscore", 2.50)
            check3 = QualityCheck(
                name="Z-Score",
                passed=abs(z_score) <= max_zscore,
                message=f"Z-score: {z_score:.2f} (maximum: {max_zscore:.2f})",
                threshold=max_zscore,
                actual_value=z_score
            )
            result.add_check(check3)

        # Check 4: Price difference is significant
        price_diff = analysis_data.get("price_difference_percent", 0)
        min_diff = thresholds.get("min_price_diff_percent", 15.00)
        check4 = QualityCheck(
            name="Price Significance",
            passed=abs(price_diff) >= min_diff,
            message=f"Price difference: {price_diff:.1f}% (minimum: {min_diff:.1f}%)",
            threshold=min_diff,
            actual_value=price_diff
        )
        result.add_check(check4)

        # Determine if safe to show (all critical checks must pass)
        result.is_safe_to_show = not result.has_critical_failure()

        return result

    # =========================================================================
    # COMPARABLE SALES VALIDATION
    # =========================================================================

    async def validate_comps_analysis(
        self,
        analysis_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate comparable sales analysis.

        Critical checks:
        - Minimum samples analyzed
        - Maximum distance for comparables
        - Maximum data age
        - Minimum similarity score

        Args:
            analysis_data: Dictionary containing:
                - comps_analyzed: int
                - comparables: list of comp dicts with distance, days_on_market
                - confidence_score: float

        Returns:
            ValidationResult with is_safe_to_show flag
        """
        result = ValidationResult(is_safe_to_show=True)
        thresholds = self.thresholds.get("comps", {})

        # Check 1: Minimum samples
        comps_count = analysis_data.get("comps_analyzed", 0)
        min_samples = thresholds.get("min_samples", 3)
        check1 = QualityCheck(
            name="Sample Count (Critical)",
            passed=comps_count >= min_samples,
            message=f"Comparables analyzed: {comps_count} (minimum: {min_samples})",
            threshold=min_samples,
            actual_value=comps_count
        )
        result.add_check(check1)

        # Check 2: Maximum distance (if comparables provided)
        comparables = analysis_data.get("comparables", [])
        if comparables:
            max_distance = thresholds.get("max_distance_miles", 1.0)
            distances = [c.get("distance_miles", float("inf")) for c in comparables]
            avg_distance = mean(distances) if distances else 0
            max_actual = max(distances) if distances else 0

            check2 = QualityCheck(
                name="Distance Check",
                passed=max_actual <= max_distance,
                message=f"Max distance: {max_actual:.2f} miles (maximum: {max_distance:.2f})",
                threshold=max_distance,
                actual_value=max_actual
            )
            result.add_check(check2)

            # Check 3: Maximum data age
            max_age = thresholds.get("max_age_days", 365)
            ages = [c.get("days_on_market", 0) for c in comparables if c.get("days_on_market")]
            if ages:
                max_actual_age = max(ages)
                check3 = QualityCheck(
                    name="Data Recency",
                    passed=max_actual_age <= max_age,
                    message=f"Oldest comp: {max_actual_age} days (maximum: {max_age})",
                    threshold=max_age,
                    actual_value=max_actual_age
                )
                result.add_check(check3)

        # Check 4: Minimum similarity score (if provided)
        similarity = analysis_data.get("similarity_score")
        if similarity is not None:
            min_similarity = thresholds.get("min_similarity_score", 0.600)
            check4 = QualityCheck(
                name="Similarity Score",
                passed=similarity >= min_similarity,
                message=f"Similarity: {similarity:.3f} (minimum: {min_similarity:.3f})",
                threshold=min_similarity,
                actual_value=similarity
            )
            result.add_check(check4)

        result.is_safe_to_show = not result.has_critical_failure()

        return result

    # =========================================================================
    # RENOVATION ESTIMATE VALIDATION
    # =========================================================================

    async def validate_renovation_estimate(
        self,
        analysis_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate renovation cost estimate.

        Critical checks:
        - Minimum number of photos analyzed
        - Minimum confidence score

        Args:
            analysis_data: Dictionary containing:
                - photos_analyzed: int
                - confidence_score: float
                - total_estimated_cost: float

        Returns:
            ValidationResult with is_safe_to_show flag
        """
        result = ValidationResult(is_safe_to_show=True)
        thresholds = self.thresholds.get("renovation", {})

        # Check 1: Minimum photos
        photo_count = analysis_data.get("photos_analyzed", 0)
        min_photos = thresholds.get("min_photos", 1)
        check1 = QualityCheck(
            name="Photo Count (Critical)",
            passed=photo_count >= min_photos,
            message=f"Photos analyzed: {photo_count} (minimum: {min_photos})",
            threshold=min_photos,
            actual_value=photo_count
        )
        result.add_check(check1)

        # Check 2: Minimum confidence
        confidence = analysis_data.get("confidence_score", 0)
        min_confidence = thresholds.get("confidence_threshold", 0.500)
        check2 = QualityCheck(
            name="Confidence Score (Critical)",
            passed=confidence >= min_confidence,
            message=f"Confidence: {confidence:.3f} (minimum: {min_confidence:.3f})",
            threshold=min_confidence,
            actual_value=confidence
        )
        result.add_check(check2)

        # Check 3: Reasonable cost range (sanity check)
        total_cost = analysis_data.get("total_estimated_cost")
        if total_cost is not None:
            # Cost should be between $1,000 and $1,000,000
            reasonable = 1000 <= total_cost <= 1000000
            check3 = QualityCheck(
                name="Cost Sanity Check",
                passed=reasonable,
                message=f"Estimated cost: ${total_cost:,.2f}",
                actual_value=total_cost
            )
            result.add_check(check3)

        result.is_safe_to_show = not result.has_critical_failure()

        return result

    # =========================================================================
    # GENERAL VALIDATION HELPERS
    # =========================================================================

    def calculate_price_statistics(
        self,
        prices: List[float]
    ) -> Dict[str, float]:
        """
        Calculate price statistics for validation.

        Returns:
            Dict with mean, median, std_dev, min, max
        """
        if not prices:
            return {}

        sorted_prices = sorted(prices)
        n = len(prices)

        return {
            "mean": mean(prices),
            "median": sorted_prices[n // 2] if n % 2 == 1 else (sorted_prices[n // 2 - 1] + sorted_prices[n // 2]) / 2,
            "std_dev": stdev(prices) if n > 1 else 0,
            "min": min(prices),
            "max": max(prices),
            "count": n
        }

    def is_price_outlier(
        self,
        price: float,
        comparables: List[float],
        max_zscore: float = 2.5
    ) -> bool:
        """
        Check if a price is an outlier compared to comparables.

        Args:
            price: The price to check
            comparables: List of comparable prices
            max_zscore: Maximum allowed z-score

        Returns:
            True if price is an outlier
        """
        if len(comparables) < 3:
            return True  # Not enough data to determine

        stats = self.calculate_price_statistics(comparables)
        std_dev = stats.get("std_dev", 0)
        mean_price = stats.get("mean", price)

        if std_dev == 0:
            return False  # All prices are the same

        z_score = abs(price - mean_price) / std_dev
        return z_score > max_zscore

    def format_validation_result(self, result: ValidationResult) -> Dict[str, Any]:
        """Format validation result for API response"""
        return {
            "is_safe_to_show": result.is_safe_to_show,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "threshold": c.threshold,
                    "actual_value": c.actual_value
                }
                for c in result.checks
            ],
            "warnings": result.warnings,
            "errors": result.errors
        }
