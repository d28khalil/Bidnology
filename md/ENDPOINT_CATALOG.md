# RapidAPI private-zillow - Complete Endpoint Catalog

**Goal:** Identify BEST endpoints for foreclosure auction analysis from real estate investor perspective

---

## ALL AVAILABLE ENDPOINTS (Categorized)

---

### Category 1: PROPERTY LOOKUP (Find the Property)

| Endpoint | Params | Returns | Investor Value |
|----------|--------|---------|-----------------|
| `/autocomplete` | `query` | Address suggestions, ZPIDs | Low - UX helper |
| `/byaddress` | `propertyaddress` | **Full property details + ZPID** | **CRITICAL** - Entry point |
| `/byurl` | `url` | Property details from Zillow URL | Medium - URL alternative |
| `/byzpid` | `zpid` | Property details from ZPID | **CRITICAL** - After lookup |

**Foreclosure Verdict:** `/byaddress` is REQUIRED - gives us ZPID to unlock all other endpoints

---

### Category 2: PROPERTY DETAILS (Core Data)

| Endpoint | Params | Returns | Investor Value |
|----------|--------|---------|-----------------|
| `/pro/byurl` | `url` | Property details (pro version) | Medium - Duplicate of byzpid? |
| `/pro/byaddress` | `propertyaddress` | **Enhanced property details** | **HIGH** - May have more fields |
| `/custom_ae/byaddress` | Search params | Custom search with investment metrics | **VERY HIGH** - Has monthlyCashFlow sort! |
| `/client/byaddress` | `propertyaddress` | Custom endpoint (no images) | Medium - Lightweight? |

**Foreclosure Verdict:** Need to test `/pro/byaddress` vs `/custom_ae/byaddress` - the latter has investment metrics built-in!

---

### Category 3: COMPARABLES & SIMILAR (ARV Calculation)

| Endpoint | Params | Returns | Investor Value |
|----------|--------|---------|-----------------|
| `/comparable_homes` | `byzpid/byurl/byaddress` | **Recent sales comps** | **CRITICAL** - ARV calculation |
| `/similar` | `byzpid/byurl/byaddress/bylotid` | Similar listed properties | **HIGH** - Active competition |
| `/nearby` | `byzpid/byurl/byaddress/bylotid` | Nearby properties | Medium - Area analysis |

**Foreclosure Verdict:**
- `/comparable_homes` = REQUIRED for ARV (After Repair Value)
- `/similar` = HIGH for seeing active listings (competition)
- `/nearby` = OPTIONAL for neighborhood context

---

### Category 4: IMAGES & VISUAL (Condition Assessment)

| Endpoint | Params | Returns | Investor Value |
|----------|--------|---------|-----------------|
| `/propimages` | `byzpid/byurl/byaddress` | **All property photos** | **HIGH** - Visual condition |
| `/mask` | `url` | Masked/proxied image | Low - Bandwidth saver |

**Foreclosure Verdict:** `/propimages` = HIGH - Photos show condition (critical for repair estimates)

---

### Category 5: PRICE & VALUE HISTORY (Trends)

| Endpoint | Params | Returns | Investor Value |
|----------|--------|---------|-----------------|
| `/pricehistory` | `byzpid/byurl/byaddress` | **Historical price changes** | **HIGH** - Market movement |
| `/graph_charts?which=listing_price` | `byzpid/byurl/byaddress` | 10-year listing price chart | **HIGH** - Long-term trend |
| `/graph_charts?which=zestimate_history` | `byzpid/byurl/byaddress` | Zestimate over time | **HIGH** - Zillow's valuation |
| `/graph_charts?which=zestimate_percent_change` | `byzpid/byurl/byaddress` | Percent change trends | Medium - Growth rate |

**Foreclosure Verdict:**
- `/pricehistory` = HIGH - Shows actual sale/listing history
- `/graph_charts?which=listing_price` = HIGH - 10-year view
- `zestimate_history` = MEDIUM - Secondary indicator

---

### Category 6: TAX & ASSESSMENT (Cost Analysis)

