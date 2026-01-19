# Zillow RapidAPI Endpoints - Final Selection

**Last Updated:** December 27, 2025
**Status:** Tested and Confirmed Working

---

## Quick Reference: All Endpoints

| # | Endpoint | Cost | Category | Provides | Best For |
|---|----------|------|----------|----------|----------|
| 1 | `/pro/byaddress` | 1 | Core | ZPID, beds, baths, sqft, yearBuilt, zestimate, **rentZestimate** | **ALL** - Entry point |
| 2 | `/custom_ad/byzpid` | 1 | Core | **100+ photos**, property details, custom fields | **ALL** - Condition assessment |
| 3 | `/similar` | 1 | Comps | 20+ active listings with prices, beds/baths/sqft | **Flippers** - ARV calculation |
| 4 | `/nearby` | 1 | Comps | All nearby properties | Neighborhood context |
| 5 | `/pricehistory` | 1 | History | Price changes over time | Red flag detection |
| 6 | `/graph_charts?which=listing_price` | 1 | History | 10-year listing price chart | Long-term trend visualization |
| 7 | `/taxinfo` | 1 | Financial | Tax history (20+ years), current amount | Expense calculation |
| 8 | `/climate` | 1 | Location | Flood, fire, storm risk scores | Insurance/risk assessment |
| 9 | `/walk_transit_bike` | 1 | Location | Walk (0-100), transit, bike scores | Rental appeal |
| 10 | `/housing_market` | 1 | Market | ZHVI, appreciation trends, forecast | Area analysis |
| 11 | `/rental_market` | 1 | Market | Rental trends by bedroom count | Landlords |
| 12 | `/ownerinfo` | 1 | Contact | Owner name, listing agent info | Pre-auction contact |
| 13 | `/custom_ae/searchbyaddress` | 1 | Search | Properties sorted by **cash flow** | Deal discovery |

**External Service (Separate API):**
| # | Service | Quota | Provides |
|---|---------|-------|----------|
| 14 | `skip-tracing-working-api` | Separate | Owner phone, email, relatives |

---

## Removed / Redundant Endpoints

| Endpoint | Why Removed |
|----------|--------------|
| `/byaddress` | Same as `/pro/byaddress` |
| `/byzpid` | Same as `/pro/byaddress` |
| `/comparable_homes` | Returns empty array - unreliable |
| `/propimages` | Built into `/custom_ad/byzpid` |
| `/graph_charts` variants | Covered by `/pricehistory` + custom calculation |
| `/skip/byaddress` | Using external service instead |
| `/skip/detailsbyid` | Using external service instead |

---

## Input Parameters

### `/pro/byaddress`
```
propertyaddress (required): "1875 AVONDALE Circle, Jacksonville, FL 32205"
```

### `/custom_ad/byzpid`
```
zpid (required): "44480538"
```

### `/similar`
```
byzpid (required): "44480538"
```

### `/nearby`
```
byzpid (required): "44480538"
```

### `/pricehistory`
```
byzpid (required): "44480538"
```

### `/graph_charts`
```
which (required): "listing_price"
byzpid (required): "44480538"
recent_first (optional): "True" | "False"
```

### `/taxinfo`
```
byzpid (required): "44480538"
```

### `/climate`
```
byzpid (required): "44480538"
```

### `/walk_transit_bike`
```
byzpid (required): "44480538"
```

### `/housing_market`
```
search_query (required): "Jacksonville, FL" or "32205" or "USA"
home_type (optional): "All_Homes" | "Single_Family" | "Condos/Co-ops"
exclude_rentalMarketTrends (optional): true
exclude_neighborhoods_zhvi (optional): true
```

### `/rental_market`
```
search_query (required): "Jacksonville, FL" or "32205"
bedrooom_type (optional): "All_Bedrooms" | "Studio" | "1_Bedroom" | "2_Bedroom"
home_type (optional): "All_Property_Types" | "Houses" | "Apartments_and_Condos"
```

### `/ownerinfo`
```
byzpid (required): "44480538"
```

### `/custom_ae/searchbyaddress`
```
location (required): "32205"
listingStatus (required): "For_Sale"
sortOrder (optional): "monthlyCashFlow_HighToLow" | "Price_Low_to_High"
bed_min, bed_max, bathrooms, etc.

# Investment calculation parameters (optional)
v_aa: 0.03 (annual appreciation)
v_cmr: 4.5 (mortgage rate %)
v_dpr: 0.2 (down payment %)
v_ir: 0.015 (insurance rate)
v_ltm: 360 (loan term months)
v_mr: 0.1 (maintenance rate)
v_pmr: 0.1 (property management rate)
v_ptr: 0.012 (property tax rate)
v_rc: 25000 (renovation cost)
v_vr: 0.05 (vacancy rate)
```

---

## Response Structures

### `/pro/byaddress` Response
```json
{
  "message": "200: Success",
  "PropertyAddress": {
    "streetAddress": "1875 AVONDALE Circle",
    "zipcode": "32205",
    "city": "Jacksonville",
    "state": "FL",
    "subdivision": "Avondale"
  },
  "zestimate": 4161200,
  "Bedrooms": 7,
  "Bathrooms": 9,
  "Area(sqft)": 7526,
  "PropertyZPID": "44480538",
  "Price": 4250000,
  "yearBuilt": 1927,
  "daysOnZillow": 304,
  "PropertyZillowURL": "https://www.zillow.com/homedetails/44480538_zpid/"
}
```

### `/similar` Response
```json
{
  "message": "200: Success",
  "similar_properties": {
    "name": "Similar homes",
    "placement": "NEIGHBORHOOD",
    "propertyDetails": [
      {
        "zpid": "44480540",
        "price": 3950000,
        "currency": "USD",
        "bedrooms": 4,
        "bathrooms": 6,
        "livingArea": 4876,
        "address": {
          "streetAddress": "1878 AVONDALE Circle",
          "city": "Jacksonville",
          "state": "FL",
          "zipcode": "32205"
        },
        "homeStatus": "FOR_SALE",
        "hdpUrl": "/homedetails/1878-Avondale-Cir-Jacksonville-FL-32205/44480540_zpid/"
      }
      // ... 20+ properties
    ]
  }
}
```

### `/custom_ae/searchbyaddress` Response
```json
{
  "message": "200",
  "resultsCount": {
    "totalMatchingCount": 161
  },
  "searchResults": [
    {
      "property": {
        "zpid": "44468328",
        "price": {"value": 5000},
        "bedrooms": 3,
        "bathrooms": 2,
        "livingArea": 1288,
        "estimates": {
          "zestimate": 199600,
          "rentZestimate": 1500
        }
      },
      "rental_metrics": {
        "monthlyCashFlow": 1093.75,
        "cashOnCashReturn": 50.5,
        "capRate": 267.3,
        "roi": 50.5,
        "totalReturn5yr": 268.3
      }
    }
  ]
}
```

---

## Cost Summary

| Tier | Endpoints | Cost/Property | Properties/Month (250 quota) |
|------|-----------|---------------|------------------------------|
| Minimal | 3 | 3 | ~83 |
| Standard | 7 | 7 | ~35 |
| Thorough | 12 | 12 | ~20 |

**Skip Tracing:** Uses separate RapidAPI quota

---

## Test Property

All endpoints tested with:
```
Address: 1875 AVONDALE Circle, Jacksonville, FL 32205
ZPID: 44480538
```
