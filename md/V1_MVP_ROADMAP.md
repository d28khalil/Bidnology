# V1 MVP ROADMAP - Simplified Foreclosure Deal Intelligence

**Core Mission:** Feed → Auto-Enrich → Identify Worthwhile Properties Quickly

---

## V1 Feature Set (8 Core Features)

| # | Feature | Description | Endpoints | Status |
|---|---------|-------------|-----------|--------|
| 1 | **Property Feed** | Foreclosure listings with filters | 5 | ✅ Complete |
| 2 | **Auto-Enrichment** | Zillow data integration | 8 | ✅ Complete |
| 3 | **Market Anomaly Detection** | Price outlier flags | 4 | ✅ Complete |
| 4 | **Comparable Sales** | AI-powered ARV calculation | 3 | ✅ Complete |
| 5 | **Saved Properties + Kanban** | Pipeline management | 5 | ✅ Complete |
| 6 | **Watchlist + Alerts** | Email notifications | 9 | ✅ Complete |
| 7 | **Deal Criteria** | Auto-match properties to user preferences | 4 | ⏳ To Build |
| 8 | **AI Data Quality Scoring** | Tags properties with incomplete data | 2 | ⏳ To Build |

**Total V1 Endpoints: 40** (34 complete + 6 to build)

---

## V1 Architecture (Simplified)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         V1: FORECLOSURE DEAL INTELLIGENCE               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐         │
│  │ DATA SOURCE  │  →   │  INGESTION   │  →   │  ENRICHMENT  │         │
│  │              │      │              │      │              │         │
│  │  • Sheriff   │      │  • Playwright│      │  • Zillow API│         │
│  │    Sales     │      │  • FastAPI   │      │  • 8 Endpts  │         │
│  │    Website   │      │    Webhooks  │      │              │         │
│  └──────────────┘      └──────────────┘      └──────┬───────┘         │
│                                                     │                 │
│                              ┌────────────────────────┴────────┐       │
│                              ▼                                 ▼       │
│                    ┌──────────────┐                  ┌──────────────┐  │
│                    │   STORAGE    │                  │ DEAL FLAGS  │  │
│                    │              │                  │              │  │
│                    │ • Supabase   │                  │ • Anomalies  │  │
│                    │ • PostgreSQL │                  │ • Comps      │  │
│                    └──────┬───────┘                  └──────┬───────┘  │
│                           │                                 │          │
│                           ▼                                 ▼          │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐         │
│  │   USER TOOLS │  ←   │     API      │  ←   │  AI QUALITY  │         │
│  │              │      │              │      │    MONITOR   │         │
│  │ • Saved List │      │  • FastAPI   │      │ • Prevents   │         │
│  │ • Kanban     │      │  • 34 Routes  │      │   False Pos  │         │
│  │ • Watchlist  │      │              │      │              │         │
│  │ • Email Only │      │              │      │              │         │
│  └──────────────┘      └──────────────┘      └──────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## V1 Data Flow

```
┌─────────────────┐
│ Sheriff Sales   │
│ Website (21 NJ  │
│ Counties)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Playwright     │
│  Scraper        │
│  → Sends JSON   │
└────────┬────────┘
         │ POST /webhook/property
         ▼
┌─────────────────┐
│  FastAPI Server │───────┐
│  - Validate     │       │
│  - Store in DB  │       │ Auto-trigger
└────────┬────────┘       │
         │                │
         ▼                ▼
┌─────────────────┐ ┌─────────────────┐
│ foreclosure_    │ │  Background     │
│ listings table  │ │  Enrichment     │
└────────┬────────┘ │  - Zillow API   │
         │          └────────┬────────┘
         │                   │
         ▼                   ▼
┌─────────────────┐ ┌─────────────────┐
│ zillow_         │ │ Deal Intelligence│
│ enrichment      │ │ Analysis        │
│ table           │ │ - Anomalies     │
└────────┬────────┘ │ - Comps         │
         │          └────────┬────────┘
         │                   │
         └─────────┬─────────┘
                   ▼
         ┌─────────────────┐
         │  Frontend UI    │
         │  (V1 Build)     │
         └─────────────────┘
```

---

## V1 Feature Details

### 1. Property Feed ✅
**What it does:** Display foreclosure listings with search/filter

**Database:** `foreclosure_listings` table
**Endpoints:**
- `GET /api/properties` - List all properties
- `GET /api/properties/{id}` - Get property details
- `GET /api/properties/search` - Search by address/county
- `GET /api/properties/hot` - Get hot deals (filtered)
- `GET /api/counties` - List all counties

