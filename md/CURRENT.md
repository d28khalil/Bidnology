# CURRENT.md - V1 Implementation Status

**Last Updated:** 2026-01-02

**Project:** Bidnology - NJ Foreclosure Property Investment Platform

---

## RECENT UPDATES

### 2026-01-02 - Share Button Feature (Complete)
- **Added** property share functionality to `PropertyDetailModal.tsx`
- **Implemented** dual-mode sharing:
  - Mobile devices: Native Web Share API (`navigator.share`)
  - Desktop: Clipboard copy fallback (`navigator.clipboard.writeText`)
- **Features**:
  - Share includes property address, auction date, and spread percentage
  - Visual feedback (checkmark badge) displays for 2 seconds after successful action
  - Button positioned between Skip Trace and Close buttons in modal header
- **Status**: ✅ Live and confirmed working on `http://localhost:3002`

---

---

## 1. ZILLOW ENRICHMENT ENDPOINTS (Active)

**API Provider:** Private Zillow RapidAPI (`private-zillow.p.rapidapi.com`)

**Cost:** 9 requests per full property enrichment

### ENABLED ENDPOINTS (9 Active)

| Internal Name | API Path | Request Cost | Data Returned |
|---------------|----------|--------------|---------------|
| `pro_byaddress` | `GET /pro/byaddress` | 1 | ZPID, beds, baths, sqft, zestimate, rentZestimate |
| `custom_ad_byzpid` | `GET /custom_ad/byzpid` | 1 | 100+ photos, property details, description |
| `similar` | `GET /similar` | 1 | 20+ active comparable properties (for ARV) |
| `pricehistory` | `GET /pricehistory` | 1 | Price changes over time |
| `graph_listing_price` | `GET /graph_charts?which=listing_price` | 1 | 10-year price chart data |
| `taxinfo` | `GET /taxinfo` | 1 | 20+ years tax assessment/payment history |
| `climate` | `GET /climate` | 1 | Flood, fire, storm risk scores |
| `housing_market` | `GET /housing_market` | 1 | ZHVI, appreciation trends |
| `ownerinfo` | `GET /ownerinfo` | 1 | Owner name, agent contact info |

### DISABLED ENDPOINTS (4 Inactive)

| Internal Name | API Path | Status |
|---------------|----------|--------|
| `nearby` | `GET /nearby` | OFF |
| `walk_transit_bike` | `GET /walk_transit_bike` | OFF |
| `rental_market` | `GET /rental_market` | OFF |
| `custom_ae_searchbyaddress` | `GET /custom_ae/searchbyaddress` | OFF |

---

## 2. V1 BACKEND ENDPOINTS (Frontend Integration)

**Base URL:** `http://localhost:8080`

