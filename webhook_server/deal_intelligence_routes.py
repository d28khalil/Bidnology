"""
Deal Intelligence API Routes

Provides REST API endpoints for all deal intelligence features:
- Feature toggle management
- Market anomaly detection
- Comparable sales analysis
- Saved properties with Kanban board
- And more...
"""

import logging
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, HTTPException, Query, Header, Depends
from pydantic import BaseModel, Field

from .feature_toggle_service import FeatureToggleService
from .market_anomaly_service import MarketAnomalyService
from .comparable_sales_service import ComparableSalesService
from .saved_properties_service import SavedPropertiesService
from .renovation_service import RenovationEstimatorService
from .investment_service import InvestmentStrategyService
from .watchlist_service import WatchlistService
# V2 ONLY: from .portfolio_service import PortfolioService
from .collaboration_service import CollaborationService
from .notes_service import NotesService
from .push_notification_service import PushNotificationService
from .deal_criteria_service import DealCriteriaService
from .data_quality_service import DataQualityService
from .zillow_enrichment import ZillowEnrichmentService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/deal-intelligence",
    tags=["Deal Intelligence (V1)"]  # Default to V1, V2 endpoints override with tags=["Deal Intelligence (V2)"]
)

# =============================================================================
# Services
# =============================================================================

feature_service = FeatureToggleService()
anomaly_service = MarketAnomalyService()
comps_service = ComparableSalesService()
saved_service = SavedPropertiesService()
renovation_service = RenovationEstimatorService()
investment_service = InvestmentStrategyService()
watchlist_service = WatchlistService()
# V2 ONLY: portfolio_service = PortfolioService()
collaboration_service = CollaborationService()
notes_service = NotesService()
push_service = PushNotificationService()
deal_criteria_service = DealCriteriaService()
data_quality_service = DataQualityService()


# =============================================================================
# Pydantic Models
# =============================================================================


# --- Feature Toggle Models ---
class AdminFeatureSettingsUpdate(BaseModel):
    feature_market_anomaly_detection: Optional[bool] = None
    feature_comparable_sales_analysis: Optional[bool] = None
    feature_renovation_cost_estimator: Optional[bool] = None
    feature_investment_strategies: Optional[bool] = None
    feature_watchlist_alerts: Optional[bool] = None
    feature_portfolio_tracking: Optional[bool] = None
    feature_team_collaboration: Optional[bool] = None
    feature_mobile_notifications: Optional[bool] = None
    feature_notes_checklist: Optional[bool] = None
    feature_export_csv: Optional[bool] = None
    feature_save_property: Optional[bool] = None
    feature_kanban_board: Optional[bool] = None

    feature_lock_market_anomaly_detection: Optional[bool] = None
    feature_lock_comparable_sales_analysis: Optional[bool] = None
    feature_lock_renovation_cost_estimator: Optional[bool] = None
    feature_lock_investment_strategies: Optional[bool] = None
    feature_lock_watchlist_alerts: Optional[bool] = None
    feature_lock_portfolio_tracking: Optional[bool] = None
    feature_lock_team_collaboration: Optional[bool] = None
    feature_lock_mobile_notifications: Optional[bool] = None
    feature_lock_notes_checklist: Optional[bool] = None
    feature_lock_export_csv: Optional[bool] = None
    feature_lock_save_property: Optional[bool] = None
    feature_lock_kanban_board: Optional[bool] = None

    # AI Quality Thresholds
    anomaly_min_comps: Optional[int] = None
    anomaly_min_confidence: Optional[float] = None
    anomaly_max_zscore: Optional[float] = None
    anomaly_min_price_diff_percent: Optional[float] = None
    comps_analysis_min_samples: Optional[int] = None
    comps_analysis_max_distance_miles: Optional[float] = None
    comps_analysis_max_age_days: Optional[int] = None
    comps_analysis_min_similarity_score: Optional[float] = None


class CountyFeatureSettingsCreate(BaseModel):
    county_id: int
    override_market_anomaly_detection: Optional[bool] = None
    override_comparable_sales_analysis: Optional[bool] = None
    override_renovation_cost_estimator: Optional[bool] = None
    override_investment_strategies: Optional[bool] = None
    override_watchlist_alerts: Optional[bool] = None
    override_portfolio_tracking: Optional[bool] = None
    override_team_collaboration: Optional[bool] = None
    override_mobile_notifications: Optional[bool] = None
    override_notes_checklist: Optional[bool] = None
    override_export_csv: Optional[bool] = None
    override_save_property: Optional[bool] = None
    override_kanban_board: Optional[bool] = None


class CountyFeatureSettingsUpdate(BaseModel):
    """For PUT /settings/county/{id} - county_id comes from URL path"""
    override_market_anomaly_detection: Optional[bool] = None
    override_comparable_sales_analysis: Optional[bool] = None
    override_renovation_cost_estimator: Optional[bool] = None
    override_investment_strategies: Optional[bool] = None
    override_watchlist_alerts: Optional[bool] = None
    override_portfolio_tracking: Optional[bool] = None
    override_team_collaboration: Optional[bool] = None
    override_mobile_notifications: Optional[bool] = None
    override_notes_checklist: Optional[bool] = None
    override_export_csv: Optional[bool] = None
    override_save_property: Optional[bool] = None
    override_kanban_board: Optional[bool] = None


class UserPreferencesCreate(BaseModel):
    """For POST /settings/user - user_id from header, county_id optional"""
    county_id: Optional[int] = None
    pref_market_anomaly_detection: Optional[bool] = None
    pref_comparable_sales_analysis: Optional[bool] = None
    pref_renovation_cost_estimator: Optional[bool] = None
    pref_investment_strategies: Optional[bool] = None
    pref_watchlist_alerts: Optional[bool] = None
    pref_portfolio_tracking: Optional[bool] = None
    pref_team_collaboration: Optional[bool] = None
    pref_mobile_notifications: Optional[bool] = None
    pref_notes_checklist: Optional[bool] = None
    pref_export_csv: Optional[bool] = None
    pref_save_property: Optional[bool] = None
    pref_kanban_board: Optional[bool] = None


class UserPreferencesUpdate(BaseModel):
    """For PUT /settings/user/{id} - user_id comes from URL path"""
    county_id: Optional[int] = None
    pref_market_anomaly_detection: Optional[bool] = None
    pref_comparable_sales_analysis: Optional[bool] = None
    pref_renovation_cost_estimator: Optional[bool] = None
    pref_investment_strategies: Optional[bool] = None
    pref_watchlist_alerts: Optional[bool] = None
    pref_portfolio_tracking: Optional[bool] = None
    pref_team_collaboration: Optional[bool] = None
    pref_mobile_notifications: Optional[bool] = None
    pref_notes_checklist: Optional[bool] = None
    pref_export_csv: Optional[bool] = None
    pref_save_property: Optional[bool] = None
    pref_kanban_board: Optional[bool] = None


# --- Market Anomaly Models ---
class AnomalyAnalysisRequest(BaseModel):
    property_id: int
    address: str
    list_price: float
    county_id: Optional[int] = None


class AnomalyVerificationUpdate(BaseModel):
    is_verified: Optional[bool] = None
    feedback: Optional[str] = None


# --- Comparable Sales Models ---
class CompsAnalysisRequest(BaseModel):
    property_id: int
    county_id: Optional[int] = None


# --- Saved Properties Models ---
class SavePropertyRequest(BaseModel):
    property_id: int
    notes: Optional[str] = None
    kanban_stage: Optional[str] = "researching"


class KanbanStageUpdate(BaseModel):
    saved_id: int
    new_stage: str


class NotesUpdate(BaseModel):
    notes: str


class BulkStageUpdate(BaseModel):
    updates: List[Dict[str, Any]]


# --- Renovation Estimator Models ---
class RenovationEstimateRequest(BaseModel):
    property_id: int
    photo_urls: List[str]


class RenovationManualUpdate(BaseModel):
    manual_total: Optional[float] = None
    adjustments: Optional[Dict[str, Any]] = None