**Filters:**
- County
- Price range (opening_bid, approx_upset)
- Sale date range
- Beds/baths/sqft
- Hot deal flag

---

### 2. Auto-Enrichment ✅
**What it does:** Automatically fetch Zillow data for new properties

**Database:** `zillow_enrichment` table
**Endpoints:**
- `POST /api/enrichment/properties/{id}/enrich` - Trigger enrichment
- `GET /api/enrichment/properties/{id}` - Get enrichment status
- `GET /api/enrichment/status/{id}` - Check what's been enriched

**Data Enriched:**
- Basic info: zpid, zestimate, beds, baths, sqft
- Similar properties (comps)
- Nearby properties
- Price history
- Tax history
- Climate risk
- Owner info
- Walk/bike/transit scores
- Property images

---

### 3. Market Anomaly Detection ✅
**What it does:** Flag properties priced below market value

**Database:** `market_anomalies` table
**Service:** `market_anomaly_service.py`

**Endpoints:**
- `GET /api/deal-intelligence/market-anomalies` - List all anomalies
- `GET /api/deal-intelligence/market-anomalies/property/{id}` - Get property anomaly
- `POST /api/deal-intelligence/market-anomalies/analyze` - Analyze property
- `PUT /api/deal-intelligence/market-anomalies/{id}/verify` - Verify/correct

**How it works:**
1. Gets Zillow comps for property
2. Calculates mean/std dev of comp prices
3. Computes Z-score: `(list_price - mean) / std_dev`
4. Flags anomaly if Z-score < -2 (2+ std devs below mean)
5. **Quality check:** Requires min 3 comps, 0.7 confidence

**AI Quality Thresholds:**
- `anomaly_min_comps`: 3 (minimum comparable properties)
- `anomaly_min_confidence`: 0.700 (70% confidence)
- `anomaly_max_zscore`: 2.50 (flag if 2.5+ std devs below mean)

---

### 4. Comparable Sales Analysis ✅
**What it does:** AI-powered ARV (After-Repair Value) calculation

**Database:** `comparable_sales_analysis` table
**Service:** `comparable_sales_service.py`

**Endpoints:**
- `GET /api/deal-intelligence/comparable-sales/{property_id}` - Get comps analysis
- `POST /api/deal-intelligence/comparable-sales/analyze` - Create analysis
- `PUT /api/deal-intelligence/comparable-sales/{id}` - Update manual ARV

**How it works:**
1. Gets enriched Zillow data
2. Filters comps by distance (< 1 mile), age (< 365 days)
3. Sends to OpenAI GPT-4o mini for analysis
4. Returns: ARV estimate, confidence score, comp details

**AI Quality Thresholds:**
- `comps_analysis_min_samples`: 3 (minimum comps)
- `comps_analysis_max_distance_miles`: 1.0 (max distance)
- `comps_analysis_max_age_days`: 365 (max age of comps)
- `comps_analysis_min_similarity_score`: 0.600 (60% similarity)

---

### 5. Saved Properties + Kanban Board ✅
**What it does:** Save properties and move them through pipeline stages

**Database:** `saved_properties` table
**Service:** `saved_properties_service.py`

**Endpoints:**
- `GET /api/deal-intelligence/saved/{user_id}` - Get saved properties
- `POST /api/deal-intelligence/saved` - Save property
- `DELETE /api/deal-intelligence/saved/{id}` - Unsave property
- `PUT /api/deal-intelligence/saved/stage` - Move to Kanban stage
- `GET /api/deal-intelligence/saved/{user_id}/kanban` - Get Kanban board

**Kanban Stages:**
```
researching → analyzing → due_diligence → bidding → won
                                                    → lost
                                                    → archived
```

**Features:**
- Save with notes
- Move between stages
- Bulk stage updates
- Stage statistics
- Filter by stage

---

### 6. Watchlist + Email Alerts ✅
**What it does:** Track properties and get email notifications

**Database:** `user_watchlist`, `user_alerts` tables
**Service:** `watchlist_service.py`

**Endpoints:**
- `GET /api/deal-intelligence/watchlist/{user_id}` - Get watchlist
- `POST /api/deal-intelligence/watchlist` - Add to watchlist
- `DELETE /api/deal-intelligence/watchlist/{id}` - Remove from watchlist
- `PUT /api/deal-intelligence/watchlist/{id}` - Update watchlist entry
- `GET /api/deal-intelligence/alerts/{user_id}` - Get alerts
- `PUT /api/deal-intelligence/alerts/{id}/read` - Mark as read
- `PUT /api/deal-intelligence/alerts/{user_id}/read-all` - Mark all as read
- `DELETE /api/deal-intelligence/alerts/{id}` - Delete alert
- `POST /api/deal-intelligence/checklist/{property_id}/{user_id}/reset` - Reset checklist

