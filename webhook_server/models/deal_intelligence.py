"""
Pydantic Models for Deal Intelligence API

Request and response models for the enhanced Human-in-the-Loop Deal Intelligence system.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# =============================================================================
# COMMON MODELS
# =============================================================================

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None


# =============================================================================
# FEATURE SETTINGS MODELS
# =============================================================================

class AdminFeatureSettingsUpdate(BaseModel):
    """Update admin feature settings"""
    # Feature toggles
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

    # Lock flags
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

    # AI Quality thresholds
    anomaly_min_comps: Optional[int] = Field(None, ge=1, le=10)
    anomaly_min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    anomaly_max_zscore: Optional[float] = Field(None, ge=1.0, le=5.0)
    comps_analysis_min_samples: Optional[int] = Field(None, ge=1, le=10)
    comps_analysis_max_distance_miles: Optional[float] = Field(None, ge=0.1, le=5.0)
    comps_analysis_max_age_days: Optional[int] = Field(None, ge=30, le=1825)
    reno_min_photo_count: Optional[int] = Field(None, ge=1, le=20)
    reno_min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class AdminFeatureSettingsResponse(BaseModel):
    """Admin feature settings response"""
    features: Dict[str, bool]
    locks: Dict[str, bool]
    quality_thresholds: Dict[str, Any]


# =============================================================================
# MARKET ANOMALY MODELS
# =============================================================================

class MarketAnomaly(BaseModel):
    """Market anomaly detection result"""
    id: int
    property_id: int
    anomaly_type: str
    expected_price: Optional[float] = None
    actual_price: Optional[float] = None
    price_diff_percent: Optional[float] = None
    z_score: Optional[float] = None
    comp_count: Optional[int] = None
    comp_avg_price: Optional[float] = None
    comp_median_price: Optional[float] = None
    comp_zpids: List[int] = []
    confidence_score: Optional[float] = None
    data_quality_flags: Dict[str, Any] = {}
    detected_at: datetime
    is_verified: bool = False


class AnomalyAnalysisRequest(BaseModel):
    """Request to analyze property for anomalies"""
    user_id: Optional[str] = None
    force_reanalyze: bool = False


class AnomalyVerifyRequest(BaseModel):
    """Request to verify/correct an anomaly"""
    is_verified: bool
    verified_by_user_id: str
    correction_notes: Optional[str] = None


# =============================================================================
# COMPARABLE SALES MODELS
# =============================================================================

class ComparableProperty(BaseModel):
    """A comparable property"""
    zpid: int
    address: str
    price: float
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    distance_miles: Optional[float] = None
    days_since_sale: Optional[int] = None
    sale_date: Optional[str] = None


class CompsAnalysis(BaseModel):
    """Comparable sales analysis result"""
    id: int
    property_id: int
    selected_comp_ids: List[int]
    comp_analysis: Dict[str, Any]
    ai_summary: Optional[str] = None
    ai_adjusted_arv: Optional[float] = None
    ai_confidence: Optional[float] = None
    manual_arv_override: Optional[float] = None
    manual_notes: Optional[str] = None
    comps_meet_threshold: bool = True
    quality_flags: Dict[str, Any] = {}
    created_at: datetime


class CompsAnalysisCreate(BaseModel):
    """Create comps analysis"""
    user_id: Optional[str] = None
    selected_comp_ids: List[int]
    include_ai_analysis: bool = False


class CompsAnalysisUpdate(BaseModel):
    """Update comps analysis"""
    manual_arv_override: Optional[float] = None
    manual_notes: Optional[str] = None


# =============================================================================
# RENOVATION ESTIMATE MODELS
# =============================================================================

class PhotoAnalysis(BaseModel):
    """Analysis of a single photo"""
    room_type: str
    condition_rating: int  # 1-5
    issues: List[str] = []
    renovation_level: str  # cosmetic, moderate, major
    estimated_cost_range: List[float] = []


class RenovationEstimate(BaseModel):
    """Renovation cost estimate"""
    id: int
    property_id: int
    photo_urls: List[str] = []
    photo_analysis: List[PhotoAnalysis] = []
    estimate_total: Optional[float] = None
    estimate_breakdown: Dict[str, float] = {}
    ai_estimate_summary: Optional[str] = None
    ai_confidence: Optional[float] = None
    manual_estimate_total: Optional[float] = None
    photo_count: int = 0
    analysis_quality: str = "unknown"
    created_at: datetime


class RenovationEstimateCreate(BaseModel):
    """Create renovation estimate from photos"""
    property_id: int
    user_id: Optional[str] = None
    photo_urls: List[str]


class RenovationEstimateUpdate(BaseModel):
    """Update renovation estimate"""
    manual_estimate_total: Optional[float] = None
    manual_adjustments: Optional[Dict[str, Any]] = None


# =============================================================================
# INVESTMENT STRATEGY MODELS
# =============================================================================

class InvestmentStrategyCreate(BaseModel):
    """Create investment strategy"""
    user_id: str
    strategy_name: str
    strategy_type: str  # fix_and_flip, buy_and_hold, wholesale, brrrr, value_add
    min_fix_and_flip_profit: Optional[float] = Field(None, ge=0.0, le=1.0)  # Database column
    max_purchase_price: Optional[float] = None
    min_arv_spread: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_repair_cost: Optional[float] = None  # Database column (not max_rehab_cost)
    max_holding_months: Optional[int] = Field(None, ge=1, le=60)
    min_cash_flow: Optional[float] = None
    custom_criteria: Dict[str, Any] = {}


class InvestmentStrategyUpdate(BaseModel):
    """Update investment strategy"""
    strategy_name: Optional[str] = None
    is_active: Optional[bool] = None
    min_fix_and_flip_profit: Optional[float] = None  # Database column
    max_purchase_price: Optional[float] = None
    min_arv_spread: Optional[float] = None
    max_repair_cost: Optional[float] = None  # Database column
    max_holding_months: Optional[int] = None
    min_cash_flow: Optional[float] = None
    custom_criteria: Optional[Dict[str, Any]] = None


class InvestmentStrategy(BaseModel):
    """Investment strategy"""
    id: int
    user_id: str
    name: str  # Database column is 'name', not 'strategy_name'
    strategy_type: str
    min_fix_and_flip_profit: Optional[float] = None  # Database column
    max_purchase_price: Optional[float] = None
    min_arv_spread: Optional[float] = None
    max_repair_cost: Optional[float] = None  # Database column
    max_holding_months: Optional[int] = None
    min_cash_flow: Optional[float] = None
    custom_criteria: Dict[str, Any] = {}
    is_active: bool = True
    is_default: bool = False
    created_at: datetime
    updated_at: datetime


# =============================================================================
# WATCHLIST MODELS
# =============================================================================

class WatchlistCreate(BaseModel):
    """Add property to watchlist"""
    user_id: str
    property_id: int
    alert_on_price_change: bool = True
    alert_on_status_change: bool = True
    alert_on_new_comps: bool = False
    alert_on_auction_near: bool = False
    auction_alert_days: int = Field(7, ge=1, le=30)
    watch_notes: Optional[str] = None
    priority: str = "normal"  # low, normal, high, urgent


class WatchlistUpdate(BaseModel):
    """Update watchlist entry"""
    alert_on_price_change: Optional[bool] = None
    alert_on_status_change: Optional[bool] = None
    alert_on_new_comps: Optional[bool] = None
    alert_on_auction_near: Optional[bool] = None
    auction_alert_days: Optional[int] = None
    watch_notes: Optional[str] = None
    priority: Optional[str] = None


class UserAlert(BaseModel):
    """User alert"""
    id: int
    user_id: str
    property_id: int
    alert_type: str
    alert_title: str
    alert_message: str
    is_read: bool = False
    read_at: Optional[datetime] = None
    action_url: Optional[str] = None
    created_at: datetime


# =============================================================================
# PORTFOLIO MODELS
# =============================================================================

class PortfolioEntryCreate(BaseModel):
    """Add property to portfolio"""
    user_id: str
    property_id: int
    acquisition_date: Optional[str] = None
    purchase_price: Optional[float] = None
    rehab_cost: Optional[float] = None
    strategy_used: Optional[str] = None
    arv_target: Optional[float] = None


class PortfolioEntryUpdate(BaseModel):
    """Update portfolio entry"""
    current_value: Optional[float] = None
    actual_arv: Optional[float] = None
    portfolio_status: Optional[str] = None
    sale_date: Optional[str] = None
    sale_price: Optional[float] = None


class PortfolioEntry(BaseModel):
    """Portfolio entry"""
    id: int
    user_id: str
    property_id: int
    acquisition_date: Optional[str] = None
    purchase_price: Optional[float] = None
    rehab_cost: Optional[float] = None
    total_investment: Optional[float] = None
    strategy_used: Optional[str] = None
    current_value: Optional[float] = None
    arv_target: Optional[float] = None
    actual_arv: Optional[float] = None
    roi_percent: Optional[float] = None
    portfolio_status: str
    sale_date: Optional[str] = None
    sale_price: Optional[float] = None
    actual_roi: Optional[float] = None
    added_to_portfolio_at: datetime
    updated_at: datetime


# =============================================================================
# COLLABORATION MODELS
# =============================================================================

class SharePropertyRequest(BaseModel):
    """Share property with team member"""
    property_id: int
    shared_by_user_id: str
    shared_with_user_id: str
    share_type: str = "view"  # view, edit, comment
    share_message: Optional[str] = None


class PropertyCommentCreate(BaseModel):
    """Add comment to property"""
    property_id: int
    user_id: str
    comment_text: str
    parent_comment_id: Optional[int] = None


class PropertyCommentUpdate(BaseModel):
    """Update comment"""
    comment_text: str


class PropertyComment(BaseModel):
    """Property comment"""
    id: int
    property_id: int
    user_id: str
    comment_text: str
    parent_comment_id: Optional[int] = None
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime


# =============================================================================
# NOTES & CHECKLIST MODELS
# =============================================================================

class PropertyNoteCreate(BaseModel):
    """Create property note"""
    property_id: int
    user_id: str
    note_text: str
    note_type: str = "general"  # general, due_diligence, inspection, financial, legal


class PropertyNoteUpdate(BaseModel):
    """Update property note"""
    note_text: str


class PropertyNote(BaseModel):
    """Property note"""
    id: int
    property_id: int
    user_id: str
    note_text: str
    note_type: str
    created_at: datetime
    updated_at: datetime


class DueDiligenceChecklistUpdate(BaseModel):
    """Update due diligence checklist"""
    checklist_items: Dict[str, bool]


class DueDiligenceChecklist(BaseModel):
    """Due diligence checklist"""
    id: int
    property_id: int
    user_id: str
    checklist_items: Dict[str, bool]
    completion_percent: int
    created_at: datetime
    updated_at: datetime


# =============================================================================
# SAVED PROPERTIES & KANBAN MODELS
# =============================================================================

class SavePropertyRequest(BaseModel):
    """Save property"""
    user_id: str
    property_id: int
    folder_name: str = "default"
    tags: List[str] = []
    notes: Optional[str] = None
    kanban_stage: str = "researching"


class SavedPropertyUpdate(BaseModel):
    """Update saved property"""
    folder_name: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class KanbanStageUpdate(BaseModel):
    """Move property to kanban stage"""
    new_stage: str  # researching, analyzing, due_diligence, bidding, won, lost, archived


class SavedProperty(BaseModel):
    """Saved property"""
    id: int
    user_id: str
    property_id: int
    folder_name: str = "default"
    tags: List[str] = []
    notes: Optional[str] = None
    kanban_stage: str = "researching"
    stage_history: List[Dict[str, Any]] = []
    saved_at: datetime
    stage_updated_at: datetime


class KanbanBoard(BaseModel):
    """User's kanban board"""
    researching: List[Dict] = []
    analyzing: List[Dict] = []
    due_diligence: List[Dict] = []
    bidding: List[Dict] = []
    won: List[Dict] = []
    lost: List[Dict] = []
    archived: List[Dict] = []