# --- Investment Strategy Models ---
class InvestmentStrategyCreate(BaseModel):
    """For POST /strategies - user_id from X-User-ID header"""
    strategy_name: str
    strategy_type: str
    min_fix_and_flip_profit: Optional[float] = None  # Database column
    max_purchase_price: Optional[float] = None
    min_arv_spread: Optional[float] = None
    max_repair_cost: Optional[float] = None  # Database column (not max_rehab_cost)
    max_holding_months: Optional[int] = None
    min_cash_flow: Optional[float] = None
    custom_criteria: Optional[Dict[str, Any]] = None


class InvestmentStrategyUpdate(BaseModel):
    county_id: Optional[int] = None
    strategy_name: Optional[str] = None
    min_fix_and_flip_profit: Optional[float] = None  # Database column
    max_purchase_price: Optional[float] = None
    min_arv_spread: Optional[float] = None
    max_repair_cost: Optional[float] = None  # Database column (not max_rehab_cost)
    max_holding_months: Optional[int] = None
    min_cash_flow: Optional[float] = None
    custom_criteria: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


# --- Watchlist Models ---
class WatchlistAddRequest(BaseModel):
    property_id: int
    alert_on_price_change: bool = True
    alert_on_status_change: bool = True
    alert_on_new_comps: bool = False
    alert_on_auction_near: bool = False
    auction_alert_days: int = 7
    watch_notes: Optional[str] = None
    priority: str = "normal"


class WatchlistUpdateRequest(BaseModel):
    alert_on_price_change: Optional[bool] = None
    alert_on_status_change: Optional[bool] = None
    alert_on_new_comps: Optional[bool] = None
    alert_on_auction_near: Optional[bool] = None
    auction_alert_days: Optional[int] = None
    watch_notes: Optional[str] = None
    priority: Optional[str] = None


# --- Portfolio Models ---
# V2 ONLY: Portfolio tracking is not part of V1 MVP
# class PortfolioAddRequest(BaseModel):
#     property_id: int
#     acquisition_date: Optional[str] = None
#     purchase_price: Optional[float] = None
#     rehab_cost: Optional[float] = None
#     strategy_used: Optional[str] = None
#     arv_target: Optional[float] = None
#
#
# class PortfolioUpdateRequest(BaseModel):
#     current_value: Optional[float] = None
#     actual_arv: Optional[float] = None
#     portfolio_status: Optional[str] = None
#     sale_date: Optional[str] = None
#     sale_price: Optional[float] = None


# --- Collaboration Models ---
class SharePropertyRequest(BaseModel):
    property_id: int
    shared_with_user_id: str
    share_type: str = "view"
    share_message: Optional[str] = None


class CommentAddRequest(BaseModel):
    property_id: int
    comment_text: str
    parent_comment_id: Optional[int] = None


class CommentUpdateRequest(BaseModel):
    comment_text: str


# --- Notes & Checklist Models ---
class NoteAddRequest(BaseModel):
    property_id: int
    content: str  # Changed from note_text for API consistency
    note_type: str = "general"


class NoteUpdateRequest(BaseModel):
    content: str  # Changed from note_text for API consistency


class ChecklistUpdateRequest(BaseModel):
    checklist_items: Dict[str, bool]


# --- Push Notification Models ---
class PushTokenRegisterRequest(BaseModel):
    device_token: str
    platform: str
    device_info: Optional[Dict[str, Any]] = None


class NotificationCreateRequest(BaseModel):
    user_id: str
    notification_type: str
    title: str
    body: str
    property_id: Optional[int] = None
    deep_link: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None
    priority: str = "normal"


class NotificationPreferencesUpdate(BaseModel):
    enable_hot_deals: Optional[bool] = None
    enable_auction_updates: Optional[bool] = None
    enable_price_drops: Optional[bool] = None
    enable_status_changes: Optional[bool] = None
    enable_watchlist_alerts: Optional[bool] = None
    enable_comps_available: Optional[bool] = None
    enable_marketing_updates: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    quiet_timezone: Optional[str] = None


# --- CSV Export Models ---
class CsvExportRequest(BaseModel):
    county_id: Optional[int] = None
    property_ids: Optional[List[int]] = None
    columns: Optional[List[str]] = None


# =============================================================================
# Helper Functions
# =============================================================================

async def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user ID from header"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-ID header required")
    return x_user_id


# =============================================================================
# FEATURE SETTINGS ROUTES
# =============================================================================

