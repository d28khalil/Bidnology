# Enrichment System - Complete Summary

**Version:** 1.0
**Date:** December 27, 2025

---

## Overview

This document provides a complete overview of the Zillow enrichment system for the NJ Sheriff Sale Foreclosure Scraper. It combines all configuration, database schema, API routes, and business logic into one reference.

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| [ZILLOW_ENDPOINT_FINAL.md](ZILLOW_ENDPOINT_FINAL.md) | Complete catalog of 13 Zillow endpoints |
| [DATABASE_SCHEMA_ENRICHMENT_SETTINGS.md](DATABASE_SCHEMA_ENRICHMENT_SETTINGS.md) | Three-table settings system schema |
| [API_ROUTES_ENRICHMENT.md](API_ROUTES_ENRICHMENT.md) | All API endpoints for settings and enrichment |
| [ENRICHMENT_LOGIC.md](ENRICHMENT_LOGIC.md) | Execution flow and data processing |
| [INVESTMENT_METRICS.md](INVESTMENT_METRICS.md) | ROI formulas and calculations |
| [SETTINGS_RESOLUTION.md](SETTINGS_RESOLUTION.md) | Settings priority and lock logic |
| [TEMPLATES.md](TEMPLATES.md) | Template presets (Flipper, Landlord, etc.) |
| [SKIP_TRACING_EXTERNAL.md](SKIP_TRACING_EXTERNAL.md) | External skip tracing integration |

---

## Quick Reference

### 13 Final Zillow Endpoints

| # | Endpoint | Cost | Category | Provides |
|---|----------|------|----------|----------|
| 1 | `/pro/byaddress` | 1 | Core | ZPID, beds, baths, sqft, zestimate, rentZestimate |
| 2 | `/custom_ad/byzpid` | 1 | Core | 100+ photos, property details |
| 3 | `/similar` | 1 | Comps | 20+ active listings for ARV |
| 4 | `/nearby` | 1 | Comps | Nearby properties |
| 5 | `/pricehistory` | 1 | History | Price changes over time |
| 6 | `/graph_charts?which=listing_price` | 1 | History | 10-year listing price chart |
| 7 | `/taxinfo` | 1 | Financial | Tax history (20+ years) |
| 8 | `/climate` | 1 | Location | Flood, fire, storm risk scores |
| 9 | `/walk_transit_bike` | 1 | Location | Walk, transit, bike scores |
| 10 | `/housing_market` | 1 | Market | ZHVI, appreciation trends |
| 11 | `/rental_market` | 1 | Market | Rental trends by bedroom |
| 12 | `/ownerinfo` | 1 | Contact | Owner name, agent info |
| 13 | `/custom_ae/searchbyaddress` | 1 | Search | Properties sorted by cash flow |

**External Service:**
- **Skip Tracing** - Uses separate API (skip-tracing-working-api)

---

### Three-Tier Settings System

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADMIN SETTINGS (Global)                       │
│  enrichment_admin_settings (singleton table)                    │
│  - Default values for all endpoints                             │
│  - Lock flags to prevent overrides                              │
│  - Permission flags (allow_user_overrides, etc.)                │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   COUNTY SETTINGS (Per-County)                   │
│  county_enrichment_settings (one row per county)                │
│  - Override defaults for specific counties                      │
│  - NULL values use admin defaults                               │
│  - Template presets (flipper, landlord, etc.)                   │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   USER PREFERENCES (Per-User)                    │
│  user_enrichment_preferences (one row per user+county)          │
│  - User customizations (if allowed by admin)                    │
│  - NULL values use county/admin defaults                        │
└─────────────────────────────────────────────────────────────────┘
```

---

### Template Presets

| Template | Endpoints | Cost | Best For |
|----------|-----------|------|----------|
| **Minimal** | 3 | 3 | Quick filtering (83 properties/month) |
| **Standard** | 7 | 7 | General analysis (35 properties/month) |
| **Flipper** | 7 | 7 | ARV/flipping focus (35 properties/month) |
| **Landlord** | 9 | 9 | Rental ROI focus (27 properties/month) |
| **Thorough** | 12 | 12 | Complete analysis (20 properties/month) |

---

### Key Investment Metrics

| Metric | Formula | Purpose |
|--------|---------|---------|
| **ARV** | Median of active comps | After-repair value |
| **Monthly Cash Flow** | Rent - All expenses | Rental profitability |
| **Cash on Cash Return** | (Annual CF / Cash Invested) × 100 | ROI on cash invested |
| **Cap Rate** | (NOI / Property Value) × 100 | unleveraged return |
| **MAO** | ARV - Repairs - Costs - Target Profit | Max bid price |
| **Flip Profit** | ARV - (Price + Repairs + Costs) | Expected profit from flip |

---

## Database Schema Summary

### Three Settings Tables

```sql
-- 1. Admin Settings (singleton)
enrichment_admin_settings (
    id,  -- Always 1
    endpoint_pro_byaddress BOOLEAN,
    endpoint_lock_pro_byaddress BOOLEAN,
    -- ... 13 endpoint pairs (value + lock)
    skip_trace_external_enabled BOOLEAN,
    skip_trace_external_lock BOOLEAN,
    -- Investment parameters
    inv_annual_appreciation DECIMAL(5,4),
    inv_mortgage_rate DECIMAL(5,4),
    -- ... 8 more parameters
    -- Permissions
    allow_user_overrides BOOLEAN,
    allow_user_templates BOOLEAN,
    allow_custom_investment_params BOOLEAN
);

