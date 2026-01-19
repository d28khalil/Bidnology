# API Routes - Enrichment Settings System

**Version:** 1.0
**Date:** December 27, 2025

---

## Overview

FastAPI routes for managing enrichment settings at three levels:
1. **Admin Settings** - Global defaults and locks
2. **County Settings** - Per-county overrides
3. **User Preferences** - Per-user overrides (if allowed)

---

## Table of Contents

- [Admin Settings Routes](#admin-settings-routes)
- [County Settings Routes](#county-settings-routes)
- [User Preferences Routes](#user-preferences-routes)
- [Template Routes](#template-routes)
- [Enrichment Execution Routes](#enrichment-execution-routes)

---

## Admin Settings Routes

### GET /api/admin/settings

Get current admin settings (singleton).

**Response:**
```json
{
  "id": 1,
  "endpoint_pro_byaddress": true,
  "endpoint_lock_pro_byaddress": false,
  "endpoint_custom_ad_byzpid": true,
  "endpoint_lock_custom_ad_byzpid": false,
  "endpoint_similar": true,
  "endpoint_lock_similar": false,
  "endpoint_nearby": false,
  "endpoint_lock_nearby": false,
  "endpoint_pricehistory": true,
  "endpoint_lock_pricehistory": false,
  "endpoint_graph_listing_price": false,
  "endpoint_lock_graph_listing_price": false,
  "endpoint_taxinfo": true,
  "endpoint_lock_taxinfo": false,
  "endpoint_climate": true,
  "endpoint_lock_climate": false,
  "endpoint_walk_transit_bike": true,
  "endpoint_lock_walk_transit_bike": false,
  "endpoint_housing_market": false,
  "endpoint_lock_housing_market": false,
  "endpoint_rental_market": false,
  "endpoint_lock_rental_market": false,
  "endpoint_ownerinfo": false,
  "endpoint_lock_ownerinfo": false,
  "endpoint_custom_ae_search": false,
  "endpoint_lock_custom_ae_search": false,
  "enable_skip_trace_external": true,
  "skip_trace_external_enabled": false,
  "skip_trace_external_lock": false,
  "inv_annual_appreciation": 0.03,
  "inv_mortgage_rate": 0.045,
  "inv_down_payment_rate": 0.20,
  "inv_insurance_rate": 0.015,
  "inv_loan_term_months": 360,
  "inv_maintenance_rate": 0.10,
  "inv_property_mgmt_rate": 0.10,
  "inv_property_tax_rate": 0.012,
  "inv_vacancy_rate": 0.05,
  "inv_renovation_cost": 25000,
  "allow_user_overrides": true,
  "allow_user_templates": true,
  "allow_custom_investment_params": true,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

---

### PUT /api/admin/settings

Update admin settings (creates if doesn't exist).

**Request Body:**
```json
{
  "endpoint_pro_byaddress": true,
  "endpoint_lock_pro_byaddress": true,
  "skip_trace_external_enabled": true,
  "allow_user_overrides": true,
  "inv_annual_appreciation": 0.035
}
```

**Partial update allowed** - only include fields to change.

**Response:** Returns updated settings object (same as GET).

---

## County Settings Routes

### GET /api/admin/counties

List all county settings.

**Query Params:**
- `state` (optional) - Filter by state code
- `template_preset` (optional) - Filter by template

**Response:**
```json
{
  "count": 3,
  "counties": [
    {
      "id": 1,
      "county_id": 25290,
      "county_name": "Duval",
      "state": "FL",
      "endpoint_pro_byaddress": true,
      "endpoint_similar": true,
      "template_preset": "flipper",
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

---

### GET /api/admin/counties/{county_id}

Get settings for a specific county.

**Path Params:**
- `county_id` - County identifier

**Response:**
```json
{
  "id": 1,
  "county_id": 25290,
  "county_name": "Duval",
  "state": "FL",
  "endpoint_pro_byaddress": true,
  "endpoint_custom_ad_byzpid": true,
  "endpoint_similar": true,
  "endpoint_pricehistory": true,
  "endpoint_taxinfo": true,
  "endpoint_climate": false,
  "template_preset": "flipper",
  "skip_trace_external_enabled": true,
  "inv_annual_appreciation": 0.04,
  "inv_mortgage_rate": 0.05,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

---

### PUT /api/admin/counties/{county_id}

Create or update county settings.

**Path Params:**
- `county_id` - County identifier

**Request Body:**
```json
{
  "county_name": "Duval",
  "state": "FL",
  "endpoint_similar": true,
  "endpoint_climate": true,
  "template_preset": "landlord",
  "skip_trace_external_enabled": true,
  "inv_annual_appreciation": 0.04
}
```

**Response:** Returns updated county settings.

---

### DELETE /api/admin/counties/{county_id}

Delete county settings (reverts to admin defaults).

**Path Params:**
- `county_id` - County identifier

**Response:**
```json
{
  "message": "County settings deleted",
  "county_id": 25290
}
```

---

### POST /api/admin/counties/{county_id}/apply-template

Apply a template preset to a county.

**Path Params:**
- `county_id` - County identifier

**Request Body:**
```json
{
  "template": "landlord"
}
```

**Response:** Returns updated county settings with template applied.

---

## User Preferences Routes

### GET /api/users/{user_id}/preferences

Get user preferences for all counties.

**Path Params:**
- `user_id` - User UUID

**Query Params:**
- `county_id` (optional) - Filter by county
- `state` (optional) - Filter by state

**Response:**
```json
{
  "count": 2,
  "preferences": [
    {
      "id": 1,
      "user_id": "uuid-here",
      "county_id": 25290,
      "state": "FL",
      "endpoint_similar": true,
      "endpoint_climate": true,
      "template_preset": null,
      "skip_trace_external_enabled": false,
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

---

### GET /api/users/{user_id}/preferences/{county_id}

Get user preferences for a specific county.

**Path Params:**
- `user_id` - User UUID
- `county_id` - County identifier

**Response:** Single preference object (same structure as above).

---

### PUT /api/users/{user_id}/preferences/{county_id}

Create or update user preferences for a county.

**Path Params:**
- `user_id` - User UUID
- `county_id` - County identifier

**Request Body:**
```json
{
  "state": "FL",
  "endpoint_climate": true,
  "endpoint_ownerinfo": true,
  "skip_trace_external_enabled": true,
  "inv_annual_appreciation": 0.035
}
```

**Response:** Returns updated user preferences.

**Error Responses:**
- `403 Forbidden` - If admin has `allow_user_overrides = false`
- `403 Forbidden` - If trying to override a locked endpoint

---

### DELETE /api/users/{user_id}/preferences/{county_id}

Delete user preferences for a county (reverts to county/admin defaults).

**Path Params:**
- `user_id` - User UUID
- `county_id` - County identifier

**Response:**
```json
{
  "message": "User preferences deleted",
  "user_id": "uuid-here",
  "county_id": 25290
}
```

---

## Template Routes

### GET /api/templates

List available template presets.

**Response:**
```json
{
  "templates": [
    {
      "name": "minimal",
      "description": "Essential data only (3 endpoints)",
      "endpoints": [
        "endpoint_pro_byaddress",
        "endpoint_custom_ad_byzpid",
        "endpoint_pricehistory"
      ],
      "cost_per_property": 3
    },
    {
      "name": "flipper",
      "description": "ARV-focused (7 endpoints)",
      "endpoints": [
        "endpoint_pro_byaddress",
        "endpoint_custom_ad_byzpid",
        "endpoint_similar",
        "endpoint_nearby",
        "endpoint_pricehistory",
        "endpoint_taxinfo",
        "endpoint_ownerinfo"
      ],
      "cost_per_property": 7
    },
    {
      "name": "landlord",
      "description": "Rental ROI focused (9 endpoints)",
      "endpoints": [
        "endpoint_pro_byaddress",
        "endpoint_custom_ad_byzpid",
        "endpoint_similar",
        "endpoint_pricehistory",
        "endpoint_taxinfo",
        "endpoint_climate",
        "endpoint_walk_transit_bike",
        "endpoint_housing_market",
        "endpoint_rental_market"
      ],
      "cost_per_property": 9
    },
    {
      "name": "thorough",
      "description": "Complete analysis (12 endpoints)",
      "endpoints": [
        "endpoint_pro_byaddress",
        "endpoint_custom_ad_byzpid",
        "endpoint_similar",
        "endpoint_nearby",
        "endpoint_pricehistory",
        "endpoint_graph_listing_price",
        "endpoint_taxinfo",
        "endpoint_climate",
        "endpoint_walk_transit_bike",
        "endpoint_housing_market",
        "endpoint_rental_market",
        "endpoint_ownerinfo"
      ],
      "cost_per_property": 12
    }
  ]
}
```

---

### GET /api/templates/{template_name}

Get details for a specific template.

**Path Params:**
- `template_name` - Template name (minimal, flipper, landlord, thorough)

**Response:**
```json
{
  "name": "flipper",
  "description": "ARV-focused (7 endpoints)",
  "endpoints": [...],
  "investment_params": {
    "inv_annual_appreciation": 0.03,
    "inv_mortgage_rate": 0.045,
    "inv_down_payment_rate": 0.20
  },
  "metrics_available": [
    "ARV from similar properties",
    "Price history red flags",
    "Tax burden",
    "Owner contact info"
  ],
  "cost_per_property": 7,
  "properties_per_month_250": 35
}
```

---

## Enrichment Execution Routes

### POST /api/enrichment/property

Enrich a single property with configured endpoints.

**Request Body:**
```json
{
  "property_id": 12345,
  "address": "1875 AVONDALE Circle, Jacksonville, FL 32205",
  "county_id": 25290,
  "user_id": "uuid-here",
  "force_refresh": false
}
```

**Response:**
```json
{
  "property_id": 12345,
  "zpid": "44480538",
  "endpoints_called": [
    "pro_byaddress",
    "custom_ad_byzpid",
    "similar",
    "pricehistory"
  ],
  "requests_used": 4,
  "data": {
    "basic_info": {...},
    "images": [...],
    "comps": [...],
    "price_history": [...]
  },
  "metrics_available": {
    "has_arv": true,
    "has_cash_flow": false,
    "has_climate_risk": false,
    "has_investment_metrics": false
  },
  "enriched_at": "2025-01-15T10:00:00Z"
}
```

---

### POST /api/enrichment/batch

Enrich multiple properties (async job).

**Request Body:**
```json
{
  "property_ids": [12345, 12346, 12347],
  "user_id": "uuid-here",
  "priority": "normal"
}
```

**Response:**
```json
{
  "job_id": "job-uuid-here",
  "status": "queued",
  "total_properties": 3,
  "estimated_requests": 12,
  "estimated_completion": "2025-01-15T10:05:00Z"
}
```

---

### GET /api/enrichment/job/{job_id}

Get status of batch enrichment job.

**Path Params:**
- `job_id` - Job UUID from batch endpoint

**Response:**
```json
{
  "job_id": "job-uuid-here",
  "status": "processing",
  "progress": {
    "completed": 2,
    "total": 3,
    "failed": 0
  },
  "results": [
    {
      "property_id": 12345,
      "status": "completed",
      "requests_used": 4
    },
    {
      "property_id": 12346,
      "status": "completed",
      "requests_used": 4
    },
    {
      "property_id": 12347,
      "status": "pending"
    }
  ],
  "started_at": "2025-01-15T10:00:00Z",
  "estimated_completion": "2025-01-15T10:01:00Z"
}
```

---

### GET /api/enrichment/property/{property_id}

Get enriched data for a property.

**Path Params:**
- `property_id` - Property ID

**Query Params:**
- `user_id` - User UUID (for settings resolution)

**Response:**
```json
{
  "property_id": 12345,
  "zpid": "44480538",
  "address": "1875 AVONDALE Circle, Jacksonville, FL 32205",
  "basic_info": {
    "bedrooms": 7,
    "bathrooms": 9,
    "sqft": 7526,
    "year_built": 1927,
    "zestimate": 4161200,
    "rent_zestimate": null
  },
  "images": ["https://...", ...],
  "comps": [
    {
      "zpid": "44480540",
      "price": 3950000,
      "bedrooms": 4,
      "bathrooms": 6,
      "sqft": 4876
    }
  ],
  "price_history": [...],
  "tax_info": {...},
  "metrics": {
    "avg_comp_price": 3850000,
    "arv_range": {
      "low": 3500000,
      "high": 4200000
    }
  },
  "enriched_at": "2025-01-15T10:00:00Z",
  "endpoints_used": ["pro_byaddress", "custom_ad_byzpid", "similar", "pricehistory"]
}
```

---

### POST /api/enrichment/property/{property_id}/skip-trace

Run skip tracing on a property (external API).

**Path Params:**
- `property_id` - Property ID

**Request Body:**
```json
{
  "address": "1875 AVONDALE Circle",
  "city": "Jacksonville",
  "state": "FL",
  "zip": "32205"
}
```

**Response:**
```json
{
  "property_id": 12345,
  "skip_trace_results": [
    {
      "name": "JOHN DOE",
      "age": 45,
      "phones": ["904-555-1234"],
      "emails": ["john@example.com"],
      "relatives": ["JANE DOE"],
      "person_id": "px12345"
    }
  ],
  "traced_at": "2025-01-15T10:00:00Z"
}
```

---

### GET /api/enrichment/config-preview

Preview what endpoints would be used for a given context.

**Query Params:**
- `user_id` (optional) - User UUID
- `county_id` (optional) - County ID

**Response:**
```json
{
  "settings_source": "county",  // admin, county, or user
  "endpoints_enabled": {
    "pro_byaddress": true,
    "custom_ad_byzpid": true,
    "similar": true,
    "nearby": false,
    "pricehistory": true,
    "climate": false
  },
  "template_preset": "flipper",
  "cost_per_property": 4,
  "investment_params": {
    "annual_appreciation": 0.03,
    "mortgage_rate": 0.045
  },
  "metrics_available": [
    "ARV from comps",
    "Price history",
    "Property photos"
  ],
  "metrics_not_available": [
    "Climate risk",
    "Walk score",
    "Rental trends"
  ]
}
```

---

## Utility Routes

### GET /api/enrichment/quota

Check remaining RapidAPI quota.

**Response:**
```json
{
  "requests_remaining": 238,
  "requests_used_this_month": 12,
  "monthly_limit": 250,
  "reset_date": "2025-02-01T00:00:00Z"
}
```

---

### GET /api/enrichment/health

Health check for enrichment service.

**Response:**
```json
{
  "status": "healthy",
  "rapidapi_status": "up",
  "database_status": "up",
  "skip_trace_status": "up",
  "version": "1.0.0"
}
```

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request",
  "detail": "county_id is required"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required",
  "detail": "Invalid or missing API key"
}
```

### 403 Forbidden
```json
{
  "error": "Access denied",
  "detail": "User overrides are not allowed by admin"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found",
  "detail": "County settings not found for county_id: 99999"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "detail": "RapidAPI quota exhausted",
  "reset_date": "2025-02-01T00:00:00Z"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "Failed to fetch property data from RapidAPI"
}
```

---

## Authentication

All routes require authentication via JWT token:

```
Authorization: Bearer <jwt_token>
```

Admin routes (`/api/admin/*`) require admin role:
```json
{
  "user_id": "uuid",
  "role": "admin"
}
```

---

## Rate Limiting

| Route | Limit |
|-------|-------|
| Enrichment endpoints | 10 requests/minute per user |
| Settings endpoints | 60 requests/minute per user |
| Admin endpoints | 60 requests/minute per admin |