@router.get(
    "/settings/admin",
    summary="Get Admin Feature Settings",
    description="""
    Retrieve the global admin feature toggle settings and AI quality thresholds.

    ## Feature Toggle System

    This API uses a **three-tier feature toggle system**:
    1. **Admin Level** (this endpoint) - Global defaults for all users/counties
    2. **County Level** - Override settings per county
    3. **User Level** - Individual user preferences

    ## Features

    | Feature | Description |
    |---------|-------------|
    | `feature_market_anomaly_detection` | Price anomaly analysis using Zillow comps |
    | `feature_comparable_sales_analysis` | AI-powered comparable sales analysis |
    | `feature_renovation_cost_estimator` | Photo-based renovation cost estimation |
    | `feature_investment_strategies` | User investment strategy templates |
    | `feature_watchlist_alerts` | Property watchlist with alerts |
    | `feature_portfolio_tracking` | Track acquired properties (V2) |
    | `feature_team_collaboration` | Property sharing and comments |
    | `feature_mobile_notifications` | Push notification support |
    | `feature_notes_checklist` | Property notes and due diligence checklist |
    | `feature_export_csv` | CSV data export |
    | `feature_save_property` | Save properties to list |
    | `feature_kanban_board` | Kanban board workflow stages |

    ## AI Quality Thresholds

    These thresholds prevent False positives from minimal data:

    | Threshold | Default | Description |
    |----------|---------|-------------|
    | `anomaly_min_comps` | 3 | Minimum comparable sales required |
    | `anomaly_min_confidence` | 0.700 | Minimum confidence score |
    | `anomaly_max_zscore` | 2.50 | Maximum price z-score |
    | `comps_analysis_min_samples` | 3 | Minimum comps for analysis |
    | `comps_analysis_max_distance_miles` | 1.0 | Max distance for comps |
    | `comps_analysis_max_age_days` | 365 | Max age of comp data |

    ## Lock Flags

    Each feature has a corresponding `feature_lock_*` flag. When `True`, the feature
    cannot be overridden at county or user level.

    ---
    ## Example Response

    \\`json
    {
      "id": 1,
      "feature_market_anomaly_detection": True,
      "feature_save_property": True,
      "feature_kanban_board": True,
      "feature_lock_market_anomaly_detection": False,
      "anomaly_min_comps": 3,
      "anomaly_min_confidence": 0.700,
      "updated_at": "2025-12-29T12:00:00Z"
    }
    \\`
    """,
    tags=["Settings"],
    responses={
        200: {
            "description": "Admin settings retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "feature_market_anomaly_detection": True,
                        "feature_save_property": True,
                        "feature_kanban_board": True,
                        "anomaly_min_comps": 3,
                        "anomaly_min_confidence": 0.7
                    }
                }
            }
        }
    }
)
async def get_admin_settings():
    """Get admin feature settings"""
    try:
        settings = await feature_service.get_admin_settings_detailed()
        return settings
    except Exception as e:
        logger.error(f"Error getting admin settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/settings/admin",
    summary="Update Admin Feature Settings",
    description="""
    Update global admin feature toggle settings and AI quality thresholds.

    ## Partial Updates

    Only include the fields you want to change. Omitted fields will remain unchanged.

    ## Feature Toggle Fields

    To enable/disable a feature:
    \\`json
    {
      "feature_market_anomaly_detection": True,
      "feature_save_property": True
    }
    \\`

    ## AI Quality Thresholds

    Adjust thresholds to prevent False positives:
    \\`json
    {
      "anomaly_min_comps": 5,
      "anomaly_min_confidence": 0.800,
      "comps_analysis_max_distance_miles": 0.5
    }
    \\`

    ## Lock Flags

    Lock a feature to prevent county/user overrides:
    \\`json
    {
      "feature_lock_market_anomaly_detection": True
    }
    \\`
    """,
    tags=["Settings"],
    responses={
        200: {
            "description": "Settings updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "feature_market_anomaly_detection": True,
                        "updated_at": "2025-12-29T12:30:00Z"
                    }
                }
            }
        }
    }
)
async def update_admin_settings(updates: AdminFeatureSettingsUpdate):
    """Update admin feature settings"""
    try:
        # Remove None values
        update_data = updates.model_dump(exclude_none=True)
        result = await feature_service.update_admin_settings(update_data)
        return result
    except Exception as e:
        logger.error(f"Error updating admin settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    summary="Deal Intelligence Health Check",
    description="""
    Health check endpoint for the Deal Intelligence API.

    Returns the status of all core services and their feature availability.

    ## Services Checked

    | Service | Description |
    |---------|-------------|
    | `feature_toggle` | Feature toggle system status |
    | `market_anomaly` | Price anomaly detection service |
    | `comparable_sales` | Comparable sales analysis service |
    | `saved_properties` | Saved properties and Kanban service |
    | `renovation` | Renovation estimator service |
    | `investment_strategies` | Investment strategy service |
    | `watchlist` | Watchlist and alerts service |

    ## Example Response

    \\`json
    {
      "status": "healthy",
      "timestamp": "2025-12-29T12:00:00Z",
      "services": {
        "feature_toggle": "ok",
        "market_anomaly": "ok",
        "saved_properties": "ok"
      }
    }
    \\`
    """,
    tags=["Health"],
    responses={
        200: {
            "description": "All services healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2025-12-29T12:00:00Z",
                        "services": {
                            "feature_toggle": "ok",
                            "market_anomaly": "ok"
                        }
                    }
                }
            }
        }
    }
)
async def health_check():
    """Health check for Deal Intelligence API"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "feature_toggle": "ok",
            "market_anomaly": "ok",
            "comparable_sales": "ok",
            "saved_properties": "ok",
            "renovation": "ok",
            "investment_strategies": "ok",
            "watchlist": "ok"
        }
    }


@router.get("/settings/county/{county_id}")
async def get_county_settings(county_id: int):
    """Get county feature overrides"""
    try:
        settings = await feature_service.get_county_settings(county_id)
        return settings or {"message": "No county settings configured"}
    except Exception as e:
        logger.error(f"Error getting county settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/county")
async def create_county_settings(settings: CountyFeatureSettingsCreate):
    """Create county feature overrides"""
    try:
        data = settings.model_dump(exclude_none=True)
        result = await feature_service.create_county_settings(
            county_id=data.pop("county_id"),
            settings=data
        )
        return result
    except Exception as e:
        logger.error(f"Error creating county settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/county/{county_id}")
async def update_county_settings(
    county_id: int,
    settings: CountyFeatureSettingsUpdate
):
    """Update county feature overrides"""
    try:
        data = settings.model_dump(exclude_none=True)
        result = await feature_service.update_county_settings(county_id, data)
        return result
    except Exception as e:
        logger.error(f"Error updating county settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/settings/county/{county_id}")
async def delete_county_settings(county_id: int):
    """Delete county settings (revert to admin defaults)"""
    try:
        await feature_service.delete_county_settings(county_id)
        return {"message": "County settings deleted"}
    except Exception as e:
        logger.error(f"Error deleting county settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/user/{user_id}")
async def get_user_preferences(user_id: str):
    """Get user feature preferences"""
    try:
        prefs = await feature_service.list_user_preferences(user_id)
        return prefs
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/user")
async def create_user_preferences(
    preferences: UserPreferencesCreate,
    user_id: str = Depends(get_user_id_from_header)
):
    """Create user feature preferences"""
    try:
        data = preferences.model_dump(exclude_none=True)
        result = await feature_service.create_user_preferences(
            user_id=user_id,
            county_id=data.pop("county_id", None),  # Optional
            preferences=data
        )
        return result
    except Exception as e:
        logger.error(f"Error creating user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/user/{user_id}")
async def update_user_preferences(
    user_id: str,
    preferences: UserPreferencesUpdate
):
    """Update user feature preferences"""
    try:
        data = preferences.model_dump(exclude_none=True)
        result = await feature_service.update_user_preferences(user_id, data)
        return result
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/settings/user/{user_id}")
async def delete_user_preferences(user_id: str):
    """Delete user preferences (revert to inherited settings)"""
    try:
        await feature_service.delete_user_preferences(user_id)
        return {"message": "User preferences deleted"}
    except Exception as e:
        logger.error(f"Error deleting user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MARKET ANOMALY ROUTES
# =============================================================================

@router.get("/market-anomalies")
async def get_market_anomalies(
    county_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=500),
    only_anomalies: bool = True
):
    """Get list of market anomalies"""
    try:
        anomalies = await anomaly_service.get_anomalies_batch(
            county_id=county_id,
            limit=limit,
            only_anomalies=only_anomalies
        )
        return {"anomalies": anomalies}
    except Exception as e:
        logger.error(f"Error getting market anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-anomalies/property/{property_id}")
async def get_property_anomaly(property_id: int):
    """Get anomaly analysis for a specific property"""
    try:
        anomaly = await anomaly_service.get_property_anomaly(property_id)
        if not anomaly:
            raise HTTPException(status_code=404, detail="Anomaly analysis not found")
        return anomaly
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting property anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/market-anomalies/analyze",
    summary="Analyze Property for Market Anomalies",
    description="""
    Analyze a property for price anomalies using Zillow comparable sales data.

    ## Analysis Process
    1. Fetches comparable properties from Zillow near the target property
    2. Calculates statistical measures (mean, median, standard deviation)
    3. Computes Z-score to identify price anomalies
    4. Returns anomaly analysis with confidence score

    ## AI Data Quality Checks
    This endpoint uses AI data quality monitoring to prevent False positives:
    - Minimum 3 comparable sales required
    - Minimum confidence threshold (configurable, default 0.7)
    - Maximum Z-score threshold (configurable, default 2.5)

    ## Feature Toggle
    Requires the `market_anomaly_detection` feature to be enabled.

    ## Error Responses
    - **422 Unprocessable Entity**: Missing required fields (county_id)
    - **400 Bad Request**: Analysis failed or feature disabled

    ## Example Request
    ```json
    {
        "property_id": 1556,
        "county_id": 1
    }
    ```

    ## Example Response
    ```json
    {
        "id": 1,
        "property_id": 1556,
        "is_anomaly": True,
        "z_score": 2.8,
        "price_difference_percent": 35.5,
        "comparable_count": 5,
        "avg_comparable_price": 125000,
        "confidence_score": 0.85,
        "analysis_date": "2025-01-15T10:30:00Z"
    }
    ```
    """,
    tags=["Market Anomalies"],
    responses={
        200: {
            "description": "Market anomaly analysis completed",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "property_id": 1556,
                        "is_anomaly": True,
                        "z_score": 2.8,
                        "price_difference_percent": 35.5,
                        "comparable_count": 5,
                        "confidence_score": 0.85
                    }
                }
            }
        },
        400: {"description": "Bad request - Analysis failed or feature disabled"},
        422: {"description": "Unprocessable entity - Missing county_id"},
        500: {"description": "Internal server error"}
    }
)
async def analyze_market_anomaly(request: AnomalyAnalysisRequest):
    """Trigger market anomaly analysis for a property"""
    try:
        analysis = await anomaly_service.analyze_property(
            property_id=request.property_id,
            address=request.address,
            list_price=request.list_price,
            county_id=request.county_id
        )
        if not analysis:
            raise HTTPException(status_code=400, detail="Analysis failed or feature disabled")
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing market anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/market-anomalies/{anomaly_id}/verify")
async def verify_anomaly(
    anomaly_id: int,
    updates: AnomalyVerificationUpdate,
    user_id: str = Depends(get_user_id_from_header)
):
    """Verify/correct an anomaly analysis (human feedback)"""
    try:
        success = await anomaly_service.update_verification(
            anomaly_id=anomaly_id,
            user_id=user_id,
            is_verified=updates.is_verified,
            feedback=updates.feedback
        )
        if not success:
            raise HTTPException(status_code=404, detail="Anomaly not found")
        return {"message": "Verification updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# COMPARABLE SALES ROUTES
# =============================================================================

@router.get("/comparable-sales/{property_id}")
async def get_comps_analysis(property_id: int):
    """Get comparable sales analysis for a property"""
    try:
        analysis = await comps_service.get_analysis(property_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comps analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparable-sales/{analysis_id}/comps")
async def get_comparables(analysis_id: int):
    """Get comparable properties for an analysis"""
    try:
        comps = await comps_service.get_comparables(analysis_id)
        return {"comparables": comps}
    except Exception as e:
        logger.error(f"Error getting comparables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comparable-sales/analyze")
async def analyze_comps(request: CompsAnalysisRequest):
    """Trigger comparable sales analysis for a property"""
    try:
        analysis = await comps_service.analyze_property(
            property_id=request.property_id,
            county_id=request.county_id
        )
        if not analysis:
            raise HTTPException(status_code=400, detail="Analysis failed or feature disabled")
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing comps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SAVED PROPERTIES & KANBAN ROUTES
# =============================================================================

@router.get(
    "/saved/{user_id}",
    summary="Get Saved Properties",
    description="""
    Retrieve all saved properties for a user, optionally filtered by Kanban stage.

    ## Saved Properties Feature
    Users can save properties they're interested in and optionally assign them to Kanban stages for deal tracking.

    ## Kanban Stages
    | Stage | Description |
    |-------|-------------|
    | `researching` | Initial research phase |
    | `analyzing` | Deep analysis in progress |
    | `due_diligence` | Due diligence tasks |
    | `bidding` | Preparing/placing bid |
    | `won` | Successfully acquired |
    | `lost` | Didn't get the property |
    | `archived` | No longer relevant |

    ## Feature Toggle
    This endpoint requires the `save_property` feature to be enabled. The Kanban functionality requires the `kanban_board` feature to be enabled.

    ## Authentication
    Requires user authentication via frontend. The user_id in the path must match the authenticated user.
    """,
    tags=["Saved Properties"],
    responses={
        200: {
            "description": "Saved properties retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "saved_properties": [
                            {
                                "id": 1,
                                "user_id": "user123",
                                "property_id": 1556,
                                "notes": "Great potential, needs roof repair",
                                "kanban_stage": "researching",
                                "stage_updated_at": "2025-01-15T10:30:00Z",
                                "saved_at": "2025-01-15T10:30:00Z",
                                "foreclosure_listings": {
                                    "id": 1556,
                                    "address": "123 Main St",
                                    "city": "Jacksonville",
                                    "state": "FL",
                                    "zip_code": "32205",
                                    "opening_bid": 75000,
                                    "approx_upset": 85000,
                                    "sale_date": "2025-02-01"
                                }
                            }
                        ]
                    }
                }
            }
        },
        401: {"description": "Unauthorized - User not authenticated"},
        403: {"description": "Forbidden - Feature disabled"},
        500: {"description": "Internal server error"}
    }
)
async def get_saved_properties(
    user_id: str,
    kanban_stage: Optional[str] = None
):
    """Get saved properties for a user"""
    try:
        properties = await saved_service.get_saved_properties(user_id, kanban_stage)
        return {"saved_properties": properties}
    except Exception as e:
        logger.error(f"Error getting saved properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/saved",
    summary="Save Property",
    description="""
    Save a property to the user's saved properties list and optionally assign it to a Kanban stage.

    ## Request Headers
    - **X-User-ID** (required): User ID from authenticated session

    ## Feature Toggle
    Requires the `save_property` feature to be enabled. Kanban stage assignment requires `kanban_board` feature to be enabled.

    ## Error Responses
    - **400 Bad Request**: Property does not exist, feature disabled, or property already saved
    - **401 Unauthorized**: Missing or invalid X-User-ID header
    - **403 Forbidden**: Feature is disabled for this user/county

    ## Example Request
    ```json
    {
        "property_id": 1556,
        "notes": "Great potential, needs roof repair",
        "kanban_stage": "researching"
    }
    ```
    """,
    tags=["Saved Properties"],
    responses={
        200: {
            "description": "Property saved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": "user123",
                        "property_id": 1556,
                        "notes": "Great potential, needs roof repair",
                        "kanban_stage": "researching",
                        "stage_updated_at": "2025-01-15T10:30:00Z",
                        "saved_at": "2025-01-15T10:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Bad request - Property does not exist, feature disabled, or already saved"},
        401: {"description": "Unauthorized - Missing X-User-ID header"},
        403: {"description": "Forbidden - Feature disabled"},
        500: {"description": "Internal server error"}
    }
)
async def save_property(
    request: SavePropertyRequest,
    user_id: str = Depends(get_user_id_from_header)
):
    """Save a property"""
    try:
        saved = await saved_service.save_property(
            user_id=user_id,
            property_id=request.property_id,
            notes=request.notes,
            kanban_stage=request.kanban_stage
        )
        if not saved:
            raise HTTPException(
                status_code=400,
                detail="Failed to save property. The property may not exist, the feature may be disabled, or the property is already saved."
            )
        return saved
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/saved/{saved_id}",
    summary="Unsave Property",
    description="""
    Remove a property from the user's saved properties list.

    ## Request Headers
    - **X-User-ID** (required): User ID from authenticated session

    ## Authorization
    Users can only unsave properties that belong to them. This endpoint verifies ownership before deletion.

    ## Error Responses
    - **403 Forbidden**: User is not authorized to unsave this property (not the owner)
    - **404 Not Found**: Saved property not found

    ## Example Response
    ```json
    {
        "message": "Property unsaved"
    }
    ```
    """,
    tags=["Saved Properties"],
    responses={
        200: {
            "description": "Property unsaved successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Property unsaved"}
                }
            }
        },
        403: {"description": "Forbidden - Not authorized to unsave this property"},
        404: {"description": "Not found - Saved property not found"},
        500: {"description": "Internal server error"}
    }
)
async def unsave_property(
    saved_id: int,
    user_id: str = Depends(get_user_id_from_header)
):
    """Unsave/remove a saved property"""
    try:
        # First verify ownership
        saved = await saved_service.get_saved_properties(user_id)
        if not any(s.get("id") == saved_id for s in saved):
            raise HTTPException(status_code=403, detail="Not authorized to unsave this property")

        success = await saved_service.unsave_property(user_id, saved_id)
        if not success:
            raise HTTPException(status_code=404, detail="Saved property not found")
        return {"message": "Property unsaved"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsaving property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/saved/stage",
    summary="Update Kanban Stage",
    description="""
    Move a saved property to a new Kanban stage.

    ## Request Headers
    - **X-User-ID** (required): User ID from authenticated session

    ## Kanban Stages
    | Stage | Description |
    |-------|-------------|
    | `researching` | Initial research phase |
    | `analyzing` | Deep analysis in progress |
    | `due_diligence` | Due diligence tasks |
    | `bidding` | Preparing/placing bid |
    | `won` | Successfully acquired |
    | `lost` | Didn't get the property |
    | `archived` | No longer relevant |

    ## Feature Toggle
    Requires the `kanban_board` feature to be enabled.

    ## Example Request
    ```json
    {
        "saved_id": 1,
        "new_stage": "analyzing"
    }
    ```

    ## Example Response
    ```json
    {
        "id": 1,
        "user_id": "user123",
        "property_id": 1556,
        "kanban_stage": "analyzing",
        "stage_updated_at": "2025-01-15T14:30:00Z",
        "saved_at": "2025-01-15T10:30:00Z"
    }
    ```
    """,
    tags=["Kanban Board"],
    responses={
        200: {
            "description": "Kanban stage updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": "user123",
                        "property_id": 1556,
                        "kanban_stage": "analyzing",
                        "stage_updated_at": "2025-01-15T14:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Bad request - Invalid stage or update failed"},
        403: {"description": "Forbidden - Not authorized to update this property"},
        500: {"description": "Internal server error"}
    }
)
async def update_kanban_stage(
    request: KanbanStageUpdate,
    user_id: str = Depends(get_user_id_from_header)
):
    """Move property to new Kanban stage"""
    try:
        # Verify ownership
        saved = await saved_service.get_saved_properties(user_id)
        if not any(s.get("id") == request.saved_id for s in saved):
            raise HTTPException(status_code=403, detail="Not authorized to update this property")

        result = await saved_service.update_kanban_stage(
            user_id=user_id,
            saved_id=request.saved_id,
            new_stage=request.new_stage
        )
        if not result:
            raise HTTPException(status_code=400, detail="Invalid stage or update failed")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Kanban stage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/saved/{user_id}/kanban",
    summary="Get Kanban Board",
    description="""
    Retrieve the user's complete Kanban board with all properties organized by stage.

    ## Response Format
    Returns a dictionary with stage names as keys and lists of properties as values.

    ## Kanban Stages
    | Stage | Description |
    |-------|-------------|
    | `researching` | Initial research phase |
    | `analyzing` | Deep analysis in progress |
    | `due_diligence` | Due diligence tasks |
    | `bidding` | Preparing/placing bid |
    | `won` | Successfully acquired |
    | `lost` | Didn't get the property |
    | `archived` | No longer relevant |

    ## Feature Toggle
    Requires the `kanban_board` feature to be enabled. If disabled, returns all saved properties under a single \"all\" key.

    ## Example Response
    ```json
    {
        "researching": [
            {
                "id": 1,
                "property_id": 1556,
                "notes": "Initial interest",
                "kanban_stage": "researching",
                "foreclosure_listings": {
                    "id": 1556,
                    "address": "123 Main St",
                    "city": "Jacksonville",
                    "state": "FL"
                }
            }
        ],
        "analyzing": [],
        "due_diligence": [],
        "bidding": [],
        "won": [],
        "lost": [],
        "archived": []
    }
    ```
    """,
    tags=["Kanban Board"],
    responses={
        200: {
            "description": "Kanban board retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "researching": [
                            {
                                "id": 1,
                                "property_id": 1556,
                                "kanban_stage": "researching",
                                "foreclosure_listings": {
                                    "id": 1556,
                                    "address": "123 Main St"
                                }
                            }
                        ],
                        "analyzing": [],
                        "due_diligence": [],
                        "bidding": [],
                        "won": [],
                        "lost": [],
                        "archived": []
                    }
                }
            }
        },
        500: {"description": "Internal server error"}
    }
)
async def get_kanban_board(user_id: str):
    """Get user's Kanban board"""
    try:
        board = await saved_service.get_kanban_board(user_id)
        return board
    except Exception as e:
        logger.error(f"Error getting Kanban board: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/saved/{saved_id}/notes")