# =============================================================================
# EXPORT CSV MODELS
# =============================================================================

class ExportCSVRequest(BaseModel):
    """Export properties to CSV"""
    user_id: str
    filters: Optional[Dict[str, Any]] = None
    columns: Optional[List[str]] = None
    include_enrichment_data: bool = False


class ExportCSVResponse(BaseModel):
    """Export CSV response"""
    file_url: str
    row_count: int
    filename: str


# =============================================================================
# NOTIFICATION MODELS
# =============================================================================

class PushTokenRegister(BaseModel):
    """Register push notification token"""
    user_id: str
    device_token: str
    platform: str  # ios, android, web
    device_info: Optional[Dict[str, Any]] = None
    enable_hot_deals: bool = True
    enable_auction_updates: bool = True
    enable_price_drops: bool = True
    enable_status_changes: bool = True
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None  # HH:MM format


class PushTokenUpdate(BaseModel):
    """Update push token preferences"""
    enable_hot_deals: Optional[bool] = None
    enable_auction_updates: Optional[bool] = None
    enable_price_drops: Optional[bool] = None
    enable_status_changes: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class PushNotification(BaseModel):
    """Push notification"""
    id: int
    user_id: str
    property_id: Optional[int] = None
    notification_type: str
    title: str
    body: str
    deep_link: Optional[str] = None
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime


