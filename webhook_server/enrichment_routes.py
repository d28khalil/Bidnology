"""
Zillow Enrichment API Routes

REST API endpoints for Zillow property enrichment with three-tier settings system.

**Architecture:**
- Settings Resolution: Admin (Global) → County (Per-County) → User (Per-User)
- Lock flags prevent overrides at lower levels
- Template presets for quick configuration
- 13 Zillow endpoints with configurable enable/disable

**Endpoints:**
1. Settings Management (Admin, County, User)
2. Template Management
3. Property Enrichment (with settings resolution)
4. Skip Tracing
5. Deal Intelligence (future)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
import os
from dotenv import load_dotenv

from .zillow_enrichment import ZillowEnrichmentService
from .settings_service import SettingsService, ResolvedSettings
from .skip_trace_service import SkipTraceService
from .tracerfy_service import TracerfyService

load_dotenv()

router = APIRouter(
    prefix="/api/enrichment",
    tags=["Enrichment (V1)"],  # Default to V1, V2 endpoints override with tags=["Enrichment (V2)"]
    responses={
        401: {"description": "Unauthorized - Invalid or missing credentials"},
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)

# Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)


# ============================================
# Request/Response Models
# ============================================

class EnrichmentResponse(BaseModel):
    """Response for enrichment requests."""
    property_id: int
    success: bool
    status: str
    message: str
    zpid: Optional[int] = None
    error: Optional[str] = None
    requests_used: int = 0
    endpoints_called: List[str] = []


class EnrichmentStatusResponse(BaseModel):
    """Response for enrichment statistics."""
    total: int
    pending: int
    auto_enriched: int
    fully_enriched: int
    failed: int


class PropertyListResponse(BaseModel):
    """Response for property list queries."""
    count: int
    properties: List[Dict[str, Any]]


# Settings Models
class AdminSettingsUpdate(BaseModel):
    """Update admin settings."""
    # Endpoint overrides
    endpoint_pro_byaddress: Optional[bool] = None
    endpoint_custom_ad_byzpid: Optional[bool] = None
    endpoint_similar: Optional[bool] = None
    endpoint_nearby: Optional[bool] = None
    endpoint_pricehistory: Optional[bool] = None
    endpoint_graph_listing_price: Optional[bool] = None
    endpoint_taxinfo: Optional[bool] = None
    endpoint_climate: Optional[bool] = None
    endpoint_walk_transit_bike: Optional[bool] = None
    endpoint_housing_market: Optional[bool] = None
    endpoint_rental_market: Optional[bool] = None
    endpoint_ownerinfo: Optional[bool] = None
    endpoint_custom_ae_searchbyaddress: Optional[bool] = None

    # Lock flags
    endpoint_lock_pro_byaddress: Optional[bool] = None
    endpoint_lock_custom_ad_byzpid: Optional[bool] = None
    endpoint_lock_similar: Optional[bool] = None
    endpoint_lock_nearby: Optional[bool] = None
    endpoint_lock_pricehistory: Optional[bool] = None
    endpoint_lock_graph_listing_price: Optional[bool] = None
    endpoint_lock_taxinfo: Optional[bool] = None
    endpoint_lock_climate: Optional[bool] = None
    endpoint_lock_walk_transit_bike: Optional[bool] = None
    endpoint_lock_housing_market: Optional[bool] = None
    endpoint_lock_rental_market: Optional[bool] = None
    endpoint_lock_ownerinfo: Optional[bool] = None
    endpoint_lock_custom_ae_searchbyaddress: Optional[bool] = None

    # Investment parameters
    inv_annual_appreciation: Optional[float] = None
    inv_mortgage_rate: Optional[float] = None
    inv_down_payment_rate: Optional[float] = None
    inv_loan_term_months: Optional[int] = None
    inv_insurance_rate: Optional[float] = None
    inv_property_tax_rate: Optional[float] = None
    inv_maintenance_rate: Optional[float] = None
    inv_property_mgmt_rate: Optional[float] = None
    inv_vacancy_rate: Optional[float] = None
    inv_closing_costs_rate: Optional[float] = None
    inv_target_profit_margin: Optional[float] = None
    inv_renovation_cost_default: Optional[float] = None

    # Permissions
    allow_user_overrides: Optional[bool] = None
    allow_user_templates: Optional[bool] = None
    allow_custom_investment_params: Optional[bool] = None


class CountySettingsCreate(BaseModel):
    """Create county settings."""
    county_id: int
    county_name: str
    state: str
    template_preset: Optional[str] = None

    # Endpoint overrides (null = use admin default)
    endpoint_pro_byaddress: Optional[bool] = None
    endpoint_custom_ad_byzpid: Optional[bool] = None
    endpoint_similar: Optional[bool] = None
    endpoint_nearby: Optional[bool] = None
    endpoint_pricehistory: Optional[bool] = None
    endpoint_graph_listing_price: Optional[bool] = None
    endpoint_taxinfo: Optional[bool] = None
    endpoint_climate: Optional[bool] = None
    endpoint_walk_transit_bike: Optional[bool] = None
    endpoint_housing_market: Optional[bool] = None
    endpoint_rental_market: Optional[bool] = None
    endpoint_ownerinfo: Optional[bool] = None
    endpoint_custom_ae_searchbyaddress: Optional[bool] = None


class CountySettingsUpdate(BaseModel):
    """Update county settings."""
    template_preset: Optional[str] = None

    # Endpoint overrides
    endpoint_pro_byaddress: Optional[bool] = None
    endpoint_custom_ad_byzpid: Optional[bool] = None
    endpoint_similar: Optional[bool] = None
    endpoint_nearby: Optional[bool] = None
    endpoint_pricehistory: Optional[bool] = None
    endpoint_graph_listing_price: Optional[bool] = None
    endpoint_taxinfo: Optional[bool] = None
    endpoint_climate: Optional[bool] = None
    endpoint_walk_transit_bike: Optional[bool] = None
    endpoint_housing_market: Optional[bool] = None
    endpoint_rental_market: Optional[bool] = None
    endpoint_ownerinfo: Optional[bool] = None
    endpoint_custom_ae_searchbyaddress: Optional[bool] = None

    # Investment parameter overrides
    inv_annual_appreciation: Optional[float] = None
    inv_mortgage_rate: Optional[float] = None
    inv_down_payment_rate: Optional[float] = None
    inv_loan_term_months: Optional[int] = None
    inv_insurance_rate: Optional[float] = None
    inv_property_tax_rate: Optional[float] = None
    inv_maintenance_rate: Optional[float] = None
    inv_property_mgmt_rate: Optional[float] = None
    inv_vacancy_rate: Optional[float] = None


class UserPreferencesCreate(BaseModel):
    """Create user preferences."""
    user_id: str
    county_id: int
    state: str
    template_preset: Optional[str] = None

    # Endpoint overrides
    endpoint_pro_byaddress: Optional[bool] = None
    endpoint_custom_ad_byzpid: Optional[bool] = None
    endpoint_similar: Optional[bool] = None
    endpoint_nearby: Optional[bool] = None
    endpoint_pricehistory: Optional[bool] = None
    endpoint_graph_listing_price: Optional[bool] = None
    endpoint_taxinfo: Optional[bool] = None
    endpoint_climate: Optional[bool] = None
    endpoint_walk_transit_bike: Optional[bool] = None
    endpoint_housing_market: Optional[bool] = None
    endpoint_rental_market: Optional[bool] = None
    endpoint_ownerinfo: Optional[bool] = None
    endpoint_custom_ae_searchbyaddress: Optional[bool] = None

    # Investment parameter overrides
    inv_annual_appreciation: Optional[float] = None
    inv_mortgage_rate: Optional[float] = None
    inv_down_payment_rate: Optional[float] = None
    inv_loan_term_months: Optional[int] = None
    inv_insurance_rate: Optional[float] = None
    inv_property_tax_rate: Optional[float] = None
    inv_maintenance_rate: Optional[float] = None
    inv_property_mgmt_rate: Optional[float] = None
    inv_vacancy_rate: Optional[float] = None


class UserPreferencesUpdate(BaseModel):
    """Update user preferences."""
    template_preset: Optional[str] = None

    # Endpoint overrides
    endpoint_pro_byaddress: Optional[bool] = None
    endpoint_custom_ad_byzpid: Optional[bool] = None
    endpoint_similar: Optional[bool] = None
    endpoint_nearby: Optional[bool] = None
    endpoint_pricehistory: Optional[bool] = None
    endpoint_graph_listing_price: Optional[bool] = None
    endpoint_taxinfo: Optional[bool] = None
    endpoint_climate: Optional[bool] = None
    endpoint_walk_transit_bike: Optional[bool] = None
    endpoint_housing_market: Optional[bool] = None
    endpoint_rental_market: Optional[bool] = None
    endpoint_ownerinfo: Optional[bool] = None
    endpoint_custom_ae_searchbyaddress: Optional[bool] = None

    # Investment parameter overrides
    inv_annual_appreciation: Optional[float] = None
    inv_mortgage_rate: Optional[float] = None
    inv_down_payment_rate: Optional[float] = None
    inv_loan_term_months: Optional[int] = None
    inv_insurance_rate: Optional[float] = None
    inv_property_tax_rate: Optional[float] = None
    inv_maintenance_rate: Optional[float] = None
    inv_property_mgmt_rate: Optional[float] = None
    inv_vacancy_rate: Optional[float] = None


class TemplateApplyRequest(BaseModel):
    """Apply template preset to settings level."""
    level: str = Field(..., description="county or user")
    level_id: Any = Field(..., description="county_id (int) or user_id (str)")
    template: str = Field(..., description="Template name: minimal, standard, flipper, landlord, thorough")
    state: Optional[str] = None
    county_id: Optional[int] = None


class EnrichPropertyRequest(BaseModel):
    """Enrich a property with settings."""
    user_id: Optional[str] = None
    endpoints: Optional[List[str]] = None  # Optional list of endpoints to call


class SkipTraceRequest(BaseModel):
    """Skip trace a property."""
    skip_if_exists: bool = True


class BulkSkipTraceRequest(BaseModel):
    """Bulk skip trace enriched properties."""
    limit: int = 100
    skip_if_exists: bool = True


# ============================================
# ADMIN SETTINGS ENDPOINTS
# ============================================

@router.get(
    "/settings/admin",
    summary="Get Admin Settings",
    description="Get global admin settings (singleton row with id=1)"
)
async def get_admin_settings():
    """Get admin settings."""
    try:
        service = SettingsService()
        settings = await service.get_admin_settings()
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/settings/admin",
    summary="Update Admin Settings",
    description="Update global admin settings. Lock flags prevent lower-level overrides."
)
async def update_admin_settings(updates: AdminSettingsUpdate):
    """Update admin settings."""
    try:
        service = SettingsService()

        # Build update dict with only non-null values
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = await service.update_admin_settings(update_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# COUNTY SETTINGS ENDPOINTS
# ============================================

@router.get(
    "/settings/county",
    summary="List All County Settings",
    description="Get all county-level enrichment settings",
    tags=["Enrichment (V2)"]
)
async def list_county_settings():
    """List all county settings."""
    try:
        service = SettingsService()
        settings = await service.list_all_county_settings()
        return {"count": len(settings), "settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/settings/county/{county_id}/{state}",
    summary="Get County Settings",
    description="Get settings for a specific county",
    tags=["Enrichment (V2)"]
)
async def get_county_settings(county_id: int, state: str):
    """Get county settings."""
    try:
        service = SettingsService()
        settings = await service.get_county_settings(county_id, state)

        if not settings:
            raise HTTPException(
                status_code=404,
                detail=f"County settings not found for {county_id}, {state}"
            )

        return settings
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/settings/county",
    summary="Create County Settings",
    description="Create enrichment settings for a county",
    tags=["Enrichment (V2)"]
)
async def create_county_settings(settings: CountySettingsCreate):
    """Create county settings."""
    try:
        service = SettingsService()

        # Extract settings fields
        settings_dict = settings.model_dump(exclude={"county_id", "county_name", "state"})
        settings_dict = {k: v for k, v in settings_dict.items() if v is not None}

        result = await service.create_county_settings(
            county_id=settings.county_id,
            county_name=settings.county_name,
            state=settings.state,
            settings=settings_dict
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/settings/county/{county_id}/{state}",
    summary="Update County Settings",
    description="Update settings for a specific county",
    tags=["Enrichment (V2)"]
)
async def update_county_settings(county_id: int, state: str, updates: CountySettingsUpdate):
    """Update county settings."""
    try:
        service = SettingsService()

        # Build update dict with only non-null values
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = await service.update_county_settings(county_id, state, update_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/settings/county/{county_id}/{state}",
    summary="Delete County Settings",
    description="Delete county settings (revert to admin defaults)",
    tags=["Enrichment (V2)"]
)
async def delete_county_settings(county_id: int, state: str):
    """Delete county settings."""
    try:
        service = SettingsService()
        await service.delete_county_settings(county_id, state)
        return {"message": "County settings deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# USER PREFERENCES ENDPOINTS
# ============================================

@router.get(
    "/settings/user/{user_id}",
    summary="List User Preferences",
    description="Get all enrichment preferences for a user"
)
async def list_user_preferences(user_id: str):
    """List user preferences."""
    try:
        service = SettingsService()
        prefs = await service.list_user_preferences(user_id)
        return {"count": len(prefs), "preferences": prefs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/settings/user/{user_id}/{county_id}/{state}",
    summary="Get User Preferences",
    description="Get user preferences for a specific county"
)
async def get_user_preferences(user_id: str, county_id: int, state: str):
    """Get user preferences."""
    try:
        service = SettingsService()
        prefs = await service.get_user_preferences(user_id, county_id, state)

        if not prefs:
            raise HTTPException(
                status_code=404,
                detail=f"User preferences not found for {user_id}, {county_id}, {state}"
            )

        return prefs
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/settings/user",
    summary="Create User Preferences",
    description="Create enrichment preferences for a user in a county"
)
async def create_user_preferences(prefs: UserPreferencesCreate):
    """Create user preferences."""
    try:
        service = SettingsService()

        # Extract preferences fields
        prefs_dict = prefs.model_dump(exclude={"user_id", "county_id", "state"})
        prefs_dict = {k: v for k, v in prefs_dict.items() if v is not None}

        result = await service.create_user_preferences(
            user_id=prefs.user_id,
            county_id=prefs.county_id,
            state=prefs.state,
            preferences=prefs_dict
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/settings/user/{user_id}/{county_id}/{state}",
    summary="Update User Preferences",
    description="Update user preferences for a specific county"
)
async def update_user_preferences(
    user_id: str,
    county_id: int,
    state: str,
    updates: UserPreferencesUpdate
):
    """Update user preferences."""
    try:
        service = SettingsService()

        # Build update dict with only non-null values
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = await service.update_user_preferences(user_id, county_id, state, update_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/settings/user/{user_id}/{county_id}/{state}",
    summary="Delete User Preferences",
    description="Delete user preferences (revert to county/admin defaults)"
)
async def delete_user_preferences(user_id: str, county_id: int, state: str):
    """Delete user preferences."""
    try:
        service = SettingsService()
        await service.delete_user_preferences(user_id, county_id, state)
        return {"message": "User preferences deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SETTINGS RESOLUTION
# ============================================

@router.get(
    "/settings/resolve/{county_id}/{state}",
    summary="Resolve Settings",
    description="Resolve settings for a county with priority: User > County > Admin"
)
async def resolve_settings(
    county_id: int,
    state: str,
    user_id: Optional[str] = None
):
    """Resolve settings."""
    try:
        service = SettingsService()
        resolved = await service.resolve_settings(county_id, state, user_id)
        return {
            "endpoints": resolved.endpoints,
            "investment_params": resolved.investment_params,
            "permissions": resolved.permissions,
            "template_preset": resolved.template_preset,
            "sources": resolved.sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TEMPLATE MANAGEMENT
# ============================================

@router.get(
    "/templates",
    summary="List Templates",
    description="List available template presets"
)
async def list_templates():
    """List template presets."""
    try:
        service = SettingsService()
        templates = service.list_templates()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/templates/{template_name}",
    summary="Get Template",
    description="Get template preset configuration"
)
async def get_template(template_name: str):
    """Get template preset."""
    try:
        service = SettingsService()
        template = service.get_template(template_name)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")

        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/templates/apply",
    summary="Apply Template",
    description="Apply a template preset to county or user settings"
)
async def apply_template(request: TemplateApplyRequest):
    """Apply template preset."""
    try:
        service = SettingsService()
        result = await service.apply_template(
            level=request.level,
            level_id=request.level_id,
            template=request.template,
            state=request.state,
            county_id=request.county_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENRICHMENT STATUS
# ============================================

@router.get(
    "/status",
    response_model=EnrichmentStatusResponse,
    summary="Get Enrichment Statistics"
)
async def get_enrichment_status():
    """Get enrichment statistics."""
    try:
        result = supabase.table('foreclosure_listings').select(
            'zillow_enrichment_status'
        ).execute()

        properties = result.data
        stats = {
            "total": len(properties),
            "pending": 0,
            "auto_enriched": 0,
            "fully_enriched": 0,
            "failed": 0
        }

        for prop in properties:
            status = prop.get('zillow_enrichment_status', 'pending')
            if status in stats:
                stats[status] += 1

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PROPERTIES LIST (V1 - Foreclosure Listings)
# ============================================

@router.get(
    "/properties",
    response_model=PropertyListResponse,
    summary="List Foreclosure Properties",
    description="Get paginated list of foreclosure listings with optional filters. Organized for investor decision-making."
)
async def list_properties(
    county_id: Optional[int] = Query(None, description="Filter by county ID"),
    state: Optional[str] = Query(None, description="Filter by state abbreviation (e.g., 'NJ')"),
    city: Optional[str] = Query(None, description="Filter by city"),
    property_status: Optional[str] = Query(None, description="Filter by property status"),
    min_upset_price: Optional[float] = Query(None, description="Minimum upset price"),
    max_upset_price: Optional[float] = Query(None, description="Maximum upset price"),
    limit: int = Query(50, ge=1, description="Number of results per page (no upper limit)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    search: Optional[str] = Query(None, description="Search in address or city"),
    order_by: str = Query("sale_date", description="Field to order by"),
    order: str = Query("asc", description="Order direction (asc or desc)"),
    property_ids: Optional[str] = Query(None, description="Comma-separated property IDs to filter"),
    enrichment_status: Optional[str] = Query(None, description="Filter by enrichment status (fully_enriched, auto_enriched, etc.)")
):
    """
    Get foreclosure listings for investors.

    Data organized by priority:
    1. PROPERTY IDENTIFICATION - Address, location
    2. AUCTION DETAILS - Date, time, court, status
    3. FINANCIALS - Opening bid, judgment amount, upset price
    4. PROPERTY SPECS - Beds, baths, sqft, year built
    5. VALUATION - Zestimate/ARV for calculating spread
    6. ENRICHMENT STATUS - Data quality indicator

    Supports filtering by county, state, city, status, price range, and search.
    """
    try:
        # Columns organized for investor decision-making
        # Note: Cannot use SQL comments (--) in Supabase select strings
        columns = """
            id,
            property_id,
            sheriff_number,
            case_number,
            property_address,
            city,
            state,
            zip_code,
            county_name,
            sale_date,
            sale_time,
            court_name,
            property_status,
            status_detail,
            opening_bid,
            approx_upset,
            judgment_amount,
            minimum_bid,
            sale_price,
            plaintiff,
            plaintiff_attorney,
            defendant,
            property_type,
            lot_size,
            filing_date,
            judgment_date,
            writ_date,
            sale_terms,
            attorney_notes,
            general_notes,
            description,
            details_url,
            data_source_url,
            zillow_zpid,
            zillow_enrichment_status,
            zillow_enriched_at,
            zillow_enrichment!left(
                zpid,
                zestimate,
                zestimate_low,
                zestimate_high,
                bedrooms,
                bathrooms,
                sqft,
                year_built,
                lot_size,
                property_type,
                last_sold_date,
                last_sold_price,
                images,
                tax_assessment,
                tax_assessment_year,
                tax_billed,
                walk_score,
                transit_score,
                bike_score,
                tax_history,
                price_history,
                zestimate_history,
                climate_risk,
                comps,
                similar_properties,
                nearby_properties
            ),
            created_at,
            updated_at
        """

        query = supabase.table('foreclosure_listings').select(columns, count='exact')

        # Apply filters
        if county_id is not None:
            query = query.eq('county_id', county_id)
        if state:
            query = query.eq('state', state.upper())
        if city:
            query = query.eq('city', city)
        if property_status:
            query = query.eq('property_status', property_status)
        if min_upset_price is not None:
            query = query.gte('approx_upset', min_upset_price)
        if max_upset_price is not None:
            query = query.lte('approx_upset', max_upset_price)
        if search:
            query = query.or_(f"property_address.ilike.%{search}%,city.ilike.%{search}%")
        # Filter by specific property IDs (comma-separated)
        if property_ids:
            id_list = [int(id.strip()) for id in property_ids.split(',') if id.strip().isdigit()]
            if id_list:
                query = query.in_('id', id_list)
        # Filter by enrichment status
        if enrichment_status:
            query = query.eq('zillow_enrichment_status', enrichment_status)

        # Apply ordering
        order_direction = "desc" if order.lower() == "desc" else "asc"
        query = query.order(order_by, desc=(order_direction == "desc"))

        # Get total count first
        count_query = supabase.table('foreclosure_listings').select('id', count='exact')
        if county_id is not None:
            count_query = count_query.eq('county_id', county_id)
        if state:
            count_query = count_query.eq('state', state.upper())
        if city:
            count_query = count_query.eq('city', city)
        if property_status:
            count_query = count_query.eq('property_status', property_status)
        if min_upset_price is not None:
            count_query = count_query.gte('approx_upset', min_upset_price)
        if max_upset_price is not None:
            count_query = count_query.lte('approx_upset', max_upset_price)
        if search:
            count_query = count_query.or_(f"property_address.ilike.%{search}%,city.ilike.%{search}%")
        if property_ids:
            id_list = [int(id.strip()) for id in property_ids.split(',') if id.strip().isdigit()]
            if id_list:
                count_query = count_query.in_('id', id_list)
        if enrichment_status:
            count_query = count_query.eq('zillow_enrichment_status', enrichment_status)

        count_result = count_query.execute()
        total_count = count_result.count if hasattr(count_result, 'count') else 0

        # Supabase has a 1000 row limit per query, so fetch in batches if needed
        all_data = []
        remaining = limit
        current_offset = offset
        batch_size = 1000

        while remaining > 0 and current_offset < total_count:
            current_batch_size = min(batch_size, remaining, total_count - current_offset)

            # Build a fresh query for each batch
            batch_query = supabase.table('foreclosure_listings').select(columns)
            if county_id is not None:
                batch_query = batch_query.eq('county_id', county_id)
            if state:
                batch_query = batch_query.eq('state', state.upper())
            if city:
                batch_query = batch_query.eq('city', city)
            if property_status:
                batch_query = batch_query.eq('property_status', property_status)
            if min_upset_price is not None:
                batch_query = batch_query.gte('approx_upset', min_upset_price)
            if max_upset_price is not None:
                batch_query = batch_query.lte('approx_upset', max_upset_price)
            if search:
                batch_query = batch_query.or_(f"property_address.ilike.%{search}%,city.ilike.%{search}%")
            if property_ids:
                id_list = [int(id.strip()) for id in property_ids.split(',') if id.strip().isdigit()]
                if id_list:
                    batch_query = batch_query.in_('id', id_list)
            if enrichment_status:
                batch_query = batch_query.eq('zillow_enrichment_status', enrichment_status)

            batch_query = batch_query.order(order_by, desc=(order_direction == "desc"))
            batch_query = batch_query.range(current_offset, current_offset + current_batch_size - 1)
            batch_result = batch_query.execute()

            if batch_result.data:
                all_data.extend(batch_result.data)
                remaining -= len(batch_result.data)
                current_offset += len(batch_result.data)

                # If we got fewer results than requested, we've reached the end
                if len(batch_result.data) < current_batch_size:
                    break
            else:
                break

        return {
            "count": total_count,
            "properties": all_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching properties: {str(e)}")


# ============================================
# PROPERTY ENRICHMENT
# ============================================

async def enrich_property_with_settings(
    property_id: int,
    county_id: int,
    state: str,
    user_id: Optional[str] = None,
    endpoints: Optional[List[str]] = None
):
    """Background task to enrich property with settings."""
    service = ZillowEnrichmentService()
    try:
        # Get property address
        prop_result = supabase.table('foreclosure_listings').select(
            'property_address', 'city', 'zip_code'
        ).eq('id', property_id).execute()

        if not prop_result.data:
            print(f"Property {property_id} not found")
            return

        prop = prop_result.data[0]
        address = prop['property_address']

        # Convert endpoints list to enabled_endpoints dict format
        enabled_endpoints = None
        if endpoints:
            # Map endpoint names from request to the format expected by enrich_with_settings
            endpoint_mapping = {
                "basic_info": "pro_byaddress",
                "similar": "similar",
                "nearby": "nearby",
                "price_history": "pricehistory",
                "tax_info": "taxinfo",
                "climate": "climate",
                "walk_scores": "walk_transit_bike",
                "owner_info": "ownerinfo",
            }
            enabled_endpoints = {endpoint_mapping.get(e, e): True for e in endpoints}

        # Enrich with settings
        result = await service.enrich_with_settings(
            property_id=property_id,
            address=address,
            county_id=county_id,
            state=state,
            user_id=user_id,
            enabled_endpoints=enabled_endpoints  # Pass the endpoints as dict
        )

        if not result.get('success'):
            print(f"Failed to enrich property {property_id}: {result.get('error')}")
            # Update foreclosure_listings with failed status
            supabase.table('foreclosure_listings').update({
                'zillow_enrichment_status': 'failed',
                'zillow_enriched_at': 'NOW()'
            }).eq('id', property_id).execute()
            return

        # Save enrichment data to zillow_enrichment table
        enrichment_data = result.get('enrichment_data', {})
        endpoints_called = result.get('endpoints_called', [])
        endpoints_attempted = result.get('endpoints_attempted', [])
        endpoints_succeeded = result.get('endpoints_succeeded', [])
        endpoint_errors = result.get('endpoint_errors', {})

        # Determine enrichment status based on endpoints called
        # Allowed values: pending, auto_enriched, fully_enriched, failed
        if len(endpoints_called) >= 4:
            enrichment_status = 'fully_enriched'
        else:
            enrichment_status = 'auto_enriched'

        # Determine enrichment mode (allowed values: 'auto' or 'full')
        enrichment_mode = 'auto'  # Default to auto for all enrichments

        # Build zillow_enrichment record
        zillow_record = {
            'property_id': property_id,
            'zpid': enrichment_data.get('zpid'),
            'enrichment_status': enrichment_status,
            'enriched_at': 'NOW()',
            'last_updated_at': 'NOW()',
            'enrichment_mode': enrichment_mode,
            'api_call_count': result.get('requests_used', 0),
            # Endpoint tracking fields
            'endpoints_attempted': endpoints_attempted,
            'endpoints_succeeded': endpoints_succeeded,
            'endpoint_errors': endpoint_errors if endpoint_errors else {},
            # Basic info
            'zestimate': enrichment_data.get('zestimate'),
            'bedrooms': enrichment_data.get('bedrooms'),
            'bathrooms': enrichment_data.get('bathrooms'),
            'sqft': enrichment_data.get('sqft'),
            'year_built': enrichment_data.get('year_built'),
            'lot_size': enrichment_data.get('lot_size'),
            'property_type': enrichment_data.get('property_type'),
            'last_sold_price': enrichment_data.get('last_sold_price'),
            'last_sold_date': enrichment_data.get('last_sold_date'),
            # JSONB fields
            'comps': enrichment_data.get('comps'),
            'images': enrichment_data.get('images'),
            'price_history': enrichment_data.get('price_history'),
            'tax_history': enrichment_data.get('tax_history'),
            'climate_risk': enrichment_data.get('climate_data'),
            'similar_properties': enrichment_data.get('comps'),  # comps from similar endpoint
            'nearby_properties': enrichment_data.get('nearby_properties'),
            'raw_api_response': enrichment_data if enrichment_data else None,
        }

        # Upsert to zillow_enrichment table
        supabase.table('zillow_enrichment').upsert(
            zillow_record,
            on_conflict='zpid'
        ).execute()

        # Update foreclosure_listings with only summary/join fields
        summary_update = {
            'zillow_zpid': enrichment_data.get('zpid'),
            'zillow_enrichment_status': 'fully_enriched' if len(endpoints_called) >= 4 else 'auto_enriched',
            'zillow_enriched_at': 'NOW()',
        }

        supabase.table('foreclosure_listings').update(summary_update).eq('id', property_id).execute()

        print(f"Successfully enriched property {property_id} with {len(endpoints_called)} endpoints")

    except Exception as e:
        print(f"Error enriching property {property_id}: {e}")
        # Update with failed status
        try:
            supabase.table('foreclosure_listings').update({
                'zillow_enrichment_status': 'failed',
                'zillow_enriched_at': 'NOW()'
            }).eq('id', property_id).execute()
        except Exception as db_err:
            logger.error(f"Failed to update enrichment status to failed: {db_err}")
            # Continue anyway - enrichment already failed
    finally:
        await service.close()


@router.post(
    "/properties/{property_id}/enrich",
    response_model=EnrichmentResponse,
    summary="Enrich Property with Settings",
    description="Trigger Zillow enrichment using resolved settings (Admin > County > User)"
)
async def enrich_property(
    property_id: int,
    background_tasks: BackgroundTasks,
    request: EnrichPropertyRequest = None
):
    """Enrich a property with settings."""
    if request is None:
        request = EnrichPropertyRequest()

    # Get property county and state
    prop_result = supabase.table('foreclosure_listings').select(
        'id', 'county_id', 'state'
    ).eq('id', property_id).execute()

    if not prop_result.data:
        raise HTTPException(status_code=404, detail="Property not found")

    prop = prop_result.data[0]
    county_id = prop.get('county_id')
    state = prop.get('state')

    if not county_id or not state:
        raise HTTPException(
            status_code=400,
            detail="Property missing county_id or state"
        )

    # Queue background enrichment
    background_tasks.add_task(
        enrich_property_with_settings,
        property_id,
        county_id,
        state,
        request.user_id,
        request.endpoints  # Pass the endpoints from request
    )

    return EnrichmentResponse(
        property_id=property_id,
        success=True,
        status="queued",
        message=f"Enrichment queued for property {property_id}"
    )


@router.get(
    "/properties/{property_id}",
    summary="Get Property Details",
    description="Get full property details with enrichment data"
)
async def get_property(property_id: int):
    """Get property with enrichment."""
    try:
        # Query foreclosure_listings
        prop_result = supabase.table('foreclosure_listings').select(
            '*'
        ).eq('id', property_id).execute()

        if not prop_result.data:
            raise HTTPException(status_code=404, detail="Property not found")

        prop = prop_result.data[0]

        # Query zillow_enrichment
        enrich_result = supabase.table('zillow_enrichment').select(
            '*'
        ).eq('property_id', property_id).execute()

        if enrich_result.data:
            enrichment = enrich_result.data[0]
            # Add zillow_enrichment data under a nested key
            prop['zillow_enrichment'] = enrichment

        return prop
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SKIP TRACING
# ============================================

@router.post(
    "/properties/{property_id}/skip-trace",
    summary="Skip Trace Property",
    description="Skip trace property owner for contact information"
)
async def skip_trace_property(
    property_id: int,
    request: SkipTraceRequest = None
):
    """Skip trace a property."""
    if request is None:
        request = SkipTraceRequest()

    try:
        # Get property address
        prop_result = supabase.table('foreclosure_listings').select(
            'property_address', 'city', 'state', 'zip_code'
        ).eq('id', property_id).execute()

        if not prop_result.data:
            raise HTTPException(status_code=404, detail="Property not found")

        prop = prop_result.data[0]

        service = SkipTraceService()
        result = await service.skip_trace_property(
            property_id=property_id,
            address=prop['property_address'],
            city=prop['city'],
            state=prop['state'],
            zip_code=prop['zip_code'],
            skip_if_exists=request.skip_if_exists
        )

        return {
            "property_id": property_id,
            "success": result.success,
            "person_id": result.person_id,
            "data": service.format_for_display(result.data) if result.data else None,
            "error": result.error,
            "requests_used": result.requests_used
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/skip-trace/batch",
    summary="Batch Skip Trace",
    description="Skip trace multiple enriched properties"
)
async def batch_skip_trace(request: BulkSkipTraceRequest = None):
    """Batch skip trace enriched properties."""
    if request is None:
        request = BulkSkipTraceRequest()

    try:
        service = SkipTraceService()
        result = await service.batch_update_from_enrichment(
            limit=request.limit,
            skip_if_exists=request.skip_if_exists
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/properties/{property_id}/skip-trace",
    summary="Get Skip Trace Data",
    description="Get skip trace data for a property"
)
async def get_skip_trace_data(property_id: int):
    """Get skip trace data."""
    try:
        enrich_result = supabase.table('zillow_enrichment').select(
            'person_id', 'skip_trace_data', 'skip_traced_at'
        ).eq('property_id', property_id).execute()

        if not enrich_result.data:
            raise HTTPException(status_code=404, detail="Property not found")

        enrichment = enrich_result.data[0]

        if not enrichment.get('skip_trace_data'):
            raise HTTPException(
                status_code=404,
                detail="Skip trace data not available. Use POST /skip-trace to trigger."
            )

        service = SkipTraceService()
        return {
            "property_id": property_id,
            "person_id": enrichment.get('person_id'),
            "skip_traced_at": enrichment.get('skip_traced_at'),
            "data": service.format_for_display(enrichment.get('skip_trace_data'))
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TRACERFY SKIP TRACING
# ============================================

@router.post(
    "/properties/{property_id}/tracerfy",
    summary="Skip Trace Property with Tracerfy",
    description="Skip trace property owner using Tracerfy API (address-based search)"
)
async def tracerfy_property(
    property_id: int,
    request: SkipTraceRequest = None
):
    """Skip trace a property using Tracerfy."""
    if request is None:
        request = SkipTraceRequest()

    try:
        # Get property address
        prop_result = supabase.table('foreclosure_listings').select(
            'property_address', 'city', 'state', 'zip_code'
        ).eq('id', property_id).execute()

        if not prop_result.data:
            raise HTTPException(status_code=404, detail="Property not found")

        prop = prop_result.data[0]

        service = TracerfyService()
        result = await service.skip_trace_property(
            property_id=property_id,
            address=prop['property_address'],
            city=prop['city'],
            state=prop['state'],
            zip_code=prop['zip_code'],
            skip_if_exists=request.skip_if_exists
        )

        return {
            "property_id": property_id,
            "success": result.success,
            "job_id": result.job_id,
            "status": result.status,
            "data": service.format_for_display(result.data) if result.data else None,
            "error": result.error
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/properties/{property_id}/tracerfy/{job_id}",
    summary="Get Tracerfy Job Status",
    description="Check the status of a Tracerfy skip trace job"
)
async def get_tracerfy_status(property_id: int, job_id: str):
    """Get Tracerfy job status."""
    try:
        service = TracerfyService()
        result = await service.get_job_status(job_id)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "property_id": property_id,
            "job_id": job_id,
            "status": result.get("status"),
            "data": result.get("data")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/properties/{property_id}/tracerfy/{job_id}/poll",
    summary="Poll and Update Tracerfy Results",
    description="Poll Tracerfy for job completion and update database with results"
)
async def poll_tracerfy_results(property_id: int, job_id: str):
    """Poll Tracerfy job and update database with results."""
    try:
        service = TracerfyService()
        result = await service.poll_and_update(
            property_id=property_id,
            job_id=job_id
        )

        return {
            "property_id": property_id,
            "job_id": job_id,
            "success": result.success,
            "status": result.status,
            "data": service.format_for_display(result.data) if result.data else None,
            "error": result.error
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