### PROPERTY FEED ENDPOINTS

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/enrichment/properties` | GET | Property list with enrichment LEFT JOIN |
| `/api/enrichment/properties/{id}` | GET | Single property details |
| `/api/enrichment/status` | GET | Enrichment stats (total, pending, enriched, failed) |
| `POST /api/enrichment/properties/{id}/enrich` | POST | Trigger enrichment for a property |

### SAVED PROPERTIES / KANBAN ENDPOINTS

| Endpoint | Method | Purpose | Table |
|----------|--------|---------|-------|
| `/api/deal-intelligence/saved/{user_id}` | GET | Get saved properties | `user_data` |
| `/api/deal-intelligence/saved/{user_id}/kanban` | GET | Get Kanban board data | `user_data` |
| `/api/deal-intelligence/saved` | POST | Save a property | `user_data` |
| `/api/deal-intelligence/saved/{saved_id}` | DELETE | Unsave a property | `user_data` |
| `/api/deal-intelligence/saved/stage` | PUT | Update Kanban stage | `user_data` |
| `/api/deal-intelligence/saved/{saved_id}/notes` | PUT | Update property notes | `user_data.notes` |
| `/api/deal-intelligence/saved/{user_id}/stats` | GET | Saved stats summary | `user_data` |

### WATCHLIST / ALERTS ENDPOINTS

| Endpoint | Method | Purpose | Table |
|----------|--------|---------|-------|
| `/api/deal-intelligence/watchlist/{user_id}` | GET | Get watchlist | `user_data` |
| `/api/deal-intelligence/watchlist` | POST | Add to watchlist | `user_data` |
| `/api/deal-intelligence/watchlist/{property_id}` | DELETE | Remove from watchlist | `user_data` |
| `/api/deal-intelligence/watchlist/{property_id}` | PUT | Update watchlist entry | `user_data` |
| `/api/deal-intelligence/alerts/{user_id}` | GET | Get user alerts | `user_alerts` |
| `/api/deal-intelligence/alerts/{alert_id}/read` | PUT | Mark alert as read | `user_alerts` |
| `/api/deal-intelligence/alerts/{user_id}/read-all` | PUT | Mark all alerts read | `user_alerts` |
| `/api/deal-intelligence/alerts/{alert_id}` | DELETE | Delete alert | `user_alerts` |

### COMPARABLE SALES ENDPOINTS

| Endpoint | Method | Purpose | Table |
|----------|--------|---------|-------|
| `/api/deal-intelligence/comparable-sales/{property_id}` | GET | Get comps analysis | `comparable_sales_analysis` |
| `/api/deal-intelligence/comparable-sales/analyze` | POST | Create comps analysis | `comparable_sales_analysis` + `comparable_properties` |

### DEAL CRITERIA ENDPOINTS

| Endpoint | Method | Purpose | Table |
|----------|--------|---------|-------|
| `/api/deal-intelligence/criteria/{user_id}` | GET | Get user's deal criteria | `deal_intelligence_investor_criteria` |
| `/api/deal-intelligence/criteria` | POST | Save/update deal criteria | `deal_intelligence_investor_criteria` |
| `/api/deal-intelligence/matches/{user_id}` | GET | Get matching properties | Returns matched properties |
| `/api/deal-intelligence/criteria/{user_id}/test` | POST | Test property against criteria | Returns match result |

### NOTES & CHECKLIST ENDPOINTS

| Endpoint | Method | Purpose | Table |
|----------|--------|---------|-------|
| `/api/deal-intelligence/notes/{property_id}` | GET | Get property notes | `user_data.notes` (JSONB) |
| `/api/deal-intelligence/notes` | POST | Add a note | `user_data.notes` (JSONB) |
| `/api/deal-intelligence/notes/{note_id}` | PUT | Update a note | `user_data.notes` (JSONB) |
| `/api/deal-intelligence/notes/{note_id}` | DELETE | Delete a note | `user_data.notes` (JSONB) |
| `/api/deal-intelligence/checklist/{property_id}/{user_id}` | GET | Get checklist | `user_data.checklist` (JSONB) |
| `/api/deal-intelligence/checklist/{property_id}/{user_id}` | PUT | Update checklist | `user_data.checklist` (JSONB) |
| `/api/deal-intelligence/checklist/{property_id}/{user_id}/reset` | POST | Reset checklist | `user_data.checklist` (JSONB) |

### UTILITY ENDPOINTS

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/deal-intelligence/street-view` | POST | Get Google Street View images |
| `/api/deal-intelligence/export/csv` | POST | Export properties to CSV |
| `/api/deal-intelligence/quality/{property_id}` | GET | Get data quality score |

---

## 3. V1 DATABASE TABLES

### CORE PROPERTY TABLES

| Table | Rows | Purpose |
|-------|------|---------|
| `foreclosure_listings` | 1,337 | Core property data (scraped from sheriff sale sites) |
| `zillow_enrichment` | 16 | Zillow enrichment data (joined via property_id) |
| `counties` | 16 | County reference data (NJ counties) |

### USER DATA TABLES (V1 - All-in-One)

| Table | Rows | Purpose |
|-------|------|---------|
| `user_data` | 3 | Saved/watchlist, Kanban, notes, checklist (single table) |
| `user_alerts` | 0 | Alert notifications |

### DEAL INTELLIGENCE TABLES

| Table | Rows | Purpose |
|-------|------|---------|
| `comparable_sales_analysis` | 0 | Comps + ARV calculations |
| `comparable_properties` | 0 | Individual comparable properties |
| `deal_intelligence_investor_criteria` | 0 | User deal matching criteria |

### ADMIN SETTINGS TABLES

| Table | Rows | Purpose |
|-------|------|---------|
| `enrichment_admin_settings` | 1 | Global enrichment endpoint toggles |
| `county_enrichment_settings` | 0 | Per-county enrichment overrides |
| `user_enrichment_preferences` | 0 | Per-user enrichment preferences |