# =============================================================================
# VALIDATION RESULT MODELS
# =============================================================================

class ValidationCheckResponse(BaseModel):
    """Single validation check result"""
    name: str
    passed: bool
    message: str
    actual_value: Optional[Any] = None
    required_value: Optional[Any] = None


class ValidationResultResponse(BaseModel):
    """Validation result"""
    is_safe_to_show: bool
    warnings: List[str] = []
    checks: List[ValidationCheckResponse] = []
    confidence_score: float = 0.0
    validation_reason: str = ""


# =============================================================================
# ML RANKING MODELS
# =============================================================================

class InvestorCriteriaCreate(BaseModel):
    """Create/update investor criteria for personalization"""
    min_upset_price: Optional[float] = Field(None, ge=0)
    max_upset_price: Optional[float] = Field(None, ge=0)
    preferred_property_types: List[str] = []
    preferred_counties: List[int] = []
    preferred_cities: List[str] = []
    exclude_areas: List[str] = []
    min_arv_percentage: Optional[float] = Field(None, ge=50, le=500)  # 50% to 500%
    max_price_per_sqft: Optional[float] = Field(None, ge=0)
    minimum_profit_margin: Optional[float] = Field(None, ge=0, le=100)  # 0% to 100%
    max_rehab_budget: Optional[float] = Field(None, ge=0)
    max_rehab_percentage: Optional[float] = Field(None, ge=0, le=100)
    ideal_days_to_auction: Optional[int] = Field(None, ge=1, le=90)
    avoid_pending_litigation: bool = False
    investment_strategy: Optional[str] = None
    custom_weights: Dict[str, Any] = {}


