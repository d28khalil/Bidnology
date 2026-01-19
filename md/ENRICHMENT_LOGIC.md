# Enrichment Logic - Execution Flow

**Version:** 1.0
**Date:** December 27, 2025

---

## Overview

This document describes how the enrichment system executes API calls to Zillow based on the three-tier settings system (Admin → County → User).

---

## Table of Contents

- [High-Level Flow](#high-level-flow)
- [Settings Resolution](#settings-resolution)
- [Endpoint Execution Order](#endpoint-execution-order)
- [Data Extraction & Storage](#data-extraction--storage)
- [Error Handling](#error-handling)
- [Batch Processing](#batch-processing)
- [Caching Strategy](#caching-strategy)

---

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         ENRICHMENT REQUEST                       │
│  Input: property_id, address, county_id, user_id (optional)     │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    1. RESOLVE SETTINGS                          │
│  - Query admin settings (singleton)                              │
│  - Query county settings (by county_id)                         │
│  - Query user preferences (by user_id + county_id)              │
│  - Merge with priority: User > County > Admin                   │
│  - Check locks (user cannot override locked settings)           │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. BUILD ENDPOINT LIST                       │
│  - Filter enabled endpoints from merged settings                │
│  - Sort by execution order (see below)                          │
│  - Calculate total request cost                                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    3. CHECK QUOTA                               │
│  - Verify sufficient RapidAPI quota remains                     │
│  - Return 429 if quota exceeded                                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. EXECUTE ENDPOINTS                         │
│  - Sequential execution (to avoid rate limits)                  │
│  - Each endpoint:                                               │
│    1. Check cache first                                         │
│    2. Build request parameters                                  │
│    3. Call RapidAPI                                             │
│    4. Parse response                                            │
│    5. Extract data                                              │
│    6. Store in database                                         │
│    7. Update cache                                              │
│  - Continue on non-critical errors                              │
│  - Stop on critical errors                                      │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    5. CALCULATE METRICS                         │
│  - ARV from comps (median of similar sold prices)               │
│  - Cash flow (if rental estimate available)                     │
│  - Investment metrics (if custom_ae enabled)                    │
│  - Risk scores (climate, price volatility)                      │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    6. RETURN RESULTS                            │
│  - Enriched data                                                │
│  - Metrics calculated                                           │
│  - Endpoints called                                             │
│  - Requests used                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Settings Resolution

### Priority Order

Settings are resolved in this order (highest priority first):

1. **User Preferences** - If `allow_user_overrides = true` in admin settings
2. **County Settings** - Overrides for specific county
3. **Admin Settings** - Global defaults

### Lock Check

An endpoint is **locked** when:
- `endpoint_lock_* = true` in admin settings OR
- `endpoint_lock_* = true` in county settings

Locked endpoints **cannot** be overridden by lower-priority settings:
- Locked at Admin level → County and User cannot override
- Locked at County level → User cannot override

### Resolution Algorithm

```python
def resolve_settings(county_id: int, user_id: str = None):
    # 1. Get admin settings
    admin = get_admin_settings()

    # 2. Get county settings (may be None)
    county = get_county_settings(county_id)

    # 3. Get user preferences (may be None, may be forbidden)
    user = None
    if user_id and admin.allow_user_overrides:
        user = get_user_preferences(user_id, county_id)

    # 4. Resolve each setting
    resolved = {}

    for setting in ALL_SETTINGS:
        admin_value = admin[setting]
        admin_lock = admin[f"{setting}_lock"]

        county_value = county[setting] if county else None
        county_lock = county[f"{setting}_lock"] if county else False

        user_value = user[setting] if user else None

        # Apply lock logic
        if admin_lock:
            resolved[setting] = admin_value
        elif county_lock:
            resolved[setting] = county_value if county_value is not None else admin_value
        else:
            # No lock - use highest priority non-null value
            resolved[setting] = coalesce(user_value, county_value, admin_value)

    return resolved
```

---

## Endpoint Execution Order

Endpoints are executed in a specific order to handle dependencies:

### Phase 1: Core Property Data (Required)

1. **`pro_byaddress`** - Get ZPID (required for most other endpoints)
2. **`custom_ad_byzpid`** - Get property details + images (requires ZPID)

### Phase 2: Comps & History (Auto-Enrichment)

3. **`similar`** - Active listings for ARV comparison
4. **`pricehistory`** - Price changes over time
5. **`taxinfo`** - Tax history and current amount
6. **`nearby`** - Nearby properties (optional)

### Phase 3: Market Data (Optional)

7. **`graph_listing_price`** - 10-year listing price chart
8. **`housing_market`** - ZHVI market trends
9. **`rental_market`** - Rental trends by bedroom

### Phase 4: Location & Risk (Optional)

10. **`climate`** - Climate risk scores
11. **`walk_transit_bike`** - Location scores

### Phase 5: Contact (Optional)

12. **`ownerinfo`** - Owner and agent information

### Separate: Search Endpoint

- **`custom_ae_search`** - Not used for single property enrichment
  - Used for deal discovery (separate workflow)

### Skip Tracing (External API)

- **External skip tracing** - On-demand only
  - Not part of auto-enrichment
  - Uses separate API service

---

## Data Extraction & Storage

### Response Mapping

Each endpoint response is mapped to the database schema:

```python
ENDPOINT_MAPPING = {
    "pro_byaddress": {
        "zpid": "PropertyZPID",
        "address": "PropertyAddress",
        "bedrooms": "Bedrooms",
        "bathrooms": "Bathrooms",
        "sqft": "Area(sqft)",
        "year_built": "yearBuilt",
        "zestimate": "zestimate",
        "rent_zestimate": "rentZestimate",  # if available
        "days_on_zillow": "daysOnZillow",
        "price": "Price",
        "url": "PropertyZillowURL"
    },

    "custom_ad_byzpid": {
        "images": "images",  # Array of image URLs
        # Plus other custom fields
    },

    "similar": {
        "comps": "similar_properties.propertyDetails",
        # Each comp: zpid, price, bedrooms, bathrooms, livingArea, address
    },

    "pricehistory": {
        "price_history": "priceHistory",
        # Each event: date, price, event_type
    },

    "taxinfo": {
        "tax_history": "taxHistory",
        "tax_amount": "currentTaxAmount",
        "tax_year": "taxYear"
    },

    "climate": {
        "flood_risk": "climateData.flood.riskScore",
        "fire_risk": "climateData.fire.riskScore",
        "storm_risk": "climateData.storm.riskScore"
    },

    "walk_transit_bike": {
        "walk_score": "walkScore",
        "transit_score": "transitScore",
        "bike_score": "bikeScore"
    },

    "ownerinfo": {
        "owner_name": "owner.name",
        "agent_name": "listingAgent.name",
        "agent_phone": "listingAgent.phone",
        "agent_email": "listingAgent.email"
    }
}
```

### Storage Structure

Data is stored in the `zillow_enrichment` table:

```sql
UPDATE zillow_enrichment SET
    -- Core fields
    zpid = :zpid,
    bedrooms = :bedrooms,
    bathrooms = :bathrooms,
    sqft = :sqft,
    year_built = :year_built,
    zestimate = :zestimate,
    rent_zestimate = :rent_zestimate,

    -- JSON fields for complex data
    images = :images_json,              -- JSONB array
    comps = :comps_json,                -- JSONB array
    price_history = :price_history_json,-- JSONB array
    tax_history = :tax_history_json,    -- JSONB array
    climate_data = :climate_json,       -- JSONB object
    location_scores = :location_json,   -- JSONB object
    owner_info = :owner_json,           -- JSONB object

    -- Calculated metrics
    arv_low = :arv_low,
    arv_high = :arv_high,
    avg_comp_price = :avg_comp_price,

    -- Metadata
    endpoints_called = :endpoints_called_array,
    requests_used = :request_count,
    enriched_at = NOW()

WHERE property_id = :property_id;
```

---

## Error Handling

### Error Categories

| Error Type | Action | Log Level |
|------------|--------|-----------|
| **Critical** | Stop enrichment, return error | ERROR |
| **Non-Critical** | Continue, log warning | WARNING |
| **Skipped** | Endpoint disabled, skip | INFO |

### Critical Errors

- Authentication failure (invalid API key)
- Quota exceeded (429 from RapidAPI)
- ZPID not found (property doesn't exist in Zillow)
- Database connection failure

### Non-Critical Errors

- Single endpoint timeout
- Malformed response from endpoint
- Partial data returned

### Error Response Structure

```python
{
    "success": False,
    "property_id": 12345,
    "error": {
        "type": "quota_exceeded",
        "message": "RapidAPI quota exhausted",
        "reset_date": "2025-02-01T00:00:00Z"
    },
    "partial_results": {
        "endpoints_completed": ["pro_byaddress", "custom_ad_byzpid"],
        "endpoints_failed": ["similar", "pricehistory"],
        "data_stored": True
    }
}
```

---

## Batch Processing

For multiple properties, enrichment runs as async jobs:

```python
async def enrich_batch(property_ids: List[int], user_id: str):
    job = create_batch_job(property_ids, user_id)

    # Process sequentially to respect rate limits
    for prop_id in property_ids:
        try:
            result = await enrich_single(prop_id, user_id)
            job.mark_completed(prop_id, result)
        except Exception as e:
            job.mark_failed(prop_id, str(e))

        # Small delay between properties
        await asyncio.sleep(0.5)

    job.mark_finished()
    return job.summary
```

### Batch Status Tracking

```sql
CREATE TABLE enrichment_jobs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    status VARCHAR(20),  -- queued, processing, completed, failed
    total_properties INT,
    completed_properties INT DEFAULT 0,
    failed_properties INT DEFAULT 0,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

---

## Caching Strategy

### Cache Keys

```
zillow:{endpoint}:{property_id}
zillow:{endpoint}:{zpid}
zillow:{endpoint}:{county_id}:{state}  -- For market endpoints
```

### Cache TTL

| Endpoint | TTL | Reason |
|----------|-----|--------|
| `pro_byaddress` | 7 days | Property details don't change often |
| `custom_ad_byzpid` | 7 days | Images and details stable |
| `similar` | 1 day | Comps change frequently |
| `nearby` | 1 day | Nearby listings change |
| `pricehistory` | 7 days | Historical data doesn't change |
| `taxinfo` | 30 days | Tax data updates yearly |
| `climate` | 30 days | Climate risk data slow to change |
| `walk_transit_bike` | 30 days | Walk scores stable |
| `housing_market` | 1 day | Market data changes daily |
| `rental_market` | 1 day | Rental trends change daily |
| `ownerinfo` | 7 days | Owner info stable |
| `custom_ae_search` | 1 hour | Search results change |

### Cache Implementation (Redis)

```python
async def get_or_call(endpoint: str, params: dict, ttl: int):
    cache_key = f"zillow:{endpoint}:{params['zpid']}"

    # Check cache
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Call API
    response = await call_zillow_api(endpoint, params)

    # Store in cache
    redis.setex(cache_key, ttl, json.dumps(response))

    return response
```

---

## Refresh Strategy

### When to Refresh

| Trigger | Action |
|---------|--------|
| User clicks "Refresh" | Force re-enrichment (bypass cache) |
| Property status changes | Clear cache, re-enrich |
| Scheduled job | Refresh properties older than TTL |
| New endpoint enabled | Re-enrich affected properties |

### Force Refresh Parameter

```python
POST /api/enrichment/property
{
    "property_id": 12345,
    "force_refresh": true  # Bypass cache, re-call all endpoints
}
```

---

## Quota Management

### Quota Check Before Enrichment

```python
def check_quota(requests_needed: int):
    remaining = get_rapidapi_quota()

    if remaining < requests_needed:
        raise QuotaExceeded(
            remaining=remaining,
            needed=requests_needed,
            reset_date=get_quota_reset_date()
        )

    return True
```

### Quota Usage Tracking

```sql
CREATE TABLE quota_usage (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    requests_used INT DEFAULT 0,
    requests_remaining INT DEFAULT 250,
    last_checked TIMESTAMP
);

-- Unique index for daily tracking
UNIQUE(date)
```

---

## External Skip Tracing

Skip tracing uses a **separate API** with its own quota:

```python
async def skip_trace_property(address: str, city: str, state: str, zip: str):
    # External API: skip-tracing-working-api.p.rapidapi.com
    # Separate quota, does not count against Zillow 250/month

    params = {
        "street": address,
        "citystatezip": f"{city}, {state} {zip}",
        "page": 1
    }

    response = await call_skip_trace_api(params)

    # Map to database
    return {
        "property_id": property_id,
        "owner_name": response["name"],
        "owner_phones": response["phones"],
        "owner_emails": response["emails"],
        "relatives": response["relatives"],
        "skip_traced_at": NOW()
    }
```

---

## Metrics Calculation

After all endpoints complete, calculate derived metrics:

### ARV (After Repair Value)

```python
def calculate_arv(comps: List[Dict]) -> Dict[str, float]:
    prices = [c["price"] for c in comps if c.get("homeStatus") == "FOR_SALE"]

    if not prices:
        return None

    return {
        "avg": sum(prices) / len(prices),
        "median": statistics.median(prices),
        "low": min(prices),
        "high": max(prices)
    }
```

### Price Volatility Score

```python
def calculate_volatility(price_history: List[Dict]) -> float:
    # Standard deviation of price changes
    changes = []
    for i in range(1, len(price_history)):
        prev = price_history[i-1]["price"]
        curr = price_history[i]["price"]
        pct_change = abs((curr - prev) / prev)
        changes.append(pct_change)

    return statistics.stdev(changes) if changes else 0
```

---

## Complete Execution Example

```python
# Input
{
    "property_id": 12345,
    "address": "1875 AVONDALE Circle, Jacksonville, FL 32205",
    "county_id": 25290,
    "user_id": "user-uuid"
}

# Step 1: Resolve settings
# Admin: similar=true, climate=false
# County (Duval): similar=true, climate=true
# User: (none)
# Resolved: similar=true, climate=true

# Step 2: Build endpoint list
# ["pro_byaddress", "custom_ad_byzpid", "similar", "climate"]
# Cost: 4 requests

# Step 3: Check quota
# Remaining: 238, Needed: 4 ✓

# Step 4: Execute endpoints
# 1. pro_byaddress → ZPID: 44480538, basic info
# 2. custom_ad_byzpid → 100+ images, details
# 3. similar → 20 comps
# 4. climate → flood/fire/storm scores

# Step 5: Calculate metrics
# ARV: $3.85M (median comp price)
# Flood risk: Moderate (score: 4/10)

# Step 6: Return results
{
    "property_id": 12345,
    "zpid": "44480538",
    "endpoints_called": ["pro_byaddress", "custom_ad_byzpid", "similar", "climate"],
    "requests_used": 4,
    "data": {...},
    "metrics": {
        "arv_median": 3850000,
        "flood_risk": "moderate"
    }
}
```