### SCRAPER TABLES

| Table | Rows | Purpose |
|-------|------|---------|
| `scrape_schedule` | 7 | Scraper job tracking |

---

## 4. V2 TABLES (NOT FOR V1 - SKIP FOR NOW)

**These tables are reserved for V2 features and should NOT be used in V1 frontend:**

| Table | V2 Feature |
|-------|------------|
| `v2_deal_features_admin_settings` | V2 Feature Toggle System |
| `v2_deal_features_county_settings` | V2 Feature Toggle System |
| `v2_deal_features_user_preferences` | V2 Feature Toggle System |
| `v2_market_anomalies` | V2 Market Anomaly Detection |
| `v2_renovation_estimates` | V2 Renovation Cost Estimator (GPT-4o Vision) |
| `v2_investment_strategies` | V2 Investment Strategy Templates |
| `v2_user_portfolio` | V2 Portfolio Tracking |
| `v2_shared_properties` | V2 Team Collaboration |
| `v2_property_comments` | V2 Team Comments |
| `v2_mobile_push_tokens` | V2 Mobile Push Notifications |
| `v2_push_notification_queue` | V2 Push Notifications |
| `push_notification_history` | V2 Push Notifications |
| `push_notification_templates` | V2 Push Notifications |
| `v2_deal_intelligence_model_weights` | V2 ML Ranking System |
| `v2_deal_intelligence_feature_importance` | V2 ML Ranking System |
| `v2_deal_intelligence_feedback` | V2 ML Ranking System |
| `v2_deal_intelligence_ranking_history` | V2 ML Ranking System |
| `v2_deal_intelligence_exploration` | V2 ML Ranking System |
| `v2_deal_intelligence_attention_scores` | V2 ML Ranking System |

---

## 5. USER_DATA TABLE STRUCTURE (V1 All-in-One)

The `user_data` table is the **central V1 table** for user-specific property data:

| Column | Type | Purpose |
|--------|------|---------|
| `id` | bigint | Primary key |
| `user_id` | text | User identifier |
| `property_id` | integer | FK to foreclosure_listings |
| `is_saved` | boolean | Saved properties flag |
| `kanban_stage` | text | Pipeline stage (researching, analyzing, due_diligence, bidding, won, lost, archived) |
| `saved_notes` | text | Property notes (simple text) |
| `is_watched` | boolean | Watchlist flag |
| `watch_priority` | text | Priority level (low, normal, high) |
| `alert_on_price_change` | boolean | Alert setting |
| `alert_on_status_change` | boolean | Alert setting |
| `alert_on_new_comps` | boolean | Alert setting |
| `alert_on_auction_near` | boolean | Alert setting |
| `auction_alert_days` | integer | Days before auction to alert |
| `watch_notes` | text | Watchlist notes |
| `notes` | jsonb | Detailed notes array |
| `checklist` | jsonb | Due diligence checklist object |
| `checklist_total` | integer | Total checklist items |
| `checklist_completed` | integer | Completed checklist items |
| `checklist_completed_at` | timestamptz | Checklist completion timestamp |

---

## 6. PROPERTY FEED RESPONSE STRUCTURE

### `/api/enrichment/properties` Response

```json
{
  "count": 1337,
  "properties": [
    {
      "id": 1002,
      "property_address": "123 Main St",
      "city": "Newark",
      "state": "NJ",
      "zip_code": "07102",
      "county_id": 2,
      "county_name": "Essex",
      "sale_date": "2025-01-15",
      "sale_time": "10:00:00",
      "court_name": "Essex County Superior Court",
      "property_status": "scheduled",
      "opening_bid": 75000,
      "approx_upset": 85000,
      "judgment_amount": 150000,
      "minimum_bid": null,
      "sale_price": null,
      "plaintiff": "Bank of America",
      "plaintiff_attorney": "Smith & Associates",
      "defendant": "John Doe",
      "property_type": "Single Family",
      "lot_size": "60x100",
      "filing_date": "2024-08-15",
      "judgment_date": "2024-10-01",
      "writ_date": "2024-10-15",
      "description": null,
      "details_url": "https://...",
      "zillow_zpid": 12345678,
      "zillow_enrichment_status": "fully_enriched",
      "zillow_enriched_at": "2025-01-10T10:30:00Z",

      "zillow_enrichment": [
        {
          "zpid": 12345678,
          "zestimate": 185000,
          "zestimate_low": 170000,
          "zestimate_high": 200000,
          "bedrooms": 3,
          "bathrooms": 2,
          "sqft": 1450,
          "year_built": 1985,
          "lot_size": 6000,
          "property_type": "SINGLE_FAMILY",
          "last_sold_date": "2015-06-15",
          "last_sold_price": 155000,
          "images": ["url1", "url2", ...],
          "tax_assessment": 175000,
          "tax_assessment_year": 2024,
          "tax_billed": 4500,
          "walk_score": null,
          "transit_score": null,
          "bike_score": null,
          "tax_history": [...],
          "price_history": [...],
          "zestimate_history": [...],
          "climate_risk": {...},
          "comps": [...],
          "similar_properties": [...],
          "nearby_properties": [...]
        }
      ],

      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-10T10:30:00Z"
    }
  ]
}
```

