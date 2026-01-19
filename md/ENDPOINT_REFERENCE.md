# RapidAPI private-zillow - Endpoint Reference

**Format:** Input → Output → Cost

---

## 1. PROPERTY LOOKUP

---

### `/autocomplete`
**Find property suggestions as you type**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `query` (string) | - | Address suggestions with ZPIDs | 1 |

**Example:** `query="123 Main St"` → List of matching addresses

---

### `/byaddress`
**Get full property details by address**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `propertyaddress` | - | ZPID, beds, baths, sqft, year built, lot size, zestimate, description | 1 |

**Example:** `propertyaddress="1875 AVONDALE Circle, Jacksonville, FL 32205"`

---

### `/byurl`
**Get property details from Zillow URL**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `url` | - | Same as /byaddress | 1 |

**Example:** `url="https://www.zillow.com/homedetails/...zpid/"`

---

### `/byzpid`
**Get property details by ZPID**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `zpid` | - | Same as /byaddress | 1 |

**Example:** `zpid="44471319"`

---

## 2. ENHANCED PROPERTY DETAILS

---

### `/pro/byaddress`
**Enhanced property details (more fields?)**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `propertyaddress` | - | Extended property data | 1 |

---

### `/pro/byurl`
**Enhanced details from URL**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `url` | - | Extended property data | 1 |

---

### `/client/byaddress`
**Custom endpoint, no images**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `propertyaddress` | - | Property data (no image URLs) | 1 |

---

## 3. COMPARABLES & SIMILAR PROPERTIES

---

### `/comparable_homes`
**Recent sales near property (CRITICAL FOR ARV)**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | - | List of recently sold nearby properties with: | 1 |
| `byzpid` | | - Sale prices | |
| `byurl` | | - Sale dates | |
| `byaddress` | | - Beds/baths/sqft | |
| | | - Distance from subject | |

---

### `/similar`
**Similar properties currently for sale**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | - | List of similar active listings with: | 1 |
| `byzpid` | | - List prices | |
| `byurl` | | - Property details | |
| `byaddress` | | - Days on market | |
| `bylotid` | | | |

---

### `/nearby`
**All nearby properties**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | - | Properties near the subject | 1 |
| `byzpid` | | | |
| `byurl` | | | |
| `byaddress` | | | |
| `bylotid` | | | |

---

## 4. IMAGES

---

### `/propimages`
**All property photos**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | - | List of image URLs: | 1 |
| `byzpid` | | - Exterior photos | |
| `byurl` | | - Interior room photos | |
| `byaddress` | | - Aerial/views | |
| | | - Virtual tours | |

---

### `/mask`
**Proxy/mask an image URL**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `url` | - | Raw image data (JPEG/PNG) | 2 |

---

## 5. PRICE & VALUE HISTORY

---

### `/pricehistory`
**Historical price changes**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | - | List of price events: | 1 |
| `byzpid` | | - Date | |
| `byurl` | | - Price event type (list/sold) | |
| `byaddress` | | - Amount | |
| | | - Source | |

---

### `/graph_charts?which=listing_price`
**10-year listing price chart**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | `recent_first` | Monthly listing prices (10 years) | 1 |
| `byzpid` | True/False | | |
| `byurl` | | | |
| `byaddress` | | | |

---

### `/graph_charts?which=zestimate_history`
**Zestimate over time**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | `recent_first` | Monthly Zillow estimate values | 1 |
| `byzpid` | True/False | | |
| `byurl` | | | |
| `byaddress` | | | |

---

### `/graph_charts?which=zestimate_percent_change`
**Zestimate percentage change**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | `recent_first` | Monthly percent change | 1 |
| `byzpid` | True/False | | |
| `byurl` | | | |
| `byaddress` | | | |

---

## 6. TAX INFORMATION

---

### `/taxinfo`
**Tax history and current amount**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | - | Tax payment history: | 1 |
| `byzpid` | | - Tax amount | |
| `byurl` | | - Year | |
| `byaddress` | | - Tax assessment | |

---

### `/graph_charts?which=tax_assessment`
**Tax assessment history**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | `recent_first` | Assessment amounts over time | 1 |
| `byzpid` | True/False | | |
| `byurl` | | | |
| `byaddress` | | | |

---

### `/graph_charts?which=tax_paid`
**Actual taxes paid history**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | `recent_first` | Tax payments over time | 1 |
| `byzpid` | True/False | | |
| `byurl` | | | |
| `byaddress` | | | |

---

## 7. OWNER & AGENT INFORMATION

---