**Alert Types:**
- Price change (opening_bid updated)
- Status change (sale date, auction result)
- New comps available
- Auction approaching (X days before)

**Email Only:** No SMS in V1 (Twilio integration adds complexity)

---

### 7. Deal Criteria ⏳ To Build
**What it does:** Auto-match properties to user's foreclosure investment criteria

**Database:** `user_deal_criteria` table (extends `user_settings`)

**Service:** `deal_criteria_service.py`

**Endpoints:**
- `GET /api/deal-intelligence/criteria/{user_id}` - Get user's deal criteria
- `POST /api/deal-intelligence/criteria` - Create/update deal criteria
- `GET /api/deal-intelligence/matches/{user_id}` - Get matching properties
- `POST /api/deal-intelligence/criteria/{user_id}/test` - Test property against criteria

**Deal Criteria Fields:**
| Field | Type | Example |
|-------|------|---------|
| Max Opening Bid | Dollar amount | $150,000 |
| Min Equity Spread | Dollar amount | $50,000 (Zestimate - Opening Bid) |
| Counties | Array | [1, 5, 12] (Bergen, Hudson, Essex) |
| Min/Max Beds | Range | 2 - 4 |
| Min/Max Baths | Range | 1+ |
| Min SqFt | Square feet | 1,200+ |
| Property Types | Array | ["house", "townhome"] |
| Sale Date Window | Date range | Next 30 days |
| Is Anomaly Only | Boolean | Yes (only show underpriced) |

**How it works:**
1. User defines their deal criteria
2. When new property arrives via webhook:
   - System checks if property matches criteria
   - If match: Auto-add to watchlist + email notification
   - Tag property with: `matches-deal-criteria`
3. User can filter feed by "My Matches"

**AI Quality Thresholds:**
- N/A (simple filtering, no AI needed)

---

### 8. AI Data Quality Scoring ⏳ To Build
**What it does:** Tags properties with incomplete enrichment data for manual review

**Database:** Quality score stored in `zillow_enrichment` table

**Service:** `data_quality_service.py`

**Endpoints:**
- `GET /api/enrichment/quality/{property_id}` - Get quality score
- `POST /api/enrichment/quality/score` - Trigger quality scoring

**How it works:**
After enrichment completes, GPT-4o mini analyzes:
1. **Checks for missing critical fields:**
   - Zillow zpid (20 pts)
   - Zestimate (15 pts)
   - Beds/baths/sqft (10 pts each)
   - Photos (10 pts)
   - Tax history (15 pts)
   - Comparables (10 pts)

2. **Assigns completeness score (0-100%)**

3. **Tags property if score < 70%:**
   - Tag: `low-data-quality`
   - Sub-tags: `missing-zillow-data`, `no-comps`, `missing-photos`

**Quality Score Response:**
```json
{
  "property_id": 123,
  "quality_score": 65,
  "is_complete": false,
  "missing_fields": ["zestimate", "photos", "tax_history"],
  "tag": "low-data-quality",
  "recommendation": "Property lacks key information. Manual research recommended."
}
```

**For V1:**
- Tag clearly in UI with warning icon
- Add "Manual Research" checklist for users
- Store manual overrides alongside enrichment data

**For V2:**
- Auto-fetch from Redfin, MLS, county records
- Re-score quality after additional data

---

## V1 Settings System (Simplified 2-Tier)

**Removed:** County-level settings (too complex for MVP)