---

## 7. QUERY PARAMETERS FOR PROPERTY FEED

| Parameter | Type | Example | Purpose |
|-----------|------|---------|---------|
| `county_id` | int | `2` | Filter by county |
| `state` | string | `NJ` | Filter by state |
| `city` | string | `Newark` | Filter by city |
| `property_status` | string | `scheduled` | Filter by status |
| `min_upset_price` | float | `50000` | Minimum upset price |
| `max_upset_price` | float | `200000` | Maximum upset price |
| `limit` | int | `50` | Results per page (max 500) |
| `offset` | int | `0` | Pagination offset |
| `search` | string | `Main St` | Search address/city |
| `order_by` | string | `sale_date` | Sort field |
| `order` | string | `desc` | Sort direction (asc/desc) |
| `property_ids` | string | `1002,1003` | Comma-separated IDs |
| `enrichment_status` | string | `fully_enriched` | Filter by enrichment status |

---

## 8. FRONTEND PROJECT STRUCTURE

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                 # Home page (property feed)
│   ├── HomePageClient.tsx       # Client-side property feed
│   ├── pipeline/
│   │   └── page.tsx             # Kanban board page
│   └── watchlist/
│       └── page.tsx             # Watchlist page
├── components/
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   ├── PropertyRow.tsx
│   ├── KanbanCard.tsx
│   ├── KanbanColumn.tsx
│   ├── PropertyDetailModal.tsx
│   ├── StatsCard.tsx
│   ├── FilterSlider.tsx
│   └── FilterToggle.tsx
├── contexts/
│   ├── AppContext.tsx
│   └── UserContext.tsx
├── lib/
│   ├── api/
│   │   └── client.ts            # API client with all endpoints
│   ├── types/
│   │   └── property.ts          # TypeScript types
│   ├── hooks/
│   │   └── useProperties.ts
│   ├── utils/
│   │   └── format.ts
│   └── index.ts
├── .env.local                   # Environment variables
├── next.config.js
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

---

## 9. ENVIRONMENT VARIABLES

```env
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_key
CLERK_SECRET_KEY=your_clerk_secret
```

---

## 10. FRONTEND ARCHITECTURE & IMPLEMENTATION STATUS

### AUTHENTICATION MIGRATION (Complete)

**Status**: ✅ Migrated from Supabase Auth to Clerk

| Aspect | Previous (Supabase) | Current (Clerk) |
|--------|-------------------|-----------------|
| Provider | `@supabase/supabase-js` | `@clerk/nextjs@^6.36.5` |
| Routing | Standard | Hash-based (`router="hash"`) |
| Middleware | Supabase SSR | `clerkMiddleware()` |
| Public Routes | - | `/login`, `/sign-up` |
| Auth Context | `SupabaseContext` | `UserContext` (wrapper) |

**Key Files**:
- `middleware.ts` - Route protection with Clerk
- `layout.tsx` - Root provider with Clerk
- `contexts/UserContext.tsx` - User state wrapper
- `app/login/[[...login]]/page.tsx` - Sign-in page (styled dark theme)
- `app/sign-up/[[...sign-up]]/page.tsx` - Sign-up page (styled dark theme)

---

### TECHNOLOGY STACK

| Category | Technology | Version |
|----------|-----------|---------|
| Framework | Next.js | 14.2.0 |
| UI Library | React | 18.3.0 |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 3.4.0 |
| Auth | Clerk | 6.36.5 |
| Database (legacy) | Supabase | 2.89.0 |
| Font | Manrope | Google Fonts |
| Icons | Material Symbols Outlined | Google Fonts |