### `/ownerinfo`
**Owner and listing agent details**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | - | - Owner name (if not hidden) | 1 |
| `byzpid` | | - Listing agent info | |
| `byurl` | | - Agent contact | |
| `byaddress` | | - Brokerage | |

---

### `/skip/byaddress`
**SKIP TRACE - Get owner phone/email ⚠️ EXPENSIVE**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `street` | `page` (1-10) | List of people at address: | **25** |
| `citystatezip` | | - Names | |
| | | - Person IDs (for details) | |
| | | - Ages (sometimes) | |

---

### `/skip/detailsbyid`
**Full person details from skip trace**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `peo_id` | - | - Phone numbers | **25** |
| (from skip/byaddress) | | - Email addresses | |
| | | - Relatives | |
| | | - Associates | |
| | | - Other addresses | |

**Total skip trace cost: 25 + 25 = 50 requests per owner**

---

### `/agent/search`
**Find agents in an area**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `location` | `agentName` | List of agents: | 1 |
| (city/zip) | `languages` | - Name | |
| | `isTopAgent` | - Profile URL | |
| | `specialties` | - encodedZuid | |
| | `priceRange` | - Review count | |
| | | - Listings/sold count | |

---

### `/agent/details`
**Get agent profile details**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | - | - Agent name | 1 |
| `agent_link` | | - Contact info | |
| `username` | | - Listings sold | |
| | | - Rating | |
| | | - Specialties | |

---

### `/agent/for_sale`
**Agent's current for-sale listings**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `encodedZuid` | `page` | Agent's active listings | 1 |
| (from agent/search) | | | |

---

### `/agent/sold_properties`
**Agent's sold history**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `encodedZuid` | `page` | Agent's sold properties | 1 |
| (from agent/search) | | | |

---

### `/agent/reviews`
**Agent reviews**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `encodedZuid` | `page` | Client reviews | 1 |
| (from agent/search) | `sortby` | | |

---

## 8. LOCATION & NEIGHBORHOOD

---

### `/walk_transit_bike`
**Walk, transit, and bike scores**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | - | - Walk score (0-100) | 1 |
| `byzpid` | | - Transit score | |
| `byurl` | | - Bike score | |
| `byaddress` | | - Description | |

---

### `/climate`
**Climate risk data (flood, fire, storm)**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | - | - Flood risk | 1 |
| `byzpid` | | - Fire risk | |
| `byurl` | | - Storm risk | |
| `byaddress` | | - Extreme heat | |
| | | - Future projections | |

---

### `/housing_market`
**Zillow Home Value Index (ZHVI) for area**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `search_query` | `home_type` | - ZHVI (typical home value) | 1 |
| (city/zip/USA) | `exclude_rentalMarketTrends` | - Percent change (1yr, 5yr, 10yr) | |
| | `exclude_neighborhoods_zhvi` | - Market status | |
| | | - Forecast | |

---

### `/rental_market`
**Rental trends for area**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `search_query` | `bedrooom_type` | - Median rent | 1 |
| (city/zip) | `home_type` | - Percent changes | |
| | | - Rental trends by bedroom count | |

---

## 9. SEARCH ENDPOINTS

---

### `/search/byaddress`
**Search properties by address with filters**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `location` | `bed_min`, `bed_max` | Up to 1000 properties matching: | 1 (2 if pageSize>500) |
| (city/zip/address) | `bathrooms` | | |
| | `listPriceRange` | | |
| | `homeType` | | |
| | `listingStatus` | | |
| | `daysOnZillow` | | |
| | `sortOrder` | | |
| | `page`, `pageSize` | | |

**listingStatus options:** `For_Sale`, `For_Rent`, `Sold`

---

### `/search/bycoordinates`
**Search by lat/lon with radius**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `latitude` | All same as /search/byaddress | Properties within radius | 1 (2 if pageSize>500) |
| `longitude` | | | |
| `radius` | | | |

---

### `/search/bymapbounds`
**Search within map rectangle**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `northLatitude` | All same as /search/byaddress | Properties on map | 1 (2 if pageSize>500) |
| `southLatitude` | | | |
| `eastLongitude` | | | |
| `westLongitude` | | | |

---

### `/search/bypolygon`
**Search within custom polygon**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `polygon` | All same as /search/byaddress | Properties in polygon | 1 (2 if pageSize>500) |
| (coord pairs) | | | |

---

### `/search/byurl`
**Search from Zillow URL**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `url` | `page` | Properties from Zillow search | 1 |
| (Zillow search URL) | | | |

---