**V1 Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│  Level 1: Admin Settings (Global)                           │
│  ───────────────────────────────────────────────────────────│
│  • 6 feature toggles (V1 features only)                     │
│  • AI quality thresholds                                    │
│  • Lock flags (prevent user overrides)                      │
└────────────────────────┬────────────────────────────────────┘
                         │ Respects locks
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Level 2: User Preferences                                  │
│  ───────────────────────────────────────────────────────────│
│  • Per-user opt-in/opt-out for features                     │
│  • Inherits admin defaults                                  │
└─────────────────────────────────────────────────────────────┘
```

**V1 Features (Admin Toggles):**
1. `feature_market_anomaly_detection` - Default: ✅ ON
2. `feature_comparable_sales_analysis` - Default: ✅ ON
3. `feature_save_property` - Default: ✅ ON
4. `feature_kanban_board` - Default: ✅ ON
5. `feature_watchlist_alerts` - Default: ✅ ON
6. `feature_export_csv` - Default: ✅ ON

**Endpoints:**
- `GET /api/deal-intelligence/settings/admin` - Get admin settings
- `PUT /api/deal-intelligence/settings/admin` - Update admin settings
- `GET /api/deal-intelligence/settings/user/{user_id}` - Get user prefs
- `POST /api/deal-intelligence/settings/user` - Create user prefs
- `PUT /api/deal-intelligence/settings/user/{user_id}` - Update user prefs

---

## V1 Database Schema

### Core Tables

| Table | Purpose | Status |
|-------|---------|--------|
| `foreclosure_listings` | Raw foreclosure data | ✅ Existing |
| `zillow_enrichment` | Enriched property data | ✅ Existing |
| `nj_counties` | County reference | ✅ Existing |
| `deal_features_admin_settings` | Feature toggles (V1: 6 features) | ✅ Complete |
| `market_anomalies` | Price anomaly results | ✅ Complete |
| `comparable_sales_analysis` | Comps analysis | ✅ Complete |
| `saved_properties` | Saved + Kanban | ✅ Complete |
| `user_watchlist` | Watchlist | ✅ Complete |
| `user_alerts` | Alert queue | ✅ Complete |
| `property_notes` | User notes | ✅ Complete |
| `due_diligence_checklists` | Task tracking | ✅ Complete |

### Removed from V1 (V2 Only)

| Table | Reason for V2 |
|-------|---------------|
| `deal_features_county_settings` | Too complex for MVP |
| `deal_features_user_preferences` | Simplified to user_settings table |
| `user_portfolio` | Strays from core mission (acquired properties) |
| `shared_properties` | V2: Team collaboration |
| `property_comments` | V2: Team collaboration |
| `mobile_push_tokens` | V2: Mobile notifications |
| `push_notification_queue` | V2: Mobile notifications |
| `investment_strategies` | V2: Advanced features |

---

## V1 Frontend UI Plan

### Page Structure

```
/ (Home)
├── /properties (Feed)
│   ├── List view with filters
│   ├── Map view (Mapbox/Google Maps)
│   └── Property cards with hot deal badges
│
├── /property/{id} (Detail)
│   ├── Basic info + photos
│   ├── Zillow enrichment data
│   ├── Street View embed
│   ├── Market anomaly flag
│   ├── Comps analysis
│   └── Save/Watchlist buttons
│
├── /saved (Kanban)
│   ├── researching column
│   ├── analyzing column
│   ├── due_diligence column
│   ├── bidding column
│   └── won/lost/archived columns
│
├── /watchlist
│   ├── Watchlist table
│   ├── Alert notifications
│   └── Alert settings
│
└── /settings
    ├── Feature preferences
    └── Alert preferences
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14 (App Router) |
| **UI Components** | shadcn/ui + Tailwind CSS |
| **Maps** | Mapbox GL JS or Google Maps API |
| **Street View** | Google Maps Static Street View (free) |
| **State** | React Context + SWR (data fetching) |
| **Charts** | Recharts (simple, lightweight) |

---

## V1 Map Integration

### Mapbox Implementation (Recommended)

**Cost:** Free tier: 50,000 map loads/month

**Features:**
- Property markers with hot deal colors
- Clustering for 100+ properties
- Filter by county, price, hot deals
- Click marker → Property detail

**Code:**
```javascript
// app/components/PropertyMap.tsx
import mapboxgl from 'mapbox-gl'

const PropertyMap = ({ properties }) => {
  useEffect(() => {
    const map = new mapboxgl.Map({
      container: 'map',
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [-74.5, 40.0], // NJ center
      zoom: 8
    })

    // Add markers with hot deal colors
    properties.forEach(property => {
      const color = property.is_anomaly ? '#ef4444' : '#3b82f6'
      new mapboxgl.Marker({ color })
        .setLngLat([property.longitude, property.latitude])
        .setPopup(new mapboxgl.Popup().setHTML(`
          <div class="p-2">
            <h3>${property.address}</h3>
            <p>Opening Bid: $${property.opening_bid?.toLocaleString()}</p>
            ${property.is_anomaly ? '<span class="text-red-500">🔥 Hot Deal</span>' : ''}
            <a href="/property/${property.id}">View Details</a>
          </div>
        `))
        .addTo(map)
    })

    return () => map.remove()
  }, [properties])

  return <div id="map" className="w-full h-[600px] rounded-lg" />
}
```

### Google Street View Integration