async def update_property_notes(
    saved_id: int,
    request: NotesUpdate,
    user_id: str = Depends(get_user_id_from_header)
):
    """Update notes for a saved property"""
    try:
        # Verify ownership
        saved = await saved_service.get_saved_properties(user_id)
        if not any(s.get("id") == saved_id for s in saved):
            raise HTTPException(status_code=403, detail="Not authorized to update this property")

        result = await saved_service.update_notes(user_id, saved_id, request.notes)
        if not result:
            raise HTTPException(status_code=404, detail="Saved property not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/saved/bulk-update")
async def bulk_update_stages(
    request: BulkStageUpdate,
    user_id: str = Depends(get_user_id_from_header)
):
    """Bulk update Kanban stages"""
    try:
        result = await saved_service.bulk_update_stages(user_id, request.updates)
        return result
    except Exception as e:
        logger.error(f"Error bulk updating stages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved/{user_id}/stats")
async def get_saved_stats(user_id: str):
    """Get statistics about saved properties"""
    try:
        stats = await saved_service.get_property_stats(user_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting saved stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# RENOVATION ESTIMATOR ROUTES
# =============================================================================

@router.post(
    "/renovation/estimate",
    summary="Create Renovation Cost Estimate",
    description="""
    Analyze property photos using GPT-4o Vision API and estimate renovation costs.

    ## Request Headers
    - **X-User-ID** (required): User ID from authenticated session

    ## Analysis Process
    1. Each photo is analyzed using GPT-4o Vision API
    2. AI identifies: room type, condition rating (1-5), issues, and renovation level
    3. Cost estimates are calculated based on room type and condition
    4. AI summary is generated for the investor

    ## Cost Estimates by Room and Condition
    | Room | Condition | Cost Range |
    |------|-----------|------------|
    | Kitchen | Cosmetic | $5,000 - $15,000 |
    | Kitchen | Moderate | $15,000 - $35,000 |
    | Kitchen | Major | $35,000 - $70,000 |
    | Bathroom | Cosmetic | $2,000 - $5,000 |
    | Bathroom | Moderate | $5,000 - $15,000 |
    | Bathroom | Major | $15,000 - $35,000 |

    ## AI Data Quality Checks
    - Minimum photo count required (configurable, default 3)
    - Confidence score calculated based on photo coverage and consistency
    - Analysis quality rating: high, medium, or low

    ## Feature Toggle
    Requires the `renovation_cost_estimator` feature to be enabled.

    ## Example Request
    ```json
    {
        "property_id": 1556,
        "photo_urls": [
            "https://example.com/photo1.jpg",
            "https://example.com/photo2.jpg"
        ]
    }
    ```

    ## Example Response
    ```json
    {
        "id": 1,
        "property_id": 1556,
        "total_estimated_cost": 25000,
        "room_breakdown": {
            "kitchen": {"total_min": 20000, "total_max": 35000},
            "bathroom": {"total_min": 5000, "total_max": 12000}
        },
        "ai_summary": "Kitchen needs moderate renovation including cabinets and appliances...",
        "confidence_score": 0.75,
        "photo_count": 5
    }
    ```
    """,
    tags=["Deal Intelligence (V2)"],
    responses={
        200: {
            "description": "Renovation estimate created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "property_id": 1556,
                        "total_estimated_cost": 25000,
                        "confidence_score": 0.75
                    }
                }
            }
        },
        400: {"description": "Bad request - Feature disabled or insufficient photos"},
        500: {"description": "Internal server error"}
    }
)
async def create_renovation_estimate(
    request: RenovationEstimateRequest,
    user_id: str = Depends(get_user_id_from_header)
):
    """Analyze property photos and estimate renovation costs"""
    try:
        estimate = await renovation_service.estimate_from_photos(
            property_id=request.property_id,
            photo_urls=request.photo_urls,
            user_id=user_id
        )
        return estimate
    except Exception as e:
        logger.error(f"Error creating renovation estimate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/renovation/estimate/{property_id}",
    summary="Get Renovation Estimate",
    description="Get most recent renovation estimate for a property",
    tags=["Deal Intelligence (V2)"]
)
async def get_renovation_estimate(property_id: int):
    """Get most recent renovation estimate for a property"""
    try:
        estimate = await renovation_service.get_saved_estimate(property_id)
        if not estimate:
            raise HTTPException(status_code=404, detail="Renovation estimate not found")
        return estimate
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting renovation estimate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/renovation/estimate/{estimate_id}",
    summary="Update Renovation Estimate",
    description="Update renovation estimate with manual override",
    tags=["Deal Intelligence (V2)"]
)
async def update_renovation_estimate(
    estimate_id: int,
    request: RenovationManualUpdate
):
    """Update renovation estimate with manual override"""
    try:
        updated = await renovation_service.update_manual_estimate(
            estimate_id=estimate_id,
            manual_total=request.manual_total,
            adjustments=request.adjustments
        )
        return updated
    except Exception as e:
        logger.error(f"Error updating renovation estimate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# INVESTMENT STRATEGY ROUTES
# =============================================================================

@router.get(
    "/strategies/{user_id}",
    summary="Get Investment Strategies",
    description="Get all investment strategies for a user",
    tags=["Deal Intelligence (V2)"]
)
async def get_strategies(
    user_id: str,
    active_only: bool = True
):
    """Get investment strategies for a user"""
    try:
        strategies = await investment_service.get_strategies(user_id, active_only)
        return {"strategies": strategies}
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/strategies",
    summary="Create Investment Strategy",
    description="Create a new investment strategy for a user",
    tags=["Deal Intelligence (V2)"]
)
async def create_strategy(
    request: InvestmentStrategyCreate,
    user_id: str = Depends(get_user_id_from_header)
):
    """Create a new investment strategy"""
    try:
        strategy = await investment_service.create_strategy(
            user_id=user_id,
            strategy_name=request.strategy_name,
            strategy_type=request.strategy_type,
            min_fix_and_flip_profit=request.min_fix_and_flip_profit,  # Database column
            max_purchase_price=request.max_purchase_price,
            min_arv_spread=request.min_arv_spread,
            max_repair_cost=request.max_repair_cost,  # Database column
            max_holding_months=request.max_holding_months,
            min_cash_flow=request.min_cash_flow,
            custom_criteria=request.custom_criteria
        )
        return strategy
    except Exception as e:
        logger.error(f"Error creating strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/strategies/{user_id}/{strategy_id}",
    summary="Get Investment Strategy",
    description="Get a specific investment strategy",
    tags=["Deal Intelligence (V2)"]
)
async def get_strategy(user_id: str, strategy_id: int):
    """Get a specific investment strategy"""
    try:
        strategy = await investment_service.get_strategy(strategy_id, user_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/strategies/{strategy_id}",
    summary="Update Investment Strategy",
    description="Update an existing investment strategy",
    tags=["Deal Intelligence (V2)"]
)
async def update_strategy(
    strategy_id: int,
    user_id: str,
    updates: InvestmentStrategyUpdate
):
    """Update an investment strategy"""
    try:
        strategy = await investment_service.update_strategy(
            strategy_id=strategy_id,
            user_id=user_id,
            **updates.model_dump(exclude_none=True)
        )
        return strategy
    except Exception as e:
        logger.error(f"Error updating strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/strategies/{strategy_id}",
    summary="Delete Investment Strategy",
    description="Delete an investment strategy",
    tags=["Deal Intelligence (V2)"]
)
async def delete_strategy(strategy_id: int, user_id: str):
    """Delete an investment strategy"""
    try:
        success = await investment_service.delete_strategy(strategy_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return {"message": "Strategy deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/strategies/{strategy_id}/set-default",
    summary="Set Default Strategy",
    description="Set a strategy as the default for a user",
    tags=["Deal Intelligence (V2)"]
)
async def set_default_strategy(strategy_id: int, user_id: str):
    """Set a strategy as default for a user"""
    try:
        strategy = await investment_service.set_default_strategy(strategy_id, user_id)
        return strategy
    except Exception as e:
        logger.error(f"Error setting default strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/strategies/{strategy_id}/evaluate/{property_id}",
    summary="Evaluate Property Against Strategy",
    description="Evaluate if a property meets strategy criteria",
    tags=["Deal Intelligence (V2)"]
)
async def evaluate_property_against_strategy(
    strategy_id: int,
    property_id: int,
    user_id: str
):
    """Evaluate if a property meets strategy criteria"""
    try:
        evaluation = await investment_service.evaluate_property_against_strategy(
            property_id=property_id,
            strategy_id=strategy_id,
            user_id=user_id
        )
        return evaluation
    except Exception as e:
        logger.error(f"Error evaluating property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WATCHLIST & ALERTS ROUTES
# =============================================================================

@router.get("/watchlist/{user_id}")
async def get_watchlist(
    user_id: str,
    priority: Optional[str] = None
):
    """Get user's watchlist"""
    try:
        watchlist = await watchlist_service.get_watchlist(user_id, priority)
        return {"watchlist": watchlist}
    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist")
async def add_to_watchlist(
    request: WatchlistAddRequest,
    user_id: str = Depends(get_user_id_from_header)
):
    """Add property to watchlist"""
    try:
        entry = await watchlist_service.add_to_watchlist(
            user_id=user_id,
            property_id=request.property_id,
            alert_on_price_change=request.alert_on_price_change,
            alert_on_status_change=request.alert_on_status_change,
            alert_on_new_comps=request.alert_on_new_comps,
            alert_on_auction_near=request.alert_on_auction_near,
            auction_alert_days=request.auction_alert_days,
            watch_notes=request.watch_notes,
            priority=request.priority
        )
        return entry
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{property_id}")
async def remove_from_watchlist(
    property_id: int,
    user_id: str = Depends(get_user_id_from_header)
):
    """Remove property from watchlist"""
    try:
        success = await watchlist_service.remove_from_watchlist(user_id, property_id)
        if not success:
            raise HTTPException(status_code=404, detail="Watchlist entry not found")
        return {"message": "Removed from watchlist"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/watchlist/{property_id}")
async def update_watchlist_entry(
    property_id: int,
    updates: WatchlistUpdateRequest,
    user_id: str = Depends(get_user_id_from_header)
):
    """Update watchlist entry"""
    try:
        entry = await watchlist_service.update_watchlist_entry(
            user_id=user_id,
            property_id=property_id,
            updates=updates.model_dump(exclude_none=True)
        )
        if not entry:
            raise HTTPException(status_code=404, detail="Watchlist entry not found")
        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/{user_id}")
async def get_alerts(
    user_id: str,
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=500)
):
    """Get alerts for a user"""
    try:
        alerts = await watchlist_service.get_alerts(user_id, unread_only, limit)
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    user_id: str = Depends(get_user_id_from_header)
):
    """Mark alert as read"""
    try:
        success = await watchlist_service.mark_alert_read(alert_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": "Alert marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking alert read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/alerts/{user_id}/read-all")
async def mark_all_alerts_read(user_id: str):
    """Mark all alerts as read"""
    try:
        count = await watchlist_service.mark_all_alerts_read(user_id)
        return {"marked_read": count}
    except Exception as e:
        logger.error(f"Error marking all alerts read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    user_id: str = Depends(get_user_id_from_header)
):
    """Delete an alert"""
    try:
        success = await watchlist_service.delete_alert(alert_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": "Alert deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PORTFOLIO TRACKING ROUTES
# =============================================================================
# V2 ONLY: Portfolio tracking is not part of V1 MVP
# @router.get("/portfolio/{user_id}")
# async def get_portfolio(
#     user_id: str,
#     status: Optional[str] = None
# ):
#     """Get user's portfolio"""
#     try:
#         portfolio = await portfolio_service.get_portfolio(user_id, status)
#         return {"portfolio": portfolio}
#     except Exception as e:
#         logger.error(f"Error getting portfolio: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.get("/portfolio/{user_id}/summary")
# async def get_portfolio_summary(user_id: str):
#     """Get portfolio summary statistics"""
#     try:
#         summary = await portfolio_service.get_portfolio_summary(user_id)
#         return summary
#     except Exception as e:
#         logger.error(f"Error getting portfolio summary: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.post("/portfolio")
# async def add_to_portfolio(
#     request: PortfolioAddRequest,
#     user_id: str = Depends(get_user_id_from_header)
# ):
#     """Add acquired property to portfolio"""
#     try:
#         entry = await portfolio_service.add_to_portfolio(
#             user_id=user_id,
#             property_id=request.property_id,
#             acquisition_date=request.acquisition_date,
#             purchase_price=request.purchase_price,
#             rehab_cost=request.rehab_cost,
#             strategy_used=request.strategy_used,
#             arv_target=request.arv_target
#         )
#         return entry
#     except Exception as e:
#         logger.error(f"Error adding to portfolio: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.get("/portfolio/entry/{entry_id}")
# async def get_portfolio_entry(entry_id: int, user_id: str):
#     """Get specific portfolio entry"""
#     try:
#         entry = await portfolio_service.get_portfolio_entry(entry_id, user_id)
#         if not entry:
#             raise HTTPException(status_code=404, detail="Portfolio entry not found")
#         return entry
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting portfolio entry: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.put("/portfolio/entry/{entry_id}")
# async def update_portfolio_entry(
#     entry_id: int,
#     user_id: str,
#     updates: PortfolioUpdateRequest
# ):
#     """Update portfolio entry"""
#     try:
#         entry = await portfolio_service.update_portfolio_entry(
#             entry_id=entry_id,
#             user_id=user_id,
#             current_value=updates.current_value,
#             actual_arv=updates.actual_arv,
#             portfolio_status=updates.portfolio_status,
#             sale_date=updates.sale_date,
#             sale_price=updates.sale_price
#         )
#         return entry
#     except Exception as e:
#         logger.error(f"Error updating portfolio entry: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.delete("/portfolio/entry/{entry_id}")
# async def remove_from_portfolio(
#     entry_id: int,
#     user_id: str = Depends(get_user_id_from_header)
# ):
#     """Remove property from portfolio"""
#     try:
#         success = await portfolio_service.remove_from_portfolio(entry_id, user_id)
#         if not success:
#             raise HTTPException(status_code=404, detail="Portfolio entry not found")
#         return {"message": "Removed from portfolio"}
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error removing from portfolio: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# TEAM COLLABORATION ROUTES
# =============================================================================

@router.post(
    "/collaboration/share",
    summary="Share Property",
    description="Share a property with another user",
    tags=["Deal Intelligence (V2)"]
)
async def share_property(
    request: SharePropertyRequest,
    user_id: str = Depends(get_user_id_from_header)
):
    """Share property with another user"""
    try:
        share = await collaboration_service.share_property(
            property_id=request.property_id,
            shared_by_user_id=user_id,
            shared_with_user_id=request.shared_with_user_id,
            share_type=request.share_type,
            share_message=request.share_message
        )
        return share
    except Exception as e:
        logger.error(f"Error sharing property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/collaboration/share/{share_id}",
    summary="Unshare Property",
    description="Remove a property share",
    tags=["Deal Intelligence (V2)"]
)
async def unshare_property(
    share_id: int,
    user_id: str = Depends(get_user_id_from_header)
):
    """Remove property share"""
    try:
        success = await collaboration_service.unshare_property(share_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Share not found")
        return {"message": "Property unshared"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsharing property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/collaboration/shared-with-me/{user_id}",
    summary="Get Properties Shared With Me",
    description="Get properties shared with the user",
    tags=["Deal Intelligence (V2)"]
)
async def get_shared_with_me(user_id: str):
    """Get properties shared with user"""
    try:
        shared = await collaboration_service.get_shared_with_me(user_id)
        return {"shared_properties": shared}
    except Exception as e:
        logger.error(f"Error getting shared properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/collaboration/shared-by-me/{user_id}",
    summary="Get Properties Shared By Me",
    description="Get properties the user has shared with others",
    tags=["Deal Intelligence (V2)"]
)
async def get_shared_by_me(user_id: str):
    """Get properties user has shared"""
    try:
        shared = await collaboration_service.get_shared_by_me(user_id)
        return {"shared_properties": shared}
    except Exception as e:
        logger.error(f"Error getting shared by me: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collaboration/comments",
    summary="Add Comment",
    description="Add a comment to a property",
    tags=["Deal Intelligence (V2)"]
)
async def add_comment(
    request: CommentAddRequest,
    user_id: str = Depends(get_user_id_from_header)
):
    """Add comment to property"""
    try:
        comment = await collaboration_service.add_comment(
            property_id=request.property_id,
            user_id=user_id,
            comment_text=request.comment_text,
            parent_comment_id=request.parent_comment_id
        )
        return comment
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/collaboration/comments/{property_id}",
    summary="Get Property Comments",
    description="Get all comments for a property",
    tags=["Deal Intelligence (V2)"]
)
async def get_comments(property_id: int, include_deleted: bool = False):
    """Get comments for a property"""
    try:
        comments = await collaboration_service.get_comments(property_id, include_deleted)
        return {"comments": comments}
    except Exception as e:
        logger.error(f"Error getting comments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/collaboration/comments/{comment_id}",
    summary="Update Comment",
    description="Update a comment",
    tags=["Deal Intelligence (V2)"]
)
async def update_comment(
    comment_id: int,
    request: CommentUpdateRequest,
    user_id: str = Depends(get_user_id_from_header)
):
    """Update comment"""
    try:
        comment = await collaboration_service.update_comment(
            comment_id=comment_id,
            user_id=user_id,
            comment_text=request.comment_text
        )
        return comment
    except Exception as e:
        logger.error(f"Error updating comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/collaboration/comments/{comment_id}",
    summary="Delete Comment",
    description="Delete a comment",
    tags=["Deal Intelligence (V2)"]
)
async def delete_comment(
    comment_id: int,
    user_id: str = Depends(get_user_id_from_header)
):
    """Delete comment"""
    try:
        success = await collaboration_service.delete_comment(comment_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Comment not found")
        return {"message": "Comment deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# NOTES & CHECKLIST ROUTES
# =============================================================================

@router.get("/notes/{property_id}")
async def get_notes(property_id: int, note_type: Optional[str] = None):
    """Get notes for a property"""
    try:
        notes = await notes_service.get_notes(property_id, note_type)
        return {"notes": notes}
    except Exception as e:
        logger.error(f"Error getting notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes")
async def add_note(
    request: NoteAddRequest,
    user_id: str = Depends(get_user_id_from_header)
):
    """Add note to property"""
    try:
        note = await notes_service.add_note(
            property_id=request.property_id,
            user_id=user_id,
            note_text=request.content,
            note_type=request.note_type
        )
        return note
    except Exception as e:
        logger.error(f"Error adding note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notes/{note_id}")
async def update_note(
    note_id: int,
    request: NoteUpdateRequest,
    user_id: str = Depends(get_user_id_from_header)
):
    """Update note"""
    try:
        note = await notes_service.update_note(
            note_id=note_id,
            user_id=user_id,
            note_text=request.content
        )
        return note
    except Exception as e:
        logger.error(f"Error updating note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: int,
    user_id: str = Depends(get_user_id_from_header)
):
    """Delete note"""
    try:
        success = await notes_service.delete_note(note_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"message": "Note deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checklist/{property_id}/{user_id}")
async def get_checklist(property_id: int, user_id: str):
    """Get due diligence checklist for property"""
    try:
        checklist = await notes_service.get_checklist(property_id, user_id)
        return checklist
    except Exception as e:
        logger.error(f"Error getting checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/checklist/{property_id}/{user_id}")
async def update_checklist(
    property_id: int,
    user_id: str,
    request: ChecklistUpdateRequest
):
    """Update due diligence checklist"""
    try:
        checklist = await notes_service.update_checklist(
            property_id=property_id,
            user_id=user_id,
            checklist_items=request.checklist_items
        )
        return checklist
    except Exception as e:
        logger.error(f"Error updating checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checklist/{property_id}/{user_id}/reset")
async def reset_checklist(property_id: int, user_id: str):
    """Reset checklist to defaults"""
    try:
        checklist = await notes_service.reset_checklist(property_id, user_id)
        return checklist
    except Exception as e:
        logger.error(f"Error resetting checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checklist/{user_id}/all")
async def get_all_checklists(
    user_id: str,
    min_completion: Optional[int] = None
):
    """Get all checklists for user"""
    try:
        checklists = await notes_service.get_all_checklists(user_id, min_completion)
        return {"checklists": checklists}
    except Exception as e:
        logger.error(f"Error getting all checklists: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PUSH NOTIFICATION ROUTES
# =============================================================================

@router.post(
    "/notifications/register",
    summary="Register Device Token",
    description="Register device token for push notifications",
    tags=["Deal Intelligence (V2)"]
)
async def register_device_token(
    request: PushTokenRegisterRequest,
    user_id: str = Depends(get_user_id_from_header)
):
    """Register device token for push notifications"""
    try:
        token = await push_service.register_device_token(
            user_id=user_id,
            device_token=request.device_token,
            platform=request.platform,
            device_info=request.device_info
        )
        return token
    except Exception as e:
        logger.error(f"Error registering device token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/notifications/token/{token_id}",
    summary="Unregister Device Token",
    description="Unregister device token",
    tags=["Deal Intelligence (V2)"]
)
async def unregister_device_token(
    token_id: int,
    user_id: str = Depends(get_user_id_from_header)
):
    """Unregister device token"""
    try:
        success = await push_service.unregister_device_token(token_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Token not found")
        return {"message": "Token unregistered"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/notifications/create",
    summary="Create Push Notification",
    description="Create push notification",
    tags=["Deal Intelligence (V2)"]
)
async def create_notification(request: NotificationCreateRequest):
    """Create push notification"""
    try:
        notification = await push_service.create_notification(
            user_id=request.user_id,
            notification_type=request.notification_type,
            title=request.title,
            body=request.body,
            property_id=request.property_id,
            deep_link=request.deep_link,
            custom_data=request.custom_data,
            priority=request.priority
        )
        return notification
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/notifications/token/{token_id}/preferences",
    summary="Update Notification Preferences",
    description="Update notification preferences for device",
    tags=["Deal Intelligence (V2)"]
)
async def update_notification_preferences(
    token_id: int,
    updates: NotificationPreferencesUpdate,
    user_id: str = Depends(get_user_id_from_header)
):
    """Update notification preferences for device"""
    try:
        token = await push_service.update_notification_preferences(
            token_id=token_id,
            user_id=user_id,
            preferences=updates.model_dump(exclude_none=True)
        )
        return token
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/notifications/{user_id}/history",
    summary="Get Notification History",
    description="Get notification history for user",
    tags=["Deal Intelligence (V2)"]
)
async def get_notification_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=500)
):
    """Get notification history for user"""
    try:
        history = await push_service.get_notification_history(user_id, limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"Error getting notification history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/notifications/{notification_id}/opened",
    summary="Mark Notification Opened",
    description="Mark notification as opened",
    tags=["Deal Intelligence (V2)"]
)
async def mark_notification_opened(
    notification_id: int,
    user_id: str = Depends(get_user_id_from_header)
):
    """Mark notification as opened"""
    try:
        success = await push_service.mark_notification_opened(notification_id, user_id)
        return {"opened": success}
    except Exception as e:
        logger.error(f"Error marking notification opened: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CSV EXPORT ROUTE
# =============================================================================

@router.post("/export/csv")
async def export_csv(request: CsvExportRequest):
    """Export properties to CSV"""
    try:
        import io
        import csv
        from fastapi.responses import StreamingResponse

        # Check if feature is enabled
        enabled = await feature_service.is_feature_enabled("export_csv")
        if not enabled:
            raise HTTPException(status_code=403, detail="CSV export feature is disabled")

        # Build query
        supabase = push_service.supabase  # Reuse supabase client
        query = supabase.table("foreclosure_listings").select("*")

        if request.county_id:
            query = query.eq("county_id", request.county_id)
        if request.property_ids:
            query = query.in_("id", request.property_ids)

        result = query.execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="No properties found")

        # Default columns if not specified
        default_columns = [
            "id", "address", "city", "state", "zip_code",
            "opening_bid", "approx_upset", "sale_date",
            "bedrooms", "bathrooms", "square_feet", "year_built"
        ]
        columns = request.columns or default_columns

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()

        for prop in result.data:
            row = {col: prop.get(col, "") for col in columns}
            writer.writerow(row)

        # Stream response
        output.seek(0)
        response = StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=properties_export.csv"
            }
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HEALTH CHECK
# =============================================================================


# =============================================================================
# DEAL CRITERIA ENDPOINTS (4 endpoints)
# =============================================================================

@router.get("/criteria/{user_id}", response_model=Dict[str, Any])
async def get_deal_criteria(user_id: str):
    """
    Get user's deal criteria.

    Returns the user's saved deal criteria for property matching.
    """
    try:
        criteria = await deal_criteria_service.get_criteria(user_id)
        if not criteria:
            raise HTTPException(status_code=404, detail="Deal criteria not found")
        return criteria
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deal criteria for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/criteria", response_model=Dict[str, Any])
async def upsert_deal_criteria(request: Dict[str, Any]):
    """
    Create or update user's deal criteria.

    All fields are optional. Only provided fields will be updated.
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        criteria = await deal_criteria_service.upsert_criteria(**request)
        if not criteria:
            raise HTTPException(status_code=500, detail="Failed to save criteria")
        return criteria
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upserting deal criteria: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matches/{user_id}", response_model=Dict[str, Any])
async def get_matching_properties(
    user_id: str,
    category: Optional[str] = Query(None, description="Filter by match category: hot, warm, cold"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get properties matching user's deal criteria.

    Returns a list of properties with match scores, optionally filtered by category.
    """
    try:
        matches = await deal_criteria_service.get_matching_properties(
            user_id=user_id,
            category=category,
            limit=limit
        )

        # Get stats
        stats = await deal_criteria_service.get_match_stats(user_id)

        return {
            "user_id": user_id,
            "category_filter": category,
            "matches": matches,
            "total_count": len(matches),
            "hot_count": stats.get("hot_matches", 0),
            "warm_count": stats.get("warm_matches", 0),
            "cold_count": stats.get("cold_matches", 0)
        }
    except Exception as e:
        logger.error(f"Error getting matches for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/criteria/{user_id}/test", response_model=Dict[str, Any])
async def test_property_match(user_id: str, request: Dict[str, Any]):
    """
    Test a property against user's deal criteria.

    Returns match score and breakdown without saving the result.
    """
    try:
        property_id = request.get("property_id")
        if not property_id:
            raise HTTPException(status_code=400, detail="property_id is required")

        match = await deal_criteria_service.calculate_match_score(
            user_id=user_id,
            property_id=property_id
        )

        if not match:
            raise HTTPException(status_code=404, detail="Could not calculate match score")

        # Check if alerts are enabled
        criteria = await deal_criteria_service.get_criteria(user_id)
        would_alert = criteria.get("enable_alerts", False) if criteria else False

        return {
            **match,
            "would_alert": would_alert
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing property match: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# DATA QUALITY ENDPOINTS (2 endpoints)
# =============================================================================

@router.get("/quality/{property_id}", response_model=Dict[str, Any])
async def get_quality_score(property_id: int):
    """
    Get data quality score for a property.

    Returns comprehensive quality analysis including completeness and recommendations.
    """
    try:
        # First try to get cached score
        cached = await data_quality_service.get_quality_score(property_id)
        if cached:
            return cached

        # Calculate fresh score
        quality = await data_quality_service.calculate_quality_score(property_id)
        if not quality:
            raise HTTPException(status_code=404, detail="Property not found or could not calculate quality")

        return quality
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quality score for property {property_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quality/score", response_model=Dict[str, Any])
async def trigger_quality_scoring(request: Dict[str, Any]):
    """
    Trigger quality scoring for properties.

    Accepts a single property_id or an array of property_ids for batch processing.
    """
    try:
        property_id = request.get("property_id")
        property_ids = request.get("property_ids")

        if property_id:
            # Single property
            result = await data_quality_service.calculate_quality_score(property_id)
            if not result:
                raise HTTPException(status_code=404, detail="Property not found")
            return result

        elif property_ids:
            # Batch processing
            result = await data_quality_service.score_properties_batch(property_ids)
            return result

        else:
            raise HTTPException(status_code=400, detail="Either property_id or property_ids required")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering quality scoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# STREET VIEW ENDPOINT
# =============================================================================

@router.post("/street-view", response_model=Dict[str, Any])
async def get_street_view(request: Dict[str, Any]):
    """
    Get Google Street View images for an address.

    Returns Street View image URLs for the property from multiple angles.
    Requires GOOGLE_MAPS_API_KEY environment variable.
    """
    try:
        address = request.get("address")
        if not address:
            raise HTTPException(status_code=400, detail="address is required")

        size = request.get("size", "600x400")
        headings = request.get("headings")

        zillow_service = ZillowEnrichmentService()
        try:
            result = await zillow_service.get_street_view_images(
                address=address,
                size=size,
                headings=headings
            )
            await zillow_service.close()
        finally:
            await zillow_service.close()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Could not get Street View images. Check address or verify GOOGLE_MAPS_API_KEY is set."
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Street View: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health")
async def health_check():
    """Health check for deal intelligence endpoints"""
    return {"status": "healthy", "service": "deal-intelligence"}
