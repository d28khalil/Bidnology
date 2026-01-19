"""
User Property Overrides API Routes

REST API endpoints for user-specific property value overrides.
Users can override approx_upset and judgment_amount values for personal tracking.
All values are user-specific and include history tracking with spread calculations.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/api/property-overrides",
    tags=["Property Overrides"]
)

# Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)


# ============================================
# Request/Response Models
# ============================================

class OverrideCreate(BaseModel):
    """Create a new property override."""
    property_id: int = Field(..., description="Property ID")
    field_name: str = Field(
        ...,
        description="Field name: 'approx_upset', 'judgment_amount', 'starting_bid', 'bid_cap', or 'property_sold'"
    )
    new_value: Optional[float] = Field(None, description="New value to set (numeric for bids)")
    notes: Optional[str] = Field(None, description="Optional notes for this override")
    # For property_sold, we might pass a boolean or timestamp
    property_sold_date: Optional[str] = Field(None, description="ISO timestamp when property was sold (only for property_sold field)")


class OverrideResponse(BaseModel):
    """Override response."""
    id: int
    user_id: str
    property_id: int
    field_name: str
    original_value: Optional[float]
    new_value: float
    previous_spread: Optional[float]
    notes: Optional[str]
    created_at: str


class OverrideHistoryResponse(BaseModel):
    """Override history response."""
    id: int
    original_value: Optional[float]
    new_value: float
    previous_spread: Optional[float]
    notes: Optional[str]
    created_at: str


class PropertyOverridesResponse(BaseModel):
    """All overrides for a property."""
    property_id: int
    approx_upset_override: Optional[float]
    judgment_amount_override: Optional[float]
    starting_bid_override: Optional[float]
    bid_cap_override: Optional[float]
    property_sold_override: Optional[str]  # ISO timestamp or "true"


# ============================================
# OVERRIDE MANAGEMENT ENDPOINTS
# ============================================

@router.get(
    "/property/{property_id}",
    response_model=PropertyOverridesResponse,
    summary="Get Property Overrides",
    description="Get current user's overrides for a specific property"
)
async def get_property_overrides(
    property_id: int,
    user_id: str = Query(..., description="User ID from Clerk")
) -> PropertyOverridesResponse:
    """Get all overrides for a property."""
    try:
        # Get the latest override for each field
        approx_upset_override = None
        judgment_amount_override = None
        starting_bid_override = None
        bid_cap_override = None
        property_sold_override = None

        result = supabase.table('user_property_overrides').select('*')\
            .eq('user_id', user_id)\
            .eq('property_id', property_id)\
            .order('created_at', desc=True)\
            .execute()

        for override in result.data:
            field = override['field_name']
            value = override.get('new_value')
            if field == 'approx_upset' and approx_upset_override is None:
                approx_upset_override = value
            elif field == 'judgment_amount' and judgment_amount_override is None:
                judgment_amount_override = value
            elif field == 'starting_bid' and starting_bid_override is None:
                starting_bid_override = value
            elif field == 'bid_cap' and bid_cap_override is None:
                bid_cap_override = value
            elif field == 'property_sold' and property_sold_override is None:
                property_sold_override = value  # Could be timestamp string

        return PropertyOverridesResponse(
            property_id=property_id,
            approx_upset_override=approx_upset_override,
            judgment_amount_override=judgment_amount_override,
            starting_bid_override=starting_bid_override,
            bid_cap_override=bid_cap_override,
            property_sold_override=property_sold_override
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching overrides: {str(e)}")


@router.post(
    "/",
    response_model=OverrideResponse,
    summary="Create Property Override",
    description="Create a new override for a property field with spread tracking"
)
async def create_override(
    request: OverrideCreate,
    user_id: str = Query(..., description="User ID from Clerk")
) -> OverrideResponse:
    """Create a new property override."""
    try:
        # Validate field_name
        valid_fields = ['approx_upset', 'judgment_amount', 'starting_bid', 'bid_cap', 'property_sold']
        if request.field_name not in valid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"field_name must be one of: {', '.join(valid_fields)}"
            )

        # For property_sold, store the sale price in new_value
        # Store the date in notes field
        value_to_store = request.new_value
        notes_to_store = request.notes

        if request.field_name == 'property_sold':
            # new_value is the sale price (number)
            # Store the sale date in notes for property_sold
            if request.property_sold_date:
                notes_to_store = f"Sold date: {request.property_sold_date}"
            else:
                notes_to_store = "Sold (date not specified)"
        else:
            # For other fields, use the provided notes
            notes_to_store = request.notes

        # Check if property exists
        prop = supabase.table('foreclosure_listings').select(
            'id', 'approx_upset', 'judgment_amount'
        ).eq('id', request.property_id).single().execute()

        if not prop.data:
            raise HTTPException(status_code=404, detail="Property not found")

        property_data = prop.data
        original_value = None
        previous_spread = None

        # Get original value based on field_name (only for approx_upset and judgment_amount)
        if request.field_name == 'approx_upset':
            original_value = property_data.get('approx_upset')
        elif request.field_name == 'judgment_amount':
            original_value = property_data.get('judgment_amount')
        # For starting_bid, bid_cap, property_sold, there's no "original" in foreclosure_listings

        # Get zestimate from enrichment table if available (for spread calculation)
        zestimate = None
        if request.field_name in ['approx_upset', 'judgment_amount']:
            enrichment = supabase.table('zillow_enrichment').select('zestimate')\
                .eq('property_id', request.property_id)\
                .execute()
            if enrichment.data and len(enrichment.data) > 0:
                zestimate = enrichment.data[0].get('zestimate')

        # Get other override values if they exist
        other_overrides = supabase.table('user_property_overrides').select('*')\
            .eq('user_id', user_id)\
            .eq('property_id', request.property_id)\
            .order('created_at', desc=True)\
            .execute()

        approx_upset_val = property_data.get('approx_upset')
        judgment_amount_val = property_data.get('judgment_amount')

        # Apply existing overrides to the other fields
        for override in other_overrides.data:
            if override['field_name'] == 'approx_upset' and approx_upset_val is None:
                approx_upset_val = override['new_value']
            elif override['field_name'] == 'judgment_amount' and judgment_amount_val is None:
                judgment_amount_val = override['new_value']

        # Apply the new override (only for fields that affect spread)
        if request.field_name == 'approx_upset':
            approx_upset_val = value_to_store
        elif request.field_name == 'judgment_amount':
            judgment_amount_val = value_to_store

        # Calculate spread using the higher of upset/judgment (only for relevant fields)
        if request.field_name in ['approx_upset', 'judgment_amount']:
            base_price = max(
                approx_upset_val or 0,
                judgment_amount_val or 0
            ) or 0

            if base_price > 0 and zestimate:
                previous_spread = ((zestimate - base_price) / base_price) * 100

        # Insert override
        result = supabase.table('user_property_overrides').insert({
            'user_id': user_id,
            'property_id': request.property_id,
            'field_name': request.field_name,
            'original_value': original_value,
            'new_value': value_to_store,
            'previous_spread': previous_spread,
            'notes': notes_to_store
        }).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create override")

        override = result.data[0]
        return OverrideResponse(
            id=override['id'],
            user_id=override['user_id'],
            property_id=override['property_id'],
            field_name=override['field_name'],
            original_value=override.get('original_value'),
            new_value=override['new_value'],
            previous_spread=override.get('previous_spread'),
            notes=override.get('notes'),
            created_at=override['created_at'].isoformat() if hasattr(override['created_at'], 'isoformat') else str(override['created_at'])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating override: {str(e)}")


@router.get(
    "/property/{property_id}/history/{field_name}",
    response_model=List[OverrideHistoryResponse],
    summary="Get Override History",
    description="Get change history for a specific property field"
)
async def get_override_history(
    property_id: int,
    field_name: str,
    user_id: str = Query(..., description="User ID from Clerk")
) -> List[OverrideHistoryResponse]:
    """Get override history for a field."""
    try:
        # Validate field_name
        valid_fields = ['approx_upset', 'judgment_amount', 'starting_bid', 'bid_cap', 'property_sold']
        if field_name not in valid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"field_name must be one of: {', '.join(valid_fields)}"
            )

        result = supabase.table('user_property_overrides').select('*')\
            .eq('user_id', user_id)\
            .eq('property_id', property_id)\
            .eq('field_name', field_name)\
            .order('created_at', desc=True)\
            .execute()

        history = []
        for override in result.data:
            history.append(OverrideHistoryResponse(
                id=override['id'],
                original_value=override.get('original_value'),
                new_value=override['new_value'],
                previous_spread=override.get('previous_spread'),
                notes=override.get('notes'),
                created_at=override['created_at'].isoformat() if hasattr(override['created_at'], 'isoformat') else str(override['created_at'])
            ))

        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


@router.delete(
    "/{override_id}",
    summary="Delete Override",
    description="Delete a specific override and revert to original value"
)
async def delete_override(
    override_id: int,
    user_id: str = Query(..., description="User ID from Clerk")
):
    """Delete a property override."""
    try:
        # First verify the override belongs to the user
        existing = supabase.table('user_property_overrides').select('*')\
            .eq('id', override_id)\
            .eq('user_id', user_id)\
            .single().execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Override not found or doesn't belong to user")

        # Delete the override
        supabase.table('user_property_overrides').delete()\
            .eq('id', override_id)\
            .eq('user_id', user_id)\
            .execute()

        return {"message": "Override deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting override: {str(e)}")


@router.delete(
    "/property/{property_id}/field/{field_name}",
    summary="Revert Field to Original",
    description="Delete all overrides for a specific field on a property"
)
async def revert_field(
    property_id: int,
    field_name: str,
    user_id: str = Query(..., description="User ID from Clerk")
):
    """Revert a field to its original value."""
    try:
        # Validate field_name
        valid_fields = ['approx_upset', 'judgment_amount', 'starting_bid', 'bid_cap', 'property_sold']
        if field_name not in valid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"field_name must be one of: {', '.join(valid_fields)}"
            )

        # Delete all overrides for this field
        supabase.table('user_property_overrides').delete()\
            .eq('user_id', user_id)\
            .eq('property_id', property_id)\
            .eq('field_name', field_name)\
            .execute()

        return {"message": f"Reverted {field_name} to original value"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reverting field: {str(e)}")