**Cost:** Free with Google Maps JavaScript API ($200 free credit = ~28,500 loads)

**Static Images (Easiest):**
```javascript
// Static Street View image
const StreetViewImage = ({ lat, lng }) => {
  const streetViewUrl = `https://maps.googleapis.com/maps/api/streetview?
    size=600x400
    &location=${lat},${lng}
    &fov=90
    &heading=0
    &pitch=0
    &key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}`

  return <img src={streetViewUrl} alt="Street View" className="w-full rounded-lg" />
}
```

---

## V1 Email Notifications (SendGrid)

**Setup:**
1. Create SendGrid account (free: 100 emails/day)
2. Add `SENDGRID_API_KEY` to `.env`
3. Use `watchlist_service.py` to generate alerts

**Alert Email Template:**
```html
Subject: 🔥 Hot Deal Alert: 123 Main St

Hello {user_name},

A property on your watchlist has been updated:

Property: 123 Main St, Newark, NJ 07102
Alert: Price dropped from $85,000 to $75,000
Sale Date: January 15, 2025

View Property: https://yourapp.com/property/123

---
You're receiving this because you added this property to your watchlist.
Unsubscribe: https://yourapp.com/settings/alerts
```

---

## V1 Implementation Checklist

### Backend (Already Complete ✅)

- [x] Property feed endpoints (5)
- [x] Auto-enrichment service (8 Zillow endpoints)
- [x] Market anomaly detection (4 endpoints)
- [x] Comparable sales analysis (3 endpoints)
- [x] Saved properties + Kanban (5 endpoints)
- [x] Watchlist + alerts (9 endpoints)
- [x] Feature toggle system (6 V1 features)
- [x] AI quality monitoring
- [x] Database schema (V1 tables)

### Frontend (To Build)

- [ ] Next.js 14 project setup
- [ ] shadcn/ui components
- [ ] Property feed page (list + filters)
- [ ] Property detail page
- [ ] Map component (Mapbox)
- [ ] Street View embed
- [ ] Kanban board page
- [ ] Watchlist page
- [ ] Settings page
- [ ] Email notification integration

### Integration

- [ ] Auth (Supabase Auth)
- [ ] User profiles
- [ ] Alert preferences
- [ ] CSV export (SendGrid for files)

---

## V1 Success Metrics

| Metric | Target |
|--------|--------|
| **Time to identify hot deals** | < 5 minutes from feed load |
| **Data accuracy** | > 95% enrichment success rate |
| **False positive rate** | < 5% (AI quality monitoring) |
| **User engagement** | > 10 properties saved/user/month |
| **Alert effectiveness** | > 20% alert click-through rate |

---

## V1 Launch Plan

### Phase 1: Backend (2 weeks)
- [x] API endpoints (34 routes)
- [x] Database schema
- [x] Service layer
- [ ] Integration testing
- [ ] Documentation

### Phase 2: Frontend (3 weeks)
- [ ] Next.js setup
- [ ] Core pages (feed, detail, kanban, watchlist)
- [ ] Map integration
- [ ] Street View
- [ ] Auth integration

### Phase 3: Polish (1 week)
- [ ] Email templates
- [ ] Error handling
- [ ] Loading states
- [ ] Mobile responsive
- [ ] Beta testing

**Total V1 Timeline: 6 weeks**

---

## V1 Cost Summary

| Service | Free Tier | V1 Usage | Monthly Cost |
|---------|-----------|----------|-------------|
| **Supabase** | 500MB DB | ~100MB | $0 |
| **Zillow API** | 250 req/mo | ~200 req/mo | $0 |
| **OpenAI** | $5 credit | ~50k tokens/mo | ~$0.50 |
| **Mapbox** | 50k loads | ~5k loads | $0 |
| **Google Maps** | $200 credit | ~1k loads | $0 |
| **SendGrid** | 100/day | ~50 emails | $0 |
| **Total** | - | - | **~$0.50/month** |

---

## What's in V2?

See `V2_FULL_FEATURES.md` for:

1. **Portfolio Tracking** - Acquired properties management
2. **Team Collaboration** - Share properties, comments, permissions
3. **Investment Strategies** - Custom strategy templates
4. **Renovation Estimator** - GPT-4o Vision photo analysis
5. **Mobile Push Notifications** - iOS/Android alerts
6. **SMS Notifications** - Twilio text alerts
7. **County-Level Settings** - Per-county feature overrides
8. **Advanced Analytics** - ML ranking, portfolio ROI

**V2 is everything in V1 PLUS 8 additional features.**