-- 2. County Settings (per county)
county_enrichment_settings (
    id,
    county_id INT,
    county_name VARCHAR(100),
    state VARCHAR(2),
    -- Endpoint overrides (NULL = use admin)
    endpoint_pro_byaddress BOOLEAN,
    -- ... all 13 endpoints
    -- Investment overrides (NULL = use admin)
    inv_annual_appreciation DECIMAL(5,4),
    -- ... all investment params
    template_preset VARCHAR(50),
    UNIQUE(county_id, state)
);

-- 3. User Preferences (per user + county)
user_enrichment_preferences (
    id,
    user_id UUID,
    county_id INT,
    state VARCHAR(2),
    -- Endpoint overrides (NULL = use county/admin)
    endpoint_pro_byaddress BOOLEAN,
    -- ... all 13 endpoints
    -- Investment overrides (NULL = use county/admin)
    inv_annual_appreciation DECIMAL(5,4),
    -- ... all investment params
    template_preset VARCHAR(50),
    UNIQUE(user_id, county_id, state)
);
```

---

## API Routes Summary

### Admin Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/admin/settings` | GET | Get admin settings |
| `/api/admin/settings` | PUT | Update admin settings |
| `/api/admin/counties` | GET | List all county settings |
| `/api/admin/counties/{county_id}` | GET | Get county settings |
| `/api/admin/counties/{county_id}` | PUT | Update county settings |
| `/api/admin/counties/{county_id}` | DELETE | Delete county settings |
| `/api/admin/counties/{county_id}/apply-template` | POST | Apply template to county |

### User Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/users/{user_id}/preferences` | GET | Get user preferences |
| `/api/users/{user_id}/preferences/{county_id}` | GET | Get user prefs for county |
| `/api/users/{user_id}/preferences/{county_id}` | PUT | Update user prefs |
| `/api/users/{user_id}/preferences/{county_id}` | DELETE | Delete user prefs |

### Enrichment Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/enrichment/property` | POST | Enrich single property |
| `/api/enrichment/batch` | POST | Batch enrichment (async) |
| `/api/enrichment/job/{job_id}` | GET | Get job status |
| `/api/enrichment/property/{property_id}` | GET | Get enriched data |
| `/api/enrichment/property/{property_id}/skip-trace` | POST | Run skip trace |
| `/api/enrichment/config-preview` | GET | Preview settings for context |

### Utility Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/templates` | GET | List available templates |
| `/api/templates/{name}` | GET | Get template details |
| `/api/enrichment/quota` | GET | Check remaining quota |
| `/api/enrichment/health` | GET | Health check |

---

## Settings Resolution Logic

### Priority Order

1. **User Value** (if `allow_user_overrides = true` AND endpoint not locked)
2. **County Value** (if not locked at admin or county level)
3. **Admin Value** (default)

### Lock Behavior

| Lock Location | Effect |
|---------------|--------|
| `endpoint_lock_* = true` in Admin | County AND User CANNOT override |
| `endpoint_lock_* = true` in County | User CANNOT override (but county can override admin) |
| No locks | User > County > Admin priority applies |

### Example

```
Admin:   endpoint_similar = true,  endpoint_lock_similar = false
County:  endpoint_similar = false, endpoint_lock_similar = true
User:    endpoint_similar = true

Result:  endpoint_similar = FALSE (county lock prevents user override)
```

---

## Enrichment Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. RECEIVE REQUEST                                            │
│  Input: property_id, address, county_id, user_id                │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. RESOLVE SETTINGS                                           │
│  - Query admin, county, user settings                           │
│  - Apply lock logic                                             │
│  - Build enabled endpoint list                                  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. CHECK QUOTA                                                │
│  - Verify sufficient RapidAPI quota                             │
│  - Return 429 if exceeded                                       │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. EXECUTE ENDPOINTS                                          │
│  - Check cache first                                           │
│  - Call RapidAPI sequentially                                   │
│  - Parse and store data                                         │
│  - Continue on non-critical errors                              │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. CALCULATE METRICS                                           │
│  - ARV from comps                                               │
│  - Cash flow (if rental data)                                   │
│  - Investment metrics (if custom_ae enabled)                    │
│  - Risk scores                                                  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. RETURN RESULTS                                              │
│  - Enriched data                                                │
│  - Metrics calculated                                           │
│  - Endpoints called                                             │
│  - Requests used                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Skip Tracing