### `/search/bymls`
**Lookup by MLS number**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `mlsid` | `listingStatus` | Property by MLS number | 1 |
| | `homeType` | | |

---

### `/search/offmarket`
**Find off-market properties**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `zipCode` | `includePending` | Properties not currently listed | 1 |
| | `includeClosed` | | |

---

### `/search/byaiprompt`
**Natural language search**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `ai_search_prompt` | `keywords` | Properties matching description | 1 |
| (e.g., "2 bed homes in Austin") | `page` | | |

---

## 10. CUSTOM SEARCH WITH INVESTMENT METRICS

---

### `/custom_ae/searchbyaddress`
**Search with pre-calculated cash flow!**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `location` | All same as /search/byaddress | Properties + **investment metrics**: | 1 |
| | `sortOrder` | - monthlyCashFlow | |
| | `v_aa` (annual appreciation) | - capRate | |
| | `v_cmr` (mortgage rate) | - cashOnCashReturn | |
| | `v_dpr` (down payment %) | | |
| | `v_ir` (insurance rate) | | |
| | `v_ltm` (loan term months) | | |
| | `v_mr` (maintenance rate) | | |
| | `v_pmr` (property mgmt rate) | | |
| | `v_ptr` (property tax rate) | | |
| | `v_rc` (renovation cost) | | |
| | `v_vr` (vacancy rate) | | |

**sortOrder options include:** `monthlyCashFlow_HighToLow`, `monthlyCashFlow_LowToHigh`

---

### `/custom_ad/byzpid`
**Property with custom data points**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | - | Property data + custom fields | 1 |
| `zpid` | | | |
| `url` | | | |
| `address` | | | |

---

### `/custom_ab/byaddress`
**Custom address endpoint**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `propertyaddress` | - | Property data (custom format) | 2 |

---

### `/client/byaddress`
**Lightweight property data**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `propertyaddress` | - | Property details (no images) | 1 |

---

## 11. APARTMENTS / MULTI-FAMILY

---

### `/lotid_from_address`
**Get LotID for apartment buildings**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `propertyaddress` | - | LotID (for multi-family) | 1 |

**Note:** Only returns LotID for apartments/buildings, not single-family homes

---

### `/apartment_details`
**Get building/apartment details**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| One of: | - | Building details: | 1 |
| `bylotid` | | - Unit count | |
| `byapturl` | | - Amenities | |
| | | - Building info | |

---

## 12. UTILITY ENDPOINTS

---

### `/myping`
**Check if API is working**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `check` (="Yes") | - | API status | 0 (or 1) |

---

### `/api_reqcount`
**Check your remaining request quota**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| `x_rapidapi_key` | - | Requests remaining this month | 0 |

---

### `/current_mortgage_rates`
**Current mortgage interest rates**

| Input Required | Input Optional | What You Get | Cost |
|----------------|----------------|--------------|------|
| None | - | Current 30-yr, 15-yr rates | 1 |

---

## COST SUMMARY TABLE

| Category | Endpoint | Cost |
|----------|----------|------|
| **Basic** | Most endpoints | 1 |
| **Skip trace** | `/skip/byaddress` | 25 |
| **Skip details** | `/skip/detailsbyid` | 25 |
| **Mask image** | `/mask` | 2 |
| **Custom AB** | `/custom_ab/byaddress` | 2 |
| **Large search** | Search with pageSize>500 | 2 |

---

## FORECLOSURE INVESTOR RECOMMENDATIONS

### MUST HAVE (Auto-Enrichment)

| Endpoint | Why | Cost |
|----------|-----|------|
| `/byaddress` | Get ZPID + basic details | 1 |
| `/comparable_homes` | Calculate ARV | 1 |
| `/propimages` | See condition | 1 |
| `/taxinfo` | Know ongoing costs | 1 |
| `/pricehistory` | Spot red flags | 1 |

**Total: 5 requests per property**

### NICE TO HAVE (On-Demand)

| Endpoint | Why | Cost |
|----------|-----|------|
| `/housing_market` | Area appreciating? | 1 |
| `/climate` | Flood/fire risk? | 1 |
| `/similar` | Competition? | 1 |
| `/ownerinfo` | Pre-auction contact? | 1 |

### EXPENSIVE (Use Selectively)

| Endpoint | Why | Cost |
|----------|-----|------|
| `/skip/byaddress` | Owner phone/email | 25 |
| `/skip/detailsbyid` | Full owner details | 25 |

**Total skip trace: 50 requests per owner**

---

## FREE (No Cost) - Use These First

- `/myping` - Check API status
- `/api_reqcount` - Check remaining quota