| Endpoint | Params | Returns | Investor Value |
|----------|--------|---------|-----------------|
| `/taxinfo` | `byzpid/byurl/byaddress` | **Tax history & amounts** | **HIGH** - Ongoing costs |
| `/graph_charts?which=tax_assessment` | `byzpid/byurl/byaddress` | Assessment history | **HIGH** - Tax basis trends |
| `/graph_charts?which=tax_paid` | `byzpid/byurl/byaddress` | Taxes paid over time | **HIGH** - Actual cost |

**Foreclosure Verdict:**
- `/taxinfo` = HIGH - Current tax bill (critical for ROI)
- `/graph_charts?which=tax_assessment` = MEDIUM - Historical context
- `/graph_charts?which=tax_paid` = MEDIUM - Payment history

---

### Category 7: OWNER & AGENT INFO (Deal Sourcing)

| Endpoint | Params | Returns | Investor Value |
|----------|--------|---------|-----------------|
| `/ownerinfo` | `byzpid/byurl/byaddress` | **Owner details, agent info** | **HIGH** - Pre-sale contact |
| `/skip/byaddress` | `street, citystatezip, page` | **Skip tracing (phone, email)** | **VERY HIGH** - Direct contact |
| `/skip/detailsbyid` | `peo_id` | Full person details | HIGH - After skip trace |
| `/agent/search` | `location, filters...` | Find agents by area | MEDIUM - Find buyer's agent |
| `/agent/details` | `agent_link` or `username` | Agent profile | LOW - Nice to have |
| `/agent/for_sale` | `encodedZuid` | Agent's listings | MEDIUM - See inventory |
| `/agent/sold_properties` | `encodedZuid` | Agent's sold history | MEDIUM - Track record |
| `/agent/reviews` | `encodedZuid` | Agent reviews | LOW - Vetting |

**Foreclosure Verdict:**
- `/ownerinfo` = HIGH - See if bank-owned, owner-occupied
- `/skip/byaddress` = **VERY HIGH (on-demand)** - Get owner phone/email for off-market deals
- Agent endpoints = LOWER priority (post-acquisition)

---

### Category 8: LOCATION & NEIGHBORHOOD (Area Analysis)

| Endpoint | Params | Returns | Investor Value |
|----------|--------|---------|-----------------|
| `/walk_transit_bike` | `byzpid/byurl/byaddress` | **Walk/transit/bike scores** | **MEDIUM** - Renter appeal |
| `/climate` | `byzpid/byurl/byaddress` | Climate risk data | **GROWING** - Insurance/flood |
| `/housing_market` | `search_query, home_type` | **ZHVI market trends** | **HIGH** - Area appreciation |
| `/rental_market` | `search_query, filters` | Rental trends by bedroom count | **HIGH** - Rental ROI |

**Foreclosure Verdict:**
- `/walk_transit_bike` = MEDIUM - Location score
- `/climate` = **GROWING IMPORTANCE** - Flood/fire risk affects insurance
- `/housing_market` = HIGH - Market health
- `/rental_market` = HIGH - If holding as rental

---

### Category 9: SEARCH & DISCOVERY (Finding Deals)

| Endpoint | Params | Returns | Investor Value |
|----------|--------|---------|-----------------|
| `/search/byaddress` | **Full search filters** | Properties matching criteria | **HIGH** - Find foreclosures |
| `/search/bycoordinates` | lat, lon, radius, filters | Properties within radius | **HIGH** - Map search |
| `/search/bymapbounds` | Map bounds, filters | Properties on map | **HIGH** - Area sweep |
| `/search/bypolygon` | polygon coordinates, filters | Properties in shape | **HIGH** - Custom area |
| `/search/byurl` | url, page | Properties from Zillow URL | MEDIUM - URL-based |
| `/search/bymls` | `mlsid` | Property by MLS number | MEDIUM - MLS lookup |
| `/search/offmarket` | `zipCode` | **Off-market properties** | **VERY HIGH** - Hidden inventory |
| `/search/byaiprompt` | `ai_search_prompt` | Natural language search | **LOW** - Gimmicky |
| Custom search endpoints | Investment metrics | Pre-calculated ROI | **VERY HIGH** |