class InvestorCriteriaResponse(BaseModel):
    """Investor criteria response"""
    id: int
    user_id: str
    min_upset_price: Optional[float] = None
    max_upset_price: Optional[float] = None
    preferred_property_types: List[str] = []
    preferred_counties: List[int] = []
    preferred_cities: List[str] = []
    exclude_areas: List[str] = []
    min_arv_percentage: Optional[float] = None
    max_price_per_sqft: Optional[float] = None
    minimum_profit_margin: Optional[float] = None
    max_rehab_budget: Optional[float] = None
    max_rehab_percentage: Optional[float] = None
    ideal_days_to_auction: Optional[int] = None
    avoid_pending_litigation: bool = False
    investment_strategy: Optional[str] = None
    custom_weights: Dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class FeatureScoreBreakdown(BaseModel):
    """Individual feature score with confidence"""
    score: float
    confidence: float


class PropertyRankingResult(BaseModel):
    """Property ranking result"""
    property_id: int
    score: float
    confidence: float
    data_quality: str  # high, medium, low, incomplete
    breakdown: Dict[str, FeatureScoreBreakdown] = {}
    missing_features: List[str] = []
    calculated_at: datetime
    # Optional property details
    property: Optional[Dict[str, Any]] = None


class RankingRequest(BaseModel):
    """Request to rank properties for a user"""
    user_id: str
    property_ids: Optional[List[int]] = None
    limit: int = Field(100, ge=1, le=500)
    filters: Optional[Dict[str, Any]] = None


class RankingFeedbackRequest(BaseModel):
    """Submit ranking feedback for learning"""
    user_id: str
    property_id: int
    is_positive: bool
    feedback_type: str  # viewed_property, saved_property, hid_property, etc.
    ranking_position: Optional[int] = None
    user_action: Optional[str] = None