---

### PAGES IMPLEMENTED

| Route | Page | Status | Description |
|-------|------|--------|-------------|
| `/` | `app/page.tsx` + `HomePageClient.tsx` | ✅ Live | Property feed with filtering, search, modal |
| `/pipeline` | `app/pipeline/page.tsx` | ✅ Live | Kanban board for saved properties |
| `/watchlist` | `app/watchlist/page.tsx` | ✅ Live | Watchlist for tracked properties |
| `/login` | `app/login/[[...login]]/page.tsx` | ✅ Live | Clerk sign-in (dark themed) |
| `/sign-up` | `app/sign-up/[[...sign-up]]/page.tsx` | ✅ Live | Clerk sign-up (dark themed) |

---

### COMPONENTS

| Component | File | Status | Features |
|-----------|------|--------|----------|
| `Header` | `components/Header.tsx` | ✅ Live | Search, user menu, sign out |
| `Sidebar` | `components/Sidebar.tsx` | ✅ Live | Nav links, alert badge |
| `PropertyRow` | `components/PropertyRow.tsx` | ✅ Live | Property list item |
| `PropertyDetailModal` | `components/PropertyDetailModal.tsx` | ✅ Live | Detail view + **share button** |
| `KanbanCard` | `components/KanbanCard.tsx` | ✅ Live | Kanban property card |
| `KanbanColumn` | `components/KanbanColumn.tsx` | ✅ Live | Kanban stage column |
| `StatsCard` | `components/StatsCard.tsx` | ✅ Live | Metric display |
| `FilterSlider` | `components/FilterSlider.tsx` | ✅ Live | Range filter |
| `FilterToggle` | `components/FilterToggle.tsx` | ✅ Live | Boolean filter |

---

### CONTEXT & STATE MANAGEMENT

| Context | File | Purpose |
|---------|------|---------|
| `UserContext` | `contexts/UserContext.tsx` | Auth state (Clerk wrapper) |
| `AppContext` | `contexts/AppContext.tsx` | Global app state (properties, filters, alerts, saved) |

**AppContext State**:
```typescript
{
  // Properties
  properties: Property[]
  filteredProperties: Property[]

  // Filters
  filters: PropertyFilters
  updateFilter: <K>(key: K, value: PropertyFilters[K]) => void

  // Loading
  isLoading: boolean

  // Alerts
  alerts: Alert[]
  unreadAlertCount: number

  // Saved/Kanban
  savedProperties: SavedProperty[]

  // UI State
  selectedPropertyId: number | null
}
```

---

### STYLING SYSTEM

**Color Palette** (Dark Theme):

| Usage | Color |
|-------|-------|
| Background primary | `#0F1621` |
| Background dark | `#101622` |
| Surface | `#1a2332` |
| Primary (brand) | `#2B6CEE` |
| Primary hover | `#2355c4` |
| Border dark | `rgba(255,255,255,0.08)` |
| Text white | `#ffffff` |
| Text gray | `#9ca3af` |

**Global Styles** (`app/globals.css`):
- Custom scrollbars (8px width, dark theme)
- Kanban column scrollbars (6px)
- Range slider custom styling
- Clerk component overrides (centered, dark themed, branding hidden)
- Glass effect utility (`.glass-effect`)

**Typography**:
- Font: Manrope (Google Fonts)
- Display class for headings
- Antialiasing enabled

---

### CURRENT FEATURE SET

#### Property Feed
- ✅ Property list with enrichment data
- ✅ County, city, status, price filters
- ✅ Address search
- ✅ Property detail modal
- ✅ **Share button** (mobile native, desktop clipboard)
- ✅ Skip trace integration

#### Pipeline / Kanban
- ✅ 7 stages: researching, analyzing, due_diligence, bidding, won, lost, archived
- ✅ Drag-and-drop property management
- ✅ Stage statistics

#### Watchlist
- ✅ Property tracking with alerts
- ✅ Priority levels (low, normal, high)
- ✅ Alert configuration

---

### DEVELOPMENT SERVER

**Frontend**: `http://localhost:3002`

**Start Command**:
```bash
cd frontend
PORT=3002 npm run dev
```

**Backend API**: `http://localhost:8080`

---