**Foreclosure Verdict:**
- Search endpoints = NOT for our use case (we already have sheriff sale listings)
- EXCEPT `/search/offmarket` = HIGH for finding pre-foreclosure opportunities
- `/custom_ae/searchbyaddress` = VERY HIGH - Has monthlyCashFlow calculation built-in!

---

### Category 10: APARTMENT/MULTI-FAMILY (Specific Property Type)

| Endpoint | Params | Returns | Investor Value |
|----------|--------|---------|-----------------|
| `/lotid_from_address` | `propertyaddress` | Get LotID for apartments | MEDIUM - Multi-family only |
| `/apartment_details` | `bylotid/byapturl` | Building details | MEDIUM - Multi-family |

**Foreclosure Verdict:** SKIP unless targeting multi-family specifically

---

### Category 11: UTILITIES & META

| Endpoint | Params | Returns | Investor Value |
|----------|--------|---------|-----------------|
| `/myping` | `check` | API status check | NONE - Monitoring |
| `/api_reqcount` | `x_rapidapi_key` | **Request count remaining** | **HIGH** - Quota tracking |
| `/current_mortgage_rates` | None | Current mortgage rates | **HIGH** - Financing cost |

**Foreclosure Verdict:**
- `/api_reqcount` = USEFUL - Track quota
- `/current_mortgage_rates` = HIGH - Calculate financing costs

---

## FORECLOSURE INVESTOR DECISION FRAMEWORK

### What an Investor Needs to Know at Auction:

**MUST HAVE (Bid/No-Bid Decision):**
1. ✅ What's the property? (basic details, beds/baths/sqft)
2. ✅ What's it worth after repairs? (ARV from comps)
3. ✅ What are the comps? (recent nearby sales)
4. ✅ What's the condition? (photos)
5. ✅ What are the taxes? (ongoing cost)

**NICE TO HAVE (Shortlist Properties):**
6. Price history (was it over-inflated?)
7. Market trends (is area appreciating?)
8. Climate risk (flood zone? insurance cost?)
9. Owner info (can I buy before auction?)

**OPTIONAL (Deep Dive):**
10. Walk score (renter appeal)
11. Detailed tax history
12. Agent info

---

## RECOMMENDED ENDPOINT SELECTION

### AUTO-ENRICHMENT (Run on EVERY foreclosure)

| Priority | Endpoint | Why | Request Cost |
|----------|----------|-----|--------------|
| 1 | `/byaddress` | Get ZPID + basic details | 1 |
| 2 | `/comparable_homes` | **ARV calculation** | 1 |
| 3 | `/propimages` | Visual condition | 1 |
| 4 | `/taxinfo` | Current tax burden | 1 |
| 5 | `/pricehistory` | Recent price changes | 1 |

**Total: 5 requests per property** = ~50 properties for 250 request quota

### ON-DEMAND ENRICHMENT (Run on SHORTLIST)

| Priority | Endpoint | Why | Request Cost |
|----------|----------|-----|--------------|
| 1 | `/housing_market` | Area appreciation trend | 1 |
| 2 | `/climate` | Flood/fire risk | 1 |
| 3 | `/skip/byaddress` | Owner contact for pre-auction deal | 25 ⚠️ |
| 4 | `/similar` | Active competition | 1 |

**Note:** Skip tracing costs 25 requests! Use selectively.

---

## ALTERNATIVE: CUSTOM ENDPOINTS

The `/custom_ae/` endpoints have **pre-calculated investment metrics**:
- `monthlyCashFlow` sort
- Built-in ROI calculations
- May eliminate need for separate calls

**MUST TEST:** Does `/custom_ae/byaddress` include comps, images, tax info?

If yes → Could reduce auto-enrichment to **1-2 requests** per property!

---

## NEXT STEPS

1. **Test 1 property** using current 14-endpoint plan
2. **Test 1 property** using `/custom_ae/byaddress` only
3. **Compare data completeness**
4. **Decide which approach gives better ROI**

---

## QUESTIONS FOR TESTING

1. Does `/pro/byaddress` return MORE data than `/byaddress`?
2. Does `/custom_ae/byaddress` include comps and images?
3. Which endpoints have overlapping data?
4. What's the actual schema of each response?
5. Can we reduce request count with custom endpoints?