class ModelWeightsResponse(BaseModel):
    """Model weights response"""
    id: int
    model_version: str
    is_active: bool
    weights: Dict[str, float]
    scoring_parameters: Dict[str, Any] = {}
    trained_at: Optional[datetime] = None
    training_samples_count: int = 0
    accuracy_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# PUSH NOTIFICATION MODELS (EXPANDED)
# =============================================================================

class PushNotificationCreate(BaseModel):
    """Create a push notification"""
    user_id: str
    notification_type: str
    title: str
    body: str
    property_id: Optional[int] = None
    deep_link: Optional[str] = None
    custom_data: Dict[str, Any] = {}
    priority: str = "normal"  # low, normal, high, urgent
    scheduled_for: Optional[str] = None  # ISO datetime


class PushNotificationCreateFromTemplate(BaseModel):
    """Create notification from template"""
    user_id: str
    template_key: str  # e.g., 'hot_deal_alert', 'price_drop_alert'
    variables: Dict[str, str]  # Template variable substitutions
    property_id: Optional[int] = None
    priority: str = "normal"
    scheduled_for: Optional[str] = None


class PushNotificationResponse(BaseModel):
    """Push notification response"""
    id: int
    user_id: str
    property_id: Optional[int] = None
    notification_type: str
    title: str
    body: str
    deep_link: Optional[str] = None
    custom_data: Dict[str, Any] = {}
    priority: str
    status: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    error_message: Optional[str] = None
    scheduled_for: datetime
    created_at: datetime


class PushNotificationBatchCreate(BaseModel):
    """Create notifications for multiple users"""
    user_ids: List[str]
    notification_type: str
    title: str
    body: str
    property_id: Optional[int] = None
    deep_link: Optional[str] = None
    priority: str = "normal"


class PushNotificationHistoryResponse(BaseModel):
    """Push notification history entry"""
    id: int
    user_id: str
    property_id: Optional[int] = None
    notification_type: str
    title: str
    body: str
    status: str
    platform: Optional[str] = None
    device_count: Optional[int] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    time_to_open_seconds: Optional[int] = None
    error_summary: Optional[str] = None
    created_at: datetime


class PushTemplateResponse(BaseModel):
    """Push notification template"""
    id: int
    template_key: str
    name: str
    notification_type: str
    title_template: str
    body_template: str
    variables: Dict[str, Any] = {}
    default_priority: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NotificationOpenedRequest(BaseModel):
    """Mark notification as opened"""
    notification_id: int
    user_id: str


# =============================================================================
# DEAL CRITERIA MODELS
# =============================================================================

class DealCriteriaCreate(BaseModel):
    """Create or update deal criteria"""
    user_id: str
    min_upset_price: Optional[float] = Field(None, ge=0)
    max_upset_price: Optional[float] = Field(None, ge=0)
    min_arv_percentage: Optional[float] = Field(70.0, ge=0, le=500)
    minimum_profit_margin: Optional[float] = Field(30.0, ge=0, le=100)
    max_rehab_budget: Optional[float] = Field(None, ge=0)
    max_rehab_percentage: Optional[float] = Field(30.0, ge=0, le=100)
    preferred_property_types: Optional[List[str]] = None
    preferred_counties: Optional[List[int]] = None
    preferred_cities: Optional[List[str]] = None
    exclude_areas: Optional[List[str]] = None
    ideal_days_to_auction: Optional[int] = Field(7, ge=1, le=90)
    avoid_pending_litigation: Optional[bool] = True
    min_data_quality_score: Optional[float] = Field(0.5, ge=0, le=1)
    investment_strategy: Optional[str] = None
    custom_weights: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = True
    enable_alerts: Optional[bool] = True


class DealCriteriaUpdate(BaseModel):
    """Update deal criteria"""
    min_upset_price: Optional[float] = None
    max_upset_price: Optional[float] = None
    min_arv_percentage: Optional[float] = None
    minimum_profit_margin: Optional[float] = None
    max_rehab_budget: Optional[float] = None
    max_rehab_percentage: Optional[float] = None
    preferred_property_types: Optional[List[str]] = None
    preferred_counties: Optional[List[int]] = None
    preferred_cities: Optional[List[str]] = None
    exclude_areas: Optional[List[str]] = None
    ideal_days_to_auction: Optional[int] = None
    avoid_pending_litigation: Optional[bool] = None
    min_data_quality_score: Optional[float] = None
    investment_strategy: Optional[str] = None
    custom_weights: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    enable_alerts: Optional[bool] = None


