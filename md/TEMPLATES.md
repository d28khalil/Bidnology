# Template Presets - Quick Configuration

**Version:** 1.0
**Date:** December 27, 2025

---

## Overview

Template presets are pre-configured endpoint combinations tailored for different real estate investment strategies. They provide a quick way to configure enrichment settings without manually toggling each endpoint.

---

## Table of Contents

- [Available Templates](#available-templates)
- [Template Comparison](#template-comparison)
- [Detailed Template Breakdowns](#detailed-template-breakdowns)
- [Creating Custom Templates](#creating-custom-templates)
- [Applying Templates](#applying-templates)

---

## Available Templates

| Template | Endpoints | Cost/Property | Best For |
|----------|-----------|---------------|----------|
| **Minimal** | 3 | 3 | Quick filtering |
| **Standard** | 7 | 7 | General analysis |
| **Flipper** | 7 | 7 | Flipping / ARV focus |
| **Landlord** | 9 | 9 | Rental properties |
| **Thorough** | 12 | 12 | Complete analysis |

---

## Template Comparison

```
COST vs THOROUGHNESS

Thorough (12 endpoints)  ████████████████████  $12/property  ~20 properties/month
                         │
                         │
Landlord (9 endpoints)   ██████████████░░░░░░  $9/property   ~27 properties/month
                         │
                         │
Standard (7 endpoints)   ██████████░░░░░░░░░░  $7/property   ~35 properties/month
Flipper (7 endpoints)    ██████████░░░░░░░░░░  $7/property   ~35 properties/month
                         │
                         │
Minimal (3 endpoints)    ████░░░░░░░░░░░░░░░░  $3/property   ~83 properties/month

QUOTA: 250 requests/month
```

---

## Detailed Template Breakdowns

### 1. Minimal Template

**Purpose:** Quick filtering to eliminate obviously bad deals.

**Cost:** 3 requests per property (~83 properties/month)

**Endpoints Enabled:**

| Endpoint | Why |
|----------|-----|
| `endpoint_pro_byaddress` | Get ZPID + basic info (beds, baths, sqft) |
| `endpoint_custom_ad_byzpid` | Photos to assess condition |
| `endpoint_pricehistory` | Check for price red flags |

**Metrics Available:**
- Basic property info (beds, baths, sqft, year built)
- Zestimate
- Property photos (100+)
- Price history

**Metrics NOT Available:**
- Comps / ARV
- Tax info
- Climate risk
- Rental data
- Investment calculations

**Use Case:**
- First pass on 100+ properties
- Eliminate properties with obvious issues
- Identify candidates for deeper analysis

**Example Flow:**
```
1. User loads 1300 foreclosure properties
2. Minimal enrichment runs (3 × 1300 = 3900 requests - need multiple months or prioritize)
3. System flags:
   - Properties with huge price drops (red flag)
   - Properties in terrible condition (from photos)
   - Properties outside target size range
4. User gets shortlist of ~200 properties
5. User runs Standard/Flipper/Landlord on shortlist
```

---

### 2. Standard Template

**Purpose:** Balanced analysis for general property evaluation.

**Cost:** 7 requests per property (~35 properties/month)

**Endpoints Enabled:**

| Endpoint | Why |
|----------|-----|
| `endpoint_pro_byaddress` | Basic info + ZPID |
| `endpoint_custom_ad_byzpid` | Photos + details |
| `endpoint_similar` | Active listings for comparison |
| `endpoint_pricehistory` | Price trends |
| `endpoint_taxinfo` | Tax burden |
| `endpoint_taxinfo` | Ongoing costs |
| `endpoint_ownerinfo` | Owner contact |

**Metrics Available:**
- All Minimal metrics, plus:
- Comparable properties (active listings)
- Tax history and current amount
- Owner information
- ARV range (from comps)

**Metrics NOT Available:**
- Climate risk
- Location scores
- Market trends
- Rental trends
- Investment ROI calculations

**Use Case:**
- Good for preliminary deal analysis
- Enough info to make bid/no-bid decision
- Suitable for mixed-use investors

---

### 3. Flipper Template

**Purpose:** ARV-focused analysis for house flippers.

**Cost:** 7 requests per property (~35 properties/month)

**Endpoints Enabled:**

| Endpoint | Why |
|----------|-----|
| `endpoint_pro_byaddress` | Basic info + purchase price |
| `endpoint_custom_ad_byzpid` | Condition assessment (photos) |
| `endpoint_similar` | **ARV calculation** (critical!) |
| `endpoint_nearby` | Neighborhood context |
| `endpoint_pricehistory` | Market movement |
| `endpoint_taxinfo` | Holding costs |
| `endpoint_ownerinfo` | Pre-auction contact |

**Metrics Available:**
- All Standard metrics, plus:
- Nearby properties (wider comp pool)
- ARV from active listings
- Price-to-ARV spread
- Maximum Allowable Offer (MAO)
- Fix & flip profit projection

**Flipper-Specific Calculations:**
```
ARV = Median of similar active listings
Repair Cost = Based on photos + year built
MAO = ARV - Repairs - Closing Costs - Target Profit (30%)
Flip Profit = ARV - (Purchase Price + Repairs + Costs)
```

**Use Case:**
- Shortlist properties for auction bidding
- Calculate maximum bid to hit ROI targets
- Identify owner for pre-auction deals

**Decision Framework:**
```
If ARV Spread > 50% → GREEN (bid aggressively)
If ARV Spread 30-50% → YELLOW (bid conservatively)
If ARV Spread < 30% → RED (don't bid)
```

---

### 4. Landlord Template

**Purpose:** Rental ROI analysis for buy-and-hold investors.

**Cost:** 9 requests per property (~27 properties/month)

**Endpoints Enabled:**

| Endpoint | Why |
|----------|-----|
| `endpoint_pro_byaddress` | Rent Zestimate (critical!) |
| `endpoint_custom_ad_byzpid` | Condition for rentability |
| `endpoint_similar` | Rental comps |
| `endpoint_pricehistory` | Area stability |
| `endpoint_taxinfo` | Expenses |
| `endpoint_climate` | **Insurance costs** (flood/fire risk) |
| `endpoint_walk_transit_bike` | **Renter appeal** (walkability) |
| `endpoint_housing_market` | Area appreciation |
| `endpoint_rental_market` | Rental trends by bedroom |

**Metrics Available:**
- All Standard metrics, plus:
- Rent Zestimate
- Climate risk scores (affects insurance)
- Walk/transit/bike scores (affects rentability)
- Market health (appreciation trends)
- Rental market trends
- Monthly cash flow projection
- Cash on cash return
- Cap rate
- 5-year total return

**Landlord-Specific Calculations:**
```
Monthly Cash Flow = Rent - (Mortgage + Taxes + Insurance + Maintenance + Management + Vacancy)
Cash on Cash Return = (Annual Cash Flow / Cash Invested) × 100
Cap Rate = (NOI / Property Value) × 100
5-Year Return = (5-Year Cash Flow + Appreciation) / Down Payment
```

**Use Case:**
- Evaluate rental properties
- Long-term hold decisions
- Market selection (which areas to invest in)

**Decision Framework:**
```
If Cash Flow > $500 AND Cash on Cash > 8% → GREEN
If Cash Flow > $0 AND Cash on Cash > 5% → YELLOW
If Cash Flow < $0 OR Cash on Cash < 5% → RED
```

---

### 5. Thorough Template

**Purpose:** Complete analysis for major investment decisions.

**Cost:** 12 requests per property (~20 properties/month)

**Endpoints Enabled:**

| Endpoint | Why |
|----------|-----|
| `endpoint_pro_byaddress` | Everything |
| `endpoint_custom_ad_byzpid` | Everything |
| `endpoint_similar` | Everything |
| `endpoint_nearby` | Everything |
| `endpoint_pricehistory` | Everything |
| `endpoint_graph_listing_price` | 10-year chart |
| `endpoint_taxinfo` | Everything |
| `endpoint_climate` | Everything |
| `endpoint_walk_transit_bike` | Everything |
| `endpoint_housing_market` | Everything |
| `endpoint_rental_market` | Everything |
| `endpoint_ownerinfo` | Everything |

**Metrics Available:**
- ALL metrics from all other templates
- Long-term price charts (10 years)
- Complete risk assessment
- Both flipping AND rental calculations

**Use Case:**
- Final due diligence before auction
- Major investment decisions
- Partnerships requiring full analysis

---

## Template Endpoint Matrix

| Endpoint | Minimal | Standard | Flipper | Landlord | Thorough |
|----------|---------|----------|---------|----------|----------|
| `pro_byaddress` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `custom_ad_byzpid` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `similar` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `nearby` | ❌ | ❌ | ✅ | ❌ | ✅ |
| `pricehistory` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `graph_listing_price` | ❌ | ❌ | ❌ | ❌ | ✅ |
| `taxinfo` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `climate` | ❌ | ❌ | ❌ | ✅ | ✅ |
| `walk_transit_bike` | ❌ | ❌ | ❌ | ✅ | ✅ |
| `housing_market` | ❌ | ❌ | ❌ | ✅ | ✅ |
| `rental_market` | ❌ | ❌ | ❌ | ✅ | ✅ |
| `ownerinfo` | ❌ | ✅ | ✅ | ❌ | ✅ |
| **Total** | **3** | **7** | **7** | **9** | **12** |

---

## Creating Custom Templates

Users and admins can create custom templates by:

1. **Manual Endpoint Selection**
   - Toggle individual endpoints on/off
   - Save as a named preset

2. **Clone Existing Template**
   - Start with Flipper, Landlord, etc.
   - Add/remove endpoints
   - Save with new name

3. **Custom Investment Parameters**
   - Set ROI formula inputs
   - Configure appreciation rate, mortgage rate, etc.
   - Save with template

### Custom Template Example: "Beach Rental"

**Use Case:** Vacation rental analysis

**Endpoints:**
```
pro_byaddress: ON
custom_ad_byzpid: ON
similar: ON
pricehistory: ON
taxinfo: ON
climate: ON (critical for flood risk!)
housing_market: ON
walk_transit_bike: ON (beach access)
ownerinfo: ON
```

**Investment Params:**
```
annual_appreciation: 0.05 (beach properties appreciate faster)
mortgage_rate: 0.05 (higher rate for investment properties)
vacancy_rate: 0.15 (higher vacancy for vacation rentals)
property_mgmt_rate: 0.20 (vacation rental management costs more)
```

---

## Applying Templates

### Apply to County

**Request:**
```http
POST /api/admin/counties/25290/apply-template
Content-Type: application/json

{
  "template": "flipper"
}
```

**Result:** All county settings updated to match Flipper template.

### Apply to User

**Request:**
```http
PUT /api/users/{user_id}/preferences/25290
Content-Type: application/json

{
  "state": "FL",
  "template_preset": "landlord"
}
```

**Result:** User preferences updated to match Landlord template (if allowed by admin).

### Apply with Overrides

After applying a template, individual settings can still be modified:

```http
PUT /api/admin/counties/25290
Content-Type: application/json

{
  "endpoint_climate": true  // Add climate to Flipper template
}
```

---

## Template Configurations (SQL)

### Minimal Template

```sql
INSERT INTO county_enrichment_settings (county_id, county_name, state,
    endpoint_pro_byaddress,
    endpoint_custom_ad_byzpid,
    endpoint_pricehistory,
    template_preset
) VALUES (
    25290, 'Duval', 'FL',
    true, true, true,
    'minimal'
);
```

### Flipper Template

```sql
INSERT INTO county_enrichment_settings (county_id, county_name, state,
    endpoint_pro_byaddress,
    endpoint_custom_ad_byzpid,
    endpoint_similar,
    endpoint_nearby,
    endpoint_pricehistory,
    endpoint_taxinfo,
    endpoint_ownerinfo,
    template_preset
) VALUES (
    25290, 'Duval', 'FL',
    true, true, true, true, true, true, true,
    'flipper'
);
```

### Landlord Template

```sql
INSERT INTO county_enrichment_settings (county_id, county_name, state,
    endpoint_pro_byaddress,
    endpoint_custom_ad_byzpid,
    endpoint_similar,
    endpoint_pricehistory,
    endpoint_taxinfo,
    endpoint_climate,
    endpoint_walk_transit_bike,
    endpoint_housing_market,
    endpoint_rental_market,
    template_preset
) VALUES (
    25290, 'Duval', 'FL',
    true, true, true, true, true, true, true, true, true,
    'landlord'
);
```

### Thorough Template

```sql
INSERT INTO county_enrichment_settings (county_id, county_name, state,
    endpoint_pro_byaddress,
    endpoint_custom_ad_byzpid,
    endpoint_similar,
    endpoint_nearby,
    endpoint_pricehistory,
    endpoint_graph_listing_price,
    endpoint_taxinfo,
    endpoint_climate,
    endpoint_walk_transit_bike,
    endpoint_housing_market,
    endpoint_rental_market,
    endpoint_ownerinfo,
    template_preset
) VALUES (
    25290, 'Duval', 'FL',
    true, true, true, true, true, true, true, true, true, true, true, true,
    'thorough'
);
```

---

## Template Selection Guide

### Question Tree

```
Are you flipping or holding?
│
├─ Flipping → Use FLIPPER template
│             - Need ARV from comps
│             - Don't need rental data
│
└─ Holding (rental) → Use LANDLORD template
                      - Need rent estimates
                      - Need cash flow calculations
                      - Climate matters (insurance costs)


How many properties to analyze?
│
├─ 100+ → Use MINIMAL first, then upgrade
│          - Quick filter to eliminate bad deals
│          - Apply deeper templates to shortlist
│
├─ 20-50 → Use STANDARD or FLIPPER/LANDLORD
│           - Balanced depth vs cost
│
└─ < 20 (major deals) → Use THOROUGH
                         - Complete analysis
                         - Worth the extra requests
```

---

## Template Cost Calculator

### Monthly Budget Planning

| Monthly Budget | Template | Properties/Month | Best For |
|----------------|----------|------------------|----------|
| ~75 requests (30%) | Minimal | 25 | Large volume filtering |
| ~175 requests (70%) | Flipper/Landlord | 25 | Focused analysis |
| ~240 requests (96%) | Thorough | 20 | Due diligence |

### Example Workflow

```
Month 1:
- Load 1300 foreclosure properties
- Run MINIMAL on top 100 (based on basic filters)
- Cost: 300 requests

Month 2-3:
- Run FLIPPER on shortlisted 50
- Cost: 350 requests

Month 4:
- Run THOROUGH on final 10 candidates
- Cost: 120 requests

Total: 770 requests over 4 months (~192/month)
Result: 10 fully-vetted properties for auction bidding
```

---

## Recommended Default Templates

### By County Type

| County Type | Recommended Template | Reason |
|-------------|---------------------|--------|
| Urban / High Cost | Landlord | Rental demand, appreciation |
| Suburban / Stable | Standard | Balanced flipping/rental |
| Rural / Low Cost | Flipper | Cash flow less important, ARV focus |
| Coastal | Landlord (+climate) | Flood risk critical |
| College Town | Landlord | Strong rental market |

### By User Type

| User Type | Recommended Template |
|-----------|---------------------|
| Beginner Investor | Standard |
| House Flipper | Flipper |
| Landlord | Landlord |
| Wholesaler | Minimal (volume focus) |
| Real Estate Agent | Standard (client needs vary) |
| Investment Fund | Thorough (due diligence required) |