### Why External Service?

Zillow's skip tracing costs **50 requests per owner** (25 + 25), which would consume 20% of monthly quota.

**Solution:** Use separate skip-tracing API with its own quota.

### API Details

```
Service: skip-tracing-working-api.p.rapidapi.com
Endpoint 1: /search/byaddress
  - Input: street, citystatezip, page
  - Output: List of people at address with person_ids

Endpoint 2: /detailsbyid
  - Input: peo_id (from search)
  - Output: Full details (phones, emails, relatives, associates)
```

### Settings Integration

| Setting | Purpose |
|---------|---------|
| `enable_skip_trace_external` | Master on/off (admin) |
| `skip_trace_external_enabled` | Per-county/user enable |
| `skip_trace_external_lock` | Lock the setting |

---

## Typical Usage Patterns

### Pattern 1: Volume Filtering

```
1300 foreclosure properties
         │
         ▼
Run MINIMAL template (3 requests each)
         │
         ▼
Shortlist: ~200 properties
         │
         ▼
Run FLIPPER template on shortlist (7 requests each)
         │
         ▼
Final candidates: ~20 properties
         │
         ▼
Run THOROUGH template + skip trace
```

### Pattern 2: County-Specific Strategy

```
Urban County (high appreciation, high rents)
  → Use LANDLORD template
  → Enable climate, walk scores
  → Focus on rental metrics

Suburban County (stable, family-oriented)
  → Use STANDARD template
  → Focus on ARV and comps

Rural County (low cost, lower rents)
  → Use FLIPPER template
  → Focus on purchase price + ARV spread
```

---

## Cost Calculator

### Monthly Quota Planning

| Budget | Template | Properties | Requests |
|--------|----------|------------|----------|
| 30% (75) | Minimal | 25 | 75 |
| 70% (175) | Flipper/Landlord | 25 | 175 |
| 96% (240) | Thorough | 20 | 240 |

### Example Workflow

```
Month 1: Minimal on 100 properties = 300 requests (over quota)
  → Need to spread over multiple months or prioritize top 25

Month 2: Flipper on 25 shortlisted = 175 requests ✓

Month 3: Thorough on 5 finalists = 60 requests ✓
         + Skip trace on 5 = separate quota ✓

Total: 535 Zillow requests over 3 months (~178/month average)
```

---

## Security & Permissions

### Permission Matrix

| Admin Setting | Effect |
|---------------|--------|
| `allow_user_overrides` | Users can set preferences |
| `allow_user_templates` | Users can select templates |
| `allow_custom_investment_params` | Users can customize ROI formulas |

### Lock Priority

```
Admin Lock → County cannot override, User cannot override
County Lock → User cannot override (but County can override Admin)
No Lock → User > County > Admin priority
```

---

## Key Implementation Files

| File | Purpose |
|------|---------|
| `migrations/add_enrichment_settings.sql` | Database migration for settings tables |
| `webhook_server/zillow_enrichment.py` | Enrichment execution logic |
| `webhook_server/enrichment_routes.py` | FastAPI routes |
| `webhook_server/settings_service.py` | Settings resolution service |
| `webhook_server/skip_trace_service.py` | External skip tracing integration |

---

## Test Property

All documentation uses this test property:

```
Address: 1875 AVONDALE Circle, Jacksonville, FL 32205
ZPID: 44480538
Features: 7 bed, 9 bath, 7526 sqft, built 1927
Zestimate: $4,161,200
```

---

## Next Steps for Implementation

1. **Run Database Migration**
   ```bash
   psql -U postgres -d your_database -f migrations/add_enrichment_settings.sql
   ```

2. **Insert Default Admin Settings**
   - Use migration defaults
   - Or customize for your use case

3. **Implement Settings Service**
   - Settings resolution logic
   - Lock enforcement
   - Permission checks

4. **Implement Enrichment Service**
   - Endpoint execution
   - Data extraction
   - Metric calculation
   - Caching

5. **Implement Skip Trace Service**
   - External API integration
   - Separate quota tracking

6. **Create API Routes**
   - Settings CRUD
   - Enrichment endpoints
   - Template management

7. **Testing**
   - Test with sample property
   - Verify settings resolution
   - Check quota tracking

---

## Support & Resources

### RapidAPI Private-Zillow Documentation
- https://rapidapi.com/oneapiproject/api/zllw-working-api

### Skip Tracing API
- https://rapidapi.com/oneapiproject/api/skip-tracing-working-api

### RapidAPI Dashboard
- Check quota usage
- Manage API keys
- View request history