class DealCriteriaResponse(BaseModel):
    """Deal criteria response"""
    id: int
    user_id: str
    min_upset_price: Optional[float] = None
    max_upset_price: Optional[float] = None
    min_arv_percentage: Optional[float] = None
    minimum_profit_margin: Optional[float] = None
    max_rehab_budget: Optional[float] = None
    max_rehab_percentage: Optional[float] = None
    preferred_property_types: List[str] = []
    preferred_counties: List[int] = []
    preferred_cities: List[str] = []
    exclude_areas: List[str] = []
    ideal_days_to_auction: Optional[int] = None
    avoid_pending_litigation: bool = True
    min_data_quality_score: Optional[float] = None
    investment_strategy: Optional[str] = None
    custom_weights: Dict[str, Any] = {}
    is_active: bool = True
    enable_alerts: bool = True
    created_at: datetime
    updated_at: datetime


class PropertyMatchScore(BaseModel):
    """Property match score"""
    id: int
    user_id: str
    property_id: int
    match_score: float
    match_category: str  # hot, warm, cold
    score_breakdown: Dict[str, Any] = {}
    match_reasons: List[str] = []
    disqualification_reasons: List[str] = []
    property_snapshot: Dict[str, Any] = {}
    calculated_at: datetime


class GetMatchesRequest(BaseModel):
    """Request to get matching properties"""
    user_id: str
    category: Optional[str] = None  # hot, warm, cold
    limit: int = Field(50, ge=1, le=200)


class GetMatchesResponse(BaseModel):
    """Response with matching properties"""
    user_id: str
    category_filter: Optional[str] = None
    matches: List[PropertyMatchScore] = []
    total_count: int
    hot_count: int
    warm_count: int
    cold_count: int


class TestPropertyMatchRequest(BaseModel):
    """Test a property against user's criteria"""
    user_id: str
    property_id: int


class PropertyMatchTestResponse(BaseModel):
    """Response from property match test"""
    user_id: str
    property_id: int
    match_score: float
    match_category: str
    score_breakdown: Dict[str, Any]
    match_reasons: List[str]
    disqualification_reasons: List[str]
    would_alert: bool
    calculated_at: datetime


# =============================================================================
# DATA QUALITY MODELS
# =============================================================================

class DataQualityScoreResponse(BaseModel):
    """Data quality score response"""
    property_id: int
    calculated_at: datetime
    score_breakdown: Dict[str, Any]
    overall_quality_score: float
    quality_tier: str  # high, medium, low
    is_safe_to_show: bool
    missing_fields: Dict[str, List[str]]
    recommendations: List[str]
    data_completeness: Dict[str, Any]


class QualityCheckRequest(BaseModel):
    """Request to check property quality"""
    property_id: int


class QualityValidationResponse(BaseModel):
    """Quality validation response"""
    is_safe_to_show: bool
    overall_score: Optional[float] = None
    quality_tier: Optional[str] = None
    checks: List[Dict[str, Any]] = []
    warnings: List[str] = []


class BatchQualityScoreRequest(BaseModel):
    """Request to batch score properties"""
    property_ids: List[int]


class BatchQualityScoreResponse(BaseModel):
    """Response from batch quality scoring"""
    total_processed: int
    high_quality: int
    medium_quality: int
    low_quality: int
    errors: int
    results: List[Dict[str, Any]]


# =============================================================================
# STREET VIEW MODELS
# =============================================================================

class StreetViewImage(BaseModel):
    """Single Street View image"""
    url: str
    heading: int
    label: str


class StreetViewResponse(BaseModel):
    """Street View response"""
    images: List[StreetViewImage]
    coordinates: Dict[str, float]
    address: str
    metadata_url: Optional[str] = None


class StreetViewRequest(BaseModel):
    """Request to get Street View images"""
    address: str
    size: str = "600x400"
    headings: Optional[List[int]] = None
