# BIDNOLOGY - NJ Sheriff Sale Foreclosure Platform

AI-powered web scraper for New Jersey sheriff sale foreclosure listings with Zillow enrichment and deal intelligence.

---

## VERSION DOCUMENTATION

**This project is organized into two major versions:**

| Version | Description | Documentation |
|---------|-------------|---------------|
| **V1 MVP** | Simplified foreclosure deal intelligence with 6 core features | [V1_MVP_ROADMAP.md](V1_MVP_ROADMAP.md) |
| **V2 Full** | Complete platform with 14 features including portfolio tracking, team collaboration, and advanced analytics | [V2_FULL_FEATURES.md](V2_FULL_FEATURES.md) |

### V1 MVP Features (Current Focus)
1. Property Feed - Foreclosure listings with filters
2. Auto-Enrichment - Zillow data integration
3. Market Anomaly Detection - Price outlier flags
4. Comparable Sales - AI-powered ARV calculation
5. Saved Properties + Kanban - Pipeline management
6. Watchlist + Email Alerts - Email notifications

### V2 Additional Features (Future)
- Portfolio Tracking (acquired properties management)
- Team Collaboration (share properties, comments)
- Investment Strategies (custom strategy templates)
- Renovation Estimator (GPT-4o Vision photo analysis)
- SMS/Push Notifications (Twilio, Firebase)
- County-Level Settings (per-county feature overrides)
- Advanced Analytics (ML ranking, portfolio ROI)

---

## V1 FRONTEND OVERVIEW & WORKFLOW

### V1 MVP Features Summary (Current Focus)

**8 Core Features to implement over 3 weeks:**

| Feature | Description | Priority |
|---------|-------------|----------|
| 1. Property Feed | Foreclosure listings with filters (county, price, date) | P0 |
| 2. Auto-Enrichment | Zillow data auto-fills property details | P0 |
| 3. Market Anomaly Detection | Price outlier flags ("Hot Deals") | P0 |
| 4. Comparable Sales | AI-powered ARV calculation | P0 |
| 5. Saved Properties + Kanban | Pipeline management (researching → analyzing → bidding) | P0 |
| 6. Export CSV | Download filtered results | P0 |
| 7. Watchlist + Alerts | Track properties, email notifications | P1 |
| 8. Mobile Responsive | Full mobile support | P1 |

### Frontend Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14.1.0 | React framework with App Router |
| React | 18 | UI library |
| TypeScript | 5 | Type safety |
| Tailwind CSS | 3.4.1 | Utility-first styling |
| shadcn/ui | latest | Pre-built accessible components |
| Zustand | 4.5.0 | Lightweight state management |
| Tanstack Query | 5.17.19 | Server state & caching |
| Recharts | 2.10.4 | Charts & graphs |
| Lucide React | 0.303.0 | Icon library |

### Design System

**Dark Theme Colors:**
```css
--background-primary: #0a0a0a
--background-secondary: #1a1a1a
--background-hover: #2a2a2a
--border: #333333
--text-primary: #ffffff
--text-secondary: #a0a0a0
--text-muted: #666666
--primary: #3b82f6
--primary-hover: #2563eb
--success: #22c55e
--warning: #eab308
--danger: #ef4444
```

**Glass Morphism:**
- Semi-transparent backgrounds with blur
- Subtle borders
- Gradient accents

### Frontend Pages Structure

```
frontend/app/
├── page.tsx                    # Dashboard (stats, hot deals)
├── properties/
│   ├── page.tsx               # Property feed with filters
│   └── [id]/
│       └── page.tsx           # Property detail page
├── saved/
│   └── page.tsx               # Kanban board
├── watchlist/
│   └── page.tsx               # Watchlist + alerts
├── settings/
│   └── page.tsx               # User settings
└── layout.tsx                 # Root layout
```

### Frontend Build Phases (3-Week Timeline)

**Week 1: Foundation**
- Day 1-2: Project setup, shadcn/ui installation, design system
- Day 3-4: Property feed page with filters
- Day 5: Property detail page with Zillow data

**Week 2: Core Features**
- Day 6-7: Market anomaly detection UI, "Hot Deals" alerts
- Day 8-9: Saved properties + Kanban board
- Day 10: Watchlist + alerts

**Week 3: Polish & Launch**
- Day 11-12: Settings page, user preferences
- Day 13: Mobile responsive optimization
- Day 14: Testing, bug fixes, deployment

### API Integration

**Base URL:** `http://localhost:8080`

**Key Endpoints:**
```
GET  /api/properties                    # List properties
GET  /api/properties/{id}               # Property details
POST /api/enrichment/properties/{id}/enrich  # Trigger enrichment
GET  /api/deal-intelligence/anomalies   # Market anomalies
GET  /api/deal-intelligence/comps/{id}  # Comparable sales
POST /api/deal-intelligence/saved       # Save property
GET  /api/deal-intelligence/watchlist/{user_id}  # Get watchlist
```

### Component Architecture

```
components/
├── ui/                    # shadcn/ui base components
├── PropertyCard.tsx       # Property listing card
├── PropertyGrid.tsx       # Grid/table view toggle
├── FilterBar.tsx          # County, price, date filters
├── KanbanColumn.tsx       # Kanban stage column
├── KanbanCard.tsx         # Kanban property card
├── AlertBadge.tsx         # "Hot Deal" indicator
├── StatCard.tsx           # Dashboard stat card
└── Layout/
    ├── Header.tsx         # Nav bar
    ├── Sidebar.tsx        # Filters sidebar
    └── Footer.tsx         # Footer
```

### State Management (Zustand)

```typescript
// stores/propertyStore.ts
interface PropertyStore {
  properties: Property[];
  filters: PropertyFilters;
  selectedProperty: Property | null;
  setProperties: (props: Property[]) => void;
  updateFilters: (filters: Partial<PropertyFilters>) => void;
}

// stores/userStore.ts
interface UserStore {
  user: User | null;
  savedProperties: SavedProperty[];
  watchlist: WatchlistItem[];
}
```

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  USER INTERACTION                                           │
│  ───────────────────────────────────────────────────────────│
│  1. User visits /properties                                 │
│  2. Applies filters (county, price range, date)             │
│  3. Clicks property for details                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js App Router)                              │
│  ───────────────────────────────────────────────────────────│
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Tanstack Query (React Query)                       │    │
│  │  • Caching for 5 minutes                            │    │
│  │  • Automatic refetch on window focus                │    │
│  │  • Optimistic updates for mutations                 │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │  Zustand State Store                               │    │
│  │  • Global filters                                   │    │
│  │  • User preferences                                │    │
│  │  • Selected property                               │    │
│  └──────────────────────┬──────────────────────────────┘    │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  API LAYER (/lib/api.ts)                                    │
│  ───────────────────────────────────────────────────────────│
│  • Axios client with base URL                               │
│  • Request/response interceptors                           │
│  • Error handling                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  FASTAPI BACKEND (port 8080)                                │
│  ───────────────────────────────────────────────────────────│
│  • Authentication (Supabase JWT)                            │
│  • Business logic                                           │
│  • Data validation (Pydantic)                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  SUPABASE DATABASE                                          │
│  ───────────────────────────────────────────────────────────│
│  • foreclosure_listings                                     │
│  • zillow_enrichment                                        │
│  • market_anomalies                                         │
│  • comparable_sales_analysis                                │
│  • saved_properties (Kanban)                               │
│  • user_watchlist                                           │
│  • user_alerts                                              │
└─────────────────────────────────────────────────────────────┘
```

### Development Commands

```bash
# Frontend development
cd frontend
npm install              # Install dependencies
npm run dev              # Start dev server (localhost:3000)
npm run build            # Production build
npm run start            # Run production build
npm run lint             # Run ESLint

# Backend development (from project root)
cd webhook_server
../venv/bin/python -m uvicorn app:app --reload --port 8080
```

### Testing Checklist

**Phase 1 - Property Feed**
- [ ] List all properties with pagination
- [ ] Filter by county
- [ ] Filter by price range
- [ ] Filter by sale date
- [ ] Sort by price, date, address
- [ ] Grid view toggle
- [ ] Table view toggle

**Phase 2 - Property Details**
- [ ] View property details
- [ ] Zillow data display
- [ ] Market anomaly badge
- [ ] Comparable sales
- [ ] Save property button
- [ ] Add to watchlist

**Phase 3 - Kanban Board**
- [ ] View saved properties by stage
- [ ] Drag and drop between stages
- [ ] Add notes to property
- [ ] Add priority flags
- [ ] Delete from saved

**Phase 4 - Watchlist & Alerts**
- [ ] Add property to watchlist
- [ ] Configure alert types
- [ ] View alert history
- [ ] Mark alerts as read
- [ ] Remove from watchlist

### File Structure Reference

```
salesweb-crawl/
├── frontend/                    # Next.js 14 frontend
│   ├── app/                     # App Router pages
│   ├── components/              # React components
│   ├── lib/                     # Utilities, API client
│   └── stores/                  # Zustand stores
├── webhook_server/              # FastAPI backend
│   ├── app.py                   # Main application
│   ├── routes/                  # API route handlers
│   └── services/                # Business logic
└── migrations/                  # Database migrations
```

---

## COMPLETE SYSTEM OVERVIEW (A to Z)

### The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        BIDNOLOGY - FORECLOSURE INVESTMENT PLATFORM              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐                 │
│  │ DATA SOURCE  │  →   │  INGESTION   │  →   │  ENRICHMENT  │                 │
│  │              │      │              │      │              │                 │
│  │  • Sheriff   │      │  • Playwright│      │  • Zillow API│                 │
│  │    Sales     │      │  • FastAPI   │      │  • 8 Endpts  │                 │
│  │    Website   │      │    Webhooks  │      │              │                 │
│  │  (21 NJ      │      │              │      │              │                 │
│  │   Counties)  │      │              │      │              │                 │
│  └──────────────┘      └──────────────┘      └──────────────┘                 │
│                                                           │                     │
│                                                           ▼                     │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐                 │
│  │  ANALYTICS   │  ←   │   STORAGE    │  ←   │    SUPABASE  │                 │
│  │              │      │              │      │              │                 │
│  │  • ROI       │      │  • PostgreSQL│      │  • Real-time │                 │
│  │  • Grading   │      │  • PostGIS   │      │  • REST API  │                 │
│  │  • Trends    │      │  • RLS       │      │  • Webhooks  │                 │
│  └──────────────┘      └──────────────┘      └──────────────┘                 │
│          │                                                                   │
│          ▼                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐                 │
│  │   FRONTEND   │  →   │      API     │  →   │    USERS     │                 │
│  │              │      │              │      │              │                 │
│  │  • React CRM │      │  • Express   │      │  • Investors │                 │
│  │  • Charts    │      │  • FastAPI   │      │  • Wholesalers│                 │
│  │  • Maps      │      │  • Endpoints │      │  • Flippers   │                 │
│  └──────────────┘      └──────────────┘      └──────────────┘                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## STEP-BY-STEP WORKFLOW

### STEP A: Data Source (Sheriff Sales Website)

```
┌─────────────────────────────────────────────────────────────┐
│  SOURCE: salesweb.civilview.com                             │
│  NJ Sheriff's Sale Foreclosure Listings                     │
├─────────────────────────────────────────────────────────────┤
│  • 21 NJ Counties (Atlantic → Warren)                       │
│  • Updated daily with new foreclosure listings             │
│  • Property Details:                                        │
│    - Address & Parcel ID                                    │
│    - Upset Price (minimum bid)                              │
│    - Judgment Amount                                        │
│    - Plaintiff & Attorney                                   │
│    - Owner Name                                             │
│    - Sale Date & Court                                      │
└─────────────────────────────────────────────────────────────┘
```

### STEP B: Data Ingestion (Scraping)

```
┌─────────────────────────────────────────────────────────────┐
│  INGESTION LAYER                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Playwright Scraper (Python)                         │   │
│  │  playwright_scraper.py                               │   │
│  │  • Browser automation (headless Chrome)              │   │
│  │  • County selection & date filtering                 │   │
│  │  • Property list extraction                          │   │
│  │  • Detail page scraping                              │   │
│  │  • Rate limiting & delays                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FastAPI Webhook Server                              │   │
│  │  webhook_server/ (port 8080)                         │   │
│  │  • POST /webhook/property                            │   │
│  │  • Receives scraped data                             │   │
│  │  • Validates & sanitizes                             │   │
│  │  • Triggers enrichment                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### STEP C: Data Storage (Supabase)

```
┌─────────────────────────────────────────────────────────────┐
│  SUPABASE DATABASE (PostgreSQL)                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Table: foreclosure_listings                         │   │
│  │  ───────────────────────────────────────────────    │   │
│  │  id (PK)                                            │   │
│  │  property_address                                    │   │
│  │  city, state, zip_code                              │   │
│  │  county_id (FK → nj_counties)                        │   │
│  │  parcel_id                                           │   │
│  │  upset_price, judgment_amount                        │   │
│  │  plaintiff, owner_name                               │   │
│  │  sale_date                                           │   │
│  │  zillow_enrichment_status                           │   │
│  │    → not_enriched / partially_enriched /            │   │
│  │      fully_enriched / auto_enriched                 │   │
│  │  created_at, updated_at                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Table: nj_counties                                  │   │
│  │  ───────────────────────────────────────────────    │   │
│  │  id (PK) → Essex = 2                                │   │
│  │  county_name                                         │   │
│  │  civilview_url                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### STEP D: Data Enrichment (Zillow API)

```
┌─────────────────────────────────────────────────────────────┐
│  ENRICHMENT SERVICE                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Trigger: Property created or manual request               │
│  Endpoint: POST /api/enrichment/properties/{id}/enrich     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ZillowEnrichmentService                            │   │
│  │  webhook_server/zillow_enrichment.py                │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  8 API Calls to Zillow (RapidAPI)                   │   │
│  │  ───────────────────────────────────────────────    │   │
│  │  1. pro_byaddress     → Basic info (zpid, zestimate)│   │
│  │  2. similar          → Comparable properties        │   │
│  │  3. nearby           → Nearby properties             │   │
│  │  4. pricehistory     → Price history                 │   │
│  │  5. taxinfo          → Tax history                   │   │
│  │  6. climate          → Climate risk data             │   │
│  │  7. walk_transit_bike→ Walk/bike/transit scores      │   │
│  │  8. ownerinfo        → Owner/agent info              │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Table: zillow_enrichment                            │   │
│  │  ───────────────────────────────────────────────    │   │
│  │  property_id (FK)                                    │   │
│  │  zpid                                                │   │
│  │  zestimate, bedrooms, bathrooms, sqft               │   │
│  │  similar_properties (comps)                          │   │
│  │  nearby_properties                                   │   │
│  │  price_history (JSONB)                               │   │
│  │  tax_history (JSONB)                                 │   │
│  │  climate_risk (JSONB)                                │   │
│  │  owner_info (JSONB)                                  │   │
│  │  images (array)                                      │   │
│  │  walk_score, transit_score, bike_score              │   │
│  │  raw_api_response (JSONB)                            │   │
│  │  endpoints_attempted (array)                         │   │
│  │  endpoints_succeeded (array)                         │   │
│  │  endpoint_errors (JSONB)                             │   │
│  │  api_call_count                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### STEP E: Investment Analysis (Planned)

```
┌─────────────────────────────────────────────────────────────┐
│  VALUATION & ANALYSIS ENGINE (Planned/Future)               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Using enriched Zillow data:                                │
│                                                             │
│  1. Valuation Methods:                                      │
│     • Price per Sq Ft comparison                           │
│     • Comparable sales analysis                            │
│     • Rental income approach                               │
│     • Cost approach                                        │
│                                                             │
│  2. Investment Metrics:                                     │
│     • Potential ROI                                         │
│     • Discount from market value                           │
│     • Repair cost estimates                                 │
│     • After-repair value (ARV)                              │
│                                                             │
│  3. Property Grading:                                       │
│     • Grade A: Premium deals (30%+ discount)               │
│     • Grade B: Good deals (20-30% discount)                │
│     • Grade C: Fair deals (10-20% discount)                │
│     • Grade D: Marginal (<10% discount)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### STEP F: API Layer (Data Serving)

```
┌─────────────────────────────────────────────────────────────┐
│  API ENDPOINTS                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  FastAPI Server (port 8080)                                 │
│  ───────────────────────────────────────────────────        │
│                                                             │
│  IMPLEMENTED:                                               │
│  ───────────────────────────────────────────────────        │
│  GET  /health                                    Health check│
│  POST /api/enrichment/properties/{id}/enrich    Enrich prop │
│                                                             │
│  ───────────────────────────────────────────────────        │
│  PLANNED:                                                    │
│  ───────────────────────────────────────────────────        │
│  GET  /api/properties                           List all     │
│  GET  /api/properties/{id}                    Get one       │
│  GET  /api/properties/search                   Search       │
│  GET  /api/properties/hot                      Hot deals    │
│  GET  /api/properties/{id}/analysis           Analysis     │
│  GET  /api/dashboard/stats                       Stats       │
│  GET  /api/counties                              Counties    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### STEP G: Frontend Display

```
┌─────────────────────────────────────────────────────────────┐
│  USER INTERFACE                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  DASHBOARD                                           │   │
│  │  ───────────────────────────────────────────────    │   │
│  │  • Total properties in database                     │   │
│  │  • New properties this week                         │   │
│  │  • Counties covered                                 │   │
│  │  • Average discount percentage                      │   │
│  │  • Hot deals (Grade A) count                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PROPERTY LISTINGS                                   │   │
│  │  ───────────────────────────────────────────────    │   │
│  │  • Table/Grid view                                  │   │
│  │  • Filters by county, price, discount, grade        │   │
│  │  • Sort by any field                                │   │
│  │  • Click for details                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PROPERTY DETAIL PAGE                               │   │
│  │  ───────────────────────────────────────────────    │   │
│  │  • Address, parcel ID, county                       │   │
│  │  • Upset price, judgment amount                     │   │
│  │  • Zestimate, bedrooms, bathrooms, sqft             │   │
│  │  • Comparable properties (comps)                     │   │
│  │  • Price history chart                              │   │
│  │  • Climate risk scores                              │   │
│  │  • Investment analysis (ROI, grade)                 │   │
│  │  • Walk/bike/transit scores                         │   │
│  │  • Owner/attorney info                              │   │
│  │  • Photos (if available)                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## COMPLETE DATA FLOW DIAGRAM

```
                      ┌─────────────────────┐
                      │  SalesWeb.CivilView │
                      │  .com (Sheriff      │
                      │   Sales Website)    │
                      └──────────┬──────────┘
                                 │
                                 ▼
                      ┌─────────────────────┐
                      │  Playwright Scraper │  ← Runs on schedule or manual
                      │  (browser automation)│
                      └──────────┬──────────┘
                                 │
                    POST /webhook/property
                                 │
                                 ▼
                      ┌─────────────────────┐
                      │   FastAPI Server    │
                      │  webhook_server/    │
                      │  • Validate data    │
                      │  • Insert to DB     │
                      │  • Trigger enrich  │
                      └──────────┬──────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
         ┌──────────────────┐    ┌─────────────────────┐
         │ foreclosure_     │    │  Background Task    │
         │ listings table   │    │  (async)            │
         └──────────────────┘    │  • Zillow API calls │
                                  │  • 8 endpoints      │
                                  └──────────┬──────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │ zillow_enrichment   │
                                  │ table               │
                                  └──────────┬──────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │  Update status:     │
                                  │  auto_enriched      │
                                  └─────────────────────┘

                    ┌─────────────────────────────────────┐
                    │                                     │
                    ▼                                     ▼
         ┌──────────────────┐                ┌──────────────────┐
         │   API REQUESTS   │                │  FUTURE:         │
         │   GET /properties│                │  Analysis Engine │
         │   /search        │                │  • Valuations    │
         │   /hot           │                │  • ROI calc      │
         └─────────┬────────┘                │  • Grading       │
                   │                         └──────────────────┘
                   ▼
         ┌──────────────────┐
         │   FRONTEND UI    │
         │  • React CRM     │  ← Planned
         │  • Dashboard     │
         │  • Property List │
         │  • Detail Pages  │
         └──────────────────┘
                   │
                   ▼
         ┌──────────────────┐
         │     USERS        │
         │  • Investors     │
         │  • Wholesalers   │
         │  • Flippers      │
         └──────────────────┘
```

---

## CURRENT STATUS vs PLANNED

| Component | Status | Notes |
|-----------|--------|-------|
| **Data Source** | ✅ Complete | Sheriff sales website identified |
| **Playwright Scraper** | 🟡 Partial | Exists, needs integration |
| **FastAPI Webhook Server** | ✅ Complete | Running on port 8080 |
| **Supabase Database** | ✅ Complete | Tables setup, data flowing |
| **Zillow Enrichment** | ✅ Complete | 8 endpoints working |
| **Property API** | 🟡 Planned | Endpoints defined, not built |
| **Investment Analysis** | 🔴 Not Started | Valuation engine not built |
| **React CRM Frontend** | 🟡 Planned | Design exists, not built |
| **User Authentication** | 🔴 Not Started | No auth layer |
| **Payment Integration** | 🔴 Not Started | No monetization |

---

## ENVIRONMENT & CONFIGURATION

### Required Environment Variables (.env)
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key
RAPIDAPI_KEY=ddc80cadcamsh4b4716e724116a2p122560jsnfcec8e2250a9
OPENAI_API_KEY=your_openai_key
```

### RapidAPI Status
- **Free Tier**: 250 requests/month (Zillow)
- **API Host**: `private-zillow.p.rapidapi.com`

---

## KEY FILES

| File | Purpose | Status |
|------|---------|--------|
| `playwright_scraper.py` | Main scraper | ✅ Complete |
| `ai_full_extractor.py` | GPT-4o mini extraction | ✅ Complete |
| `scraper_helper.py` | County mappings, DB helpers | ✅ Complete |
| `webhook_server/app.py` | FastAPI application | ✅ Complete |
| `webhook_server/enrichment_routes.py` | Enrichment API routes | ✅ Complete |
| `webhook_server/zillow_enrichment.py` | Zillow API service | ✅ Complete |

---

## COMMANDS

```bash
# Run FastAPI server
cd webhook_server && python -m uvicorn app:app --reload --host 0.0.0.0 --port 8080

# Run scraper (single county)
./venv/bin/python playwright_scraper.py --counties Essex

# Run scraper (multiple counties)
./venv/bin/python playwright_scraper.py --counties Essex Middlesex Union

# Run scraper (incremental mode)
./venv/bin/python playwright_scraper.py --counties Essex --incremental

# Enrich a property
curl -X POST http://localhost:8080/api/enrichment/properties/{id}/enrich

# Health check
curl http://localhost:8080/health
```

---

## AI EXTRACTION WITH SCREENSHOT FALLBACK

### Quality-First Multi-Stage Extraction

The system uses a sophisticated multi-stage extraction approach that always prioritizes data quality:

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: GPT-4o mini Text Extraction (Primary)                 │
│  ────────────────────────────────────────────────────────────  │
│  • Extracts all fields from raw HTML                           │
│  • Cost-effective: ~$0.15/1M input tokens                      │
│  • Fast processing                                            │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: Quality Check                                       │
│  ────────────────────────────────────────────────────────────  │
│  • Validates critical fields:                                  │
│    - property_address (most important)                         │
│    - sale_date OR monetary field (at least one)                │
│  • Calculates quality score (0.0 - 1.0)                         │
│  • Reports warnings for missing recommended fields             │
└───────────────────────┬─────────────────────────────────────────┘
                        │
            ┌───────────┴───────────┐
            │ Quality Check Passed?  │
            └───────────┬───────────┘
                        │
         ┌──────────────┴──────────────┐
         │ No                         │ Yes
         ▼                            ▼
┌────────────────────────┐   ┌────────────────────────┐
│  STAGE 3: Screenshot    │   │  Use Text Result        │
│  + GPT-4o Vision        │   │  (Done - Success!)      │
│  ──────────────────────│   └────────────────────────┘
│  • crawl4ai captures   │
│    full page screenshot│
│  • GPT-4o Vision       │
│    extracts from image │
│  • Quality comparison  │
│  • Keep better result  │
└────────────────────────┘
```

### Key Features

- **Always GPT-4o**: Never compromises quality - always uses OpenAI GPT-4o models
- **Automatic Fallback**: Triggers only when quality check fails
- **Smart Comparison**: Uses the result with higher quality score
- **Cost-Aware**: Primary uses GPT-4o mini ($0.15/1M), fallback uses GPT-4o Vision only when needed
- **Logging**: Scraper logs when fallback is triggered for monitoring

### Quality Thresholds

**Critical Fields (must have at least one from each group):**
- `property_address` - Primary identifier
- `sale_date`, `opening_bid`, `approx_upset`, or `judgment_amount` - At least one monetary/date field

**Quality Score Calculation:**
- Base: % of total fields present (27 fields total)
- Penalty: -0.3 for each missing critical field
- Pass: No missing critical fields

### Implementation Files

| File | Purpose |
|------|---------|
| `ai_full_extractor.py` | Main extraction module with fallback |
| `check_extraction_quality()` | Quality validation function |
| `extract_with_screenshot_fallback()` | Unified extraction with auto-fallback |
| `capture_screenshot_crawl4ai()` | Screenshot capture |
| `extract_from_screenshot()` | GPT-4o Vision extraction |

---

## DEAL INTELLIGENCE API SYSTEM (4 Core Features)

### Overview

A comprehensive deal intelligence system for foreclosure property analysis with 21 API endpoints:

| Feature | Description | Endpoints |
|---------|-------------|------------|
| **Market Anomaly Detection** | Find underpriced properties | 4 |
| **Comparable Sales Analysis** | AI-powered ARV calculation | 3 |
| **Saved Properties + Kanban** | Pipeline management | 5 |
| **Watchlist + Alerts** | Track properties with notifications | 9 |

### API Endpoints

```
/api/deal-intelligence
├── /settings
│   ├── GET    /admin           - Get admin feature settings
│   └── PUT    /admin           - Update admin feature settings
├── /anomalies
│   ├── GET    /                - List all anomalies
│   ├── GET    /{property_id}   - Get anomalies for property
│   ├── POST   /analyze/{id}    - Analyze property for anomalies
│   └── PUT    /{id}/verify     - Verify/correct anomaly
├── /comps
│   ├── GET    /{property_id}   - Get comparable properties
│   ├── POST   /{id}/analyze    - Create comps analysis
│   └── PUT    /{analysis_id}    - Update analysis (manual ARV)
├── /saved
│   ├── GET    /{user_id}       - Get saved properties
│   ├── GET    /{user_id}/kanban - Get Kanban board
│   ├── POST   /                - Save property
│   ├── PUT    /{id}/stage      - Move to Kanban stage
│   └── DELETE /{id}            - Unsave property
├── /watchlist
│   ├── GET    /{user_id}       - Get watchlist
│   ├── POST   /                - Add to watchlist
│   └── DELETE /{id}            - Remove from watchlist
└── /alerts
    ├── GET    /{user_id}       - Get alerts
    ├── PUT    /{id}/read       - Mark as read
    ├── PUT    /{user_id}/read-all - Mark all as read
    └── DELETE /{id}            - Delete alert
```

### Feature Toggle System

Three-tier settings architecture with lock flags:

1. **Admin Level** (`deal_features_admin_settings` table)
   - Global feature toggles
   - AI quality thresholds
   - Lock flags to prevent lower-level overrides

2. **County Level** (via settings service)
   - Per-county feature overrides
   - Respects admin lock flags

3. **User Level** (via settings service)
   - Per-user preferences
   - Respects county and admin lock flags

### AI Data Quality Monitoring

The `ai_quality_monitor.py` module prevents false positives from minimal data:

- **Anomaly Detection**: Requires min 3 comps, 0.7 confidence
- **Comps Analysis**: Max 1 mile distance, 365 days age, min 3 samples
- **Validation**: All AI analysis must pass quality checks before showing to users

### Database Schema

New tables (see `migrations/add_deal_intelligence_features.sql`):
- `deal_features_admin_settings` - Feature toggles and AI thresholds
- `market_anomalies` - Price anomaly detection results
- `comparable_sales_analysis` - AI-powered comps analysis
- `saved_properties` - Saved properties with Kanban stage
- `user_watchlist` - Properties users are watching
- `user_alerts` - Alert queue for watchlist items
- `investment_strategies` - User strategy templates
- `user_portfolio` - Acquired properties tracking
- `shared_properties` - Team collaboration
- `property_comments` - Comments on properties
- `property_notes` - User notes per property
- `due_diligence_checklists` - Task tracking per property

### Kanban Stages

Properties move through stages:
```
researching → analyzing → due_diligence → bidding → won
                                                    → lost
                                                    → archived
```

### Implementation Files

| File | Purpose |
|------|---------|
| `webhook_server/deal_intelligence_routes.py` | 21 API endpoints |
| `webhook_server/feature_toggle_service.py` | Feature toggle system |
| `webhook_server/market_anomaly_service.py` | Price anomaly detection |
| `webhook_server/comparable_sales_service.py` | Comps analysis |
| `webhook_server/saved_properties_service.py` | Save + Kanban |
| `webhook_server/watchlist_service.py` | Watchlist + alerts |
| `webhook_server/ai_quality_monitor.py` | Data quality validation |
| `webhook_server/models/deal_intelligence.py` | Pydantic models |
| `migrations/add_deal_intelligence_features.sql` | Database schema |

---

## ML-BASED PROPERTY RANKING SYSTEM

### Overview

Personalized property ranking using machine learning features with human feedback loop for continuous improvement.

### Features

| Feature | Description | Weight |
|---------|-------------|--------|
| Price-to-Value | Upset price vs Zestimate ratio | 35% |
| Market Anomaly | Z-score deviation from area norms | 20% |
| Time Urgency | Days until sale date | 15% |
| Property Type | Matches user preferences | 10% |
| Price Range | Within user budget | 10% |
| Location | Preferred counties | 10% |

### Database Schema

6 tables (see `migrations/add_ml_ranking_tables.sql`):
- `deal_intelligence_investor_criteria` - User investment preferences
- `deal_intelligence_model_weights` - Scoring model weights
- `deal_intelligence_property_scores` - Calculated scores per property
- `deal_intelligence_score_feedback` - Human feedback loop
- `deal_intelligence_ranking_history` - Historical rankings
- `deal_intelligence_analytics` - Performance metrics

### API Endpoints

```
/api/deal-intelligence/ranking
├── GET  /criteria/{user_id}           - Get investor criteria
├── PUT  /criteria/{user_id}           - Update investor criteria
├── GET  /property/{property_id}/{user_id} - Get property score
├── POST /rank                        - Batch rank properties
├── GET  /weights                     - Get model weights
├── PUT  /weights                     - Update model weights
└── POST /feedback                    - Submit feedback
```

### Implementation Files

| File | Purpose |
|------|---------|
| `webhook_server/ml_ranking_service.py` | ML ranking service |
| `webhook_server/models/deal_intelligence.py` | Pydantic models |

---

## MOBILE PUSH NOTIFICATIONS

### Overview

Cross-platform push notification system for iOS, Android, and Web devices with queue-based delivery and notification preferences.

### Platforms Supported

| Platform | Service | Status |
|----------|---------|--------|
| Android | Firebase Cloud Messaging (FCM) | ✅ Implemented |
| iOS | Apple Push Notification Service (APNs) | ✅ Implemented |
| Web | Web Push API | Planned |

### Database Schema

4 tables (see `migrations/add_push_notification_tables.sql`):
- `mobile_push_tokens` - Device token registry
- `push_notification_queue` - Notification queue
- `push_notification_history` - Sent notifications log
- `push_notification_templates` - Message templates

### API Endpoints

```
/api/deal-intelligence/notifications
├── POST /register                    - Register device token
├── POST /send                        - Send notification
├── POST /process-queue               - Process pending notifications
└── GET  /{user_id}                   - Get notification history
```

### Background Worker

Processes notification queue continuously:

```bash
# Run once
python -m webhook_server.push_notification_worker --once

# Run continuously
python -m webhook_server.push_notification_worker --interval 30 --batch-size 100
```

### Environment Variables Required

```bash
# Android (FCM)
FCM_SERVER_KEY=AAAAbbbbCCCCdddd...

# iOS (APNs) - Token Auth (Recommended)
APNS_AUTH_KEY_PATH=/path/to/AuthKey_ABC123.p8
APNS_KEY_ID=ABC123
APNS_TEAM_ID=DEF456
APNS_BUNDLE_ID=com.yourcompany.yourapp
APNS_USE_SANDBOX=true  # true for dev, false for prod
```

### Documentation

See `docs/MOBILE_PUSH_INTEGRATION.md` for:
- Mobile app integration guide (iOS Swift, Android Kotlin, React Native, Flutter)
- FCM/APNs setup instructions
- Testing procedures
- Production deployment guide

### Implementation Files

| File | Purpose |
|------|---------|
| `webhook_server/push_notification_service.py` | Push notification service |
| `webhook_server/push_notification_worker.py` | Background worker |
| `.env.example.push` | Environment variable template |

---

## BACKEND ARCHITECTURE OVERVIEW

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API Framework** | FastAPI (Python 3.12) | REST API, async support |
| **Database** | Supabase (PostgreSQL) | Primary data storage, RLS |
| **Auth** | Supabase Auth + JWT | User authentication |
| **Webhooks** | changedetection.io + pg_cron | Scheduled scraping triggers |
| **Scraping** | Playwright + GPT-4o | Browser automation + AI extraction |
| **Enrichment** | RapidAPI Zillow | Property data enrichment |
| **Scheduling** | pg_cron | Database cron jobs |

### Backend File Structure

```
webhook_server/
├── app.py                          # Main FastAPI application (all routes)
├── auth.py                         # JWT validation, UserContext
├── auth_routes.py                  # POST /auth/signup, /signin, /verify
├── enrichment_routes.py            # GET/POST /api/enrichment/*
├── deal_intelligence_routes.py    # 21+ /api/deal-intelligence/* endpoints
│
├── Services Layer:
├── zillow_enrichment.py           # Zillow API integration (8 endpoints)
├── settings_service.py            # Three-tier settings (admin/county/user)
├── feature_toggle_service.py      # Feature flag resolution
├── market_anomaly_service.py      # Price outlier detection
├── comparable_sales_service.py    # AI-powered comps analysis
├── saved_properties_service.py    # Save + Kanban management
├── watchlist_service.py           # Watchlist + alert generation
├── investment_service.py          # Strategy templates
├── portfolio_service.py           # Acquired properties tracking
├── notes_service.py               # Property notes CRUD
├── checklist_service.py           # Due diligence tasks
├── collaboration_service.py       # Team sharing
├── renovation_service.py          # GPT-4o Vision photo analysis
├── push_notification_service.py   # FCM/APNs push notifications
├── ml_ranking_service.py          # Property scoring ML
├── ai_quality_monitor.py          # Data quality validation
├── skip_trace_service.py          # Owner contact info
│
├── Models:
└── models/deal_intelligence.py    # Pydantic request/response models
```

### API Route Structure

```
FastAPI Application (app.py)
│
├── Health Check
│   └── GET /health
│
├── Authentication Routes (auth_routes.py)
│   ├── POST /auth/signup
│   ├── POST /auth/signin
│   ├── POST /auth/verify
│   ├── GET  /auth/me
│   ├── PUT  /auth/me/metadata
│   ├── GET  /auth/admin/users
│   └── POST /auth/admin/{user_id}/role
│
├── Enrichment Routes (enrichment_routes.py)
│   ├── POST /api/enrichment/properties/{id}/enrich
│   ├── GET  /api/enrichment/properties/{id}
│   └── GET  /api/enrichment/status
│
├── Deal Intelligence Routes (deal_intelligence_routes.py)
│   ├── Feature Settings (2 endpoints)
│   ├── Market Anomalies (4 endpoints)
│   ├── Comparable Sales (3 endpoints)
│   ├── Investment Strategies (6 endpoints)
│   ├── Saved Properties + Kanban (5 endpoints)
│   ├── Watchlist + Alerts (9 endpoints)
│   ├── Portfolio Tracking (5 endpoints)
│   ├── Notes (4 endpoints)
│   ├── Due Diligence Checklists (3 endpoints)
│   ├── Team Collaboration (4 endpoints)
│   ├── Renovation Estimator (2 endpoints)
│   ├── ML Ranking (7 endpoints)
│   └── Push Notifications (4 endpoints)
│
└── Webhook Routes (app.py)
    ├── POST /webhooks/changedetection   # changedetection.io trigger
    ├── POST /webhooks/scheduled          # pg_cron scheduled scrape
    └── POST /webhooks/property           # Individual property webhook
```

### Database Schema Summary

| Table | Purpose | Rows |
|-------|---------|------|
| `foreclosure_listings` | Sheriff sale properties | Primary table |
| `zillow_enrichment` | Zillow API data | 1:1 with listings |
| `nj_counties` | County reference (21 counties) | Lookup |
| `deal_features_admin_settings` | Feature toggles (singleton) | Settings |
| `market_anomalies` | Price anomaly flags | Analysis |
| `comparable_sales_analysis` | AI-powered comps | Analysis |
| `saved_properties` | User saved + Kanban stage | User data |
| `user_watchlist` | Watched properties | User data |
| `user_alerts` | Alert queue | Notifications |
| `investment_strategies` | Strategy templates | User data |
| `user_portfolio` | Acquired properties | User data |
| `property_notes` | User notes | User data |
| `due_diligence_checklists` | Task tracking | User data |
| `auth_users` | Supabase Auth users | Authentication |

### County ID Mapping (Corrected from SalesWeb dropdown)

| County | ID | Watch Title Format |
|--------|-----|-------------------|
| Atlantic | 25 | `CivilView | Atlantic` |
| Bergen | 7 | `CivilView | Bergen` |
| Burlington | 3 | `CivilView | Burlington` |
| Camden | 1 | `CivilView | Camden` |
| Cape May | 52 | `CivilView | Cape May` |
| Cumberland | 6 | `CivilView | Cumberland` |
| Essex | 2 | `CivilView | Essex` |
| Gloucester | 19 | `CivilView | Gloucester` |
| Hudson | 10 | `CivilView | Hudson` |
| Hunterdon | 32 | `CivilView | Hunterdon` |
| Middlesex | 73 | `CivilView | Middlesex` |
| Monmouth | 8 | `CivilView | Monmouth` |
| Morris | 9 | `CivilView | Morris` |
| Passaic | 17 | `CivilView | Passaic` |
| Salem | 20 | `CivilView | Salem` |
| Union | 15 | `CivilView | Union` |

> Note: County IDs are **non-sequential** as per the actual dropdown on salesweb.civilview.com

### Webhook Integration (changedetection.io)

**Configuration:**
- **Endpoint:** `POST /webhooks/changedetection`
- **Secret:** `X-Webhook-Secret` header (optional)
- **Watch Title Format:** `CivilView | {CountyName}`
- **All counties use the SAME endpoint** - county extracted from `watch_title`

**Request Format:**
```json
{
  "watch_title": "CivilView | Essex",
  "watch_url": "https://salesweb.civilview.com/Sales/SalesSearch?countyId=2",
  "status": 200
}
```

### pg_cron Scheduled Jobs

**Migration:** `migrations/add_pg_cron_jobs.sql`

**Schedule:** Every 4 hours (`0 */4 * * *`)

```sql
SELECT cron.schedule(
    'scrape-all-counties-every-4-hours',
    '0 */4 * * *',
    $$
    SELECT net.http_post(
        'https://your-domain.com/webhooks/scheduled'::text,
        headers: '{"X-Schedule-Secret": "YOUR_SCHEDULE_SECRET"}'::jsonb,
        body: '{}'::jsonb,
        timeout_milliseconds := 300000
    );
    $$
);
```

### Authentication Flow

```
┌─────────────┐    POST /auth/signup    ┌──────────────┐
│   Client    │ ───────────────────────► │  Supabase   │
│ (Frontend)  │                         │    Auth      │
└─────────────┘                         └──────┬───────┘
                                              │
                                              ▼
                                    ┌────────────────────┐
                                    │ auth_users table   │
                                    │ + JWT tokens       │
                                    └─────────┬──────────┘
                                              │
                 ┌────────────────────────────┴────────────────────────────┐
                 │                                                          │
                 ▼                                                          ▼
        ┌────────────────┐                                    ┌────────────────┐
        │ JWT Access     │                                    │ Refresh Token │
        │ Token          │                                    │ (stored in     │
        │ (short-lived)  │                                    │  cookie)       │
        └────────┬───────┘                                    └────────────────┘
                 │
                 │ Authorization: Bearer <token>
                 │
    ┌────────────┴──────────────┐
    │                           │
    ▼                           ▼
┌─────────────┐          ┌─────────────┐
│  Protected  │          │   Public    │
│  Routes     │          │   Routes    │
└─────────────┘          └─────────────┘
```

### Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Webhook Secrets
WEBHOOK_SECRET=your_webhook_secret
SCHEDULE_SECRET=your_schedule_secret

# External APIs
RAPIDAPI_KEY=your_rapidapi_key
OPENAI_API_KEY=your_openai_key
```

---

## CURRENT WORKFLOW OVERVIEW (Dec 31, 2025)

### Recent Changes (This Session)

| Feature | Status | Details |
|---------|--------|---------|
| **Mobile Pagination** | ✅ Complete | Compact text, chevron icons on mobile, stacked controls |
| **Mobile Filter Dropdowns** | ✅ Complete | Bottom sheet style with backdrop, slide-up animation |
| **Filter Labels on Mobile** | ✅ Complete | Labels next to icons with compact sizing |
| **Auction Day Rename** | ✅ Complete | "Day" changed to "Auction Day" on mobile only |
| **Mobile Sort Order Filter** | ✅ Complete | New mobile-only "Order" filter for auction date (ascending/descending/normal) |
| **Desktop Dropdown Fix** | ✅ Complete | Fixed dropdown positioning bug by changing overflow behavior |

### Frontend Changes Summary

**HomePageClient.tsx (Mobile UI Improvements):**

Pagination (mobile-friendly):
- Compact "Showing" text with shortened format on mobile
- Chevron icons instead of text arrows on mobile
- Vertically stacked controls on mobile

Filter Dropdowns (bottom sheet pattern):
- Fixed positioning with backdrop overlay on mobile
- Slide-up animation from bottom
- Mobile-specific header with close button
- "Done" button at bottom for mobile
- Desktop keeps regular dropdown behavior

Filter Buttons (with labels):
- Added labels next to all filter icons on mobile
- Smaller text sizes (text-xs vs text-sm) on mobile
- Smaller icons (16px vs 18px) on mobile
- "Day" changed to "Auction Day" on mobile only

New Sort Order Filter (mobile-only):
- "Order" button with sort icon
- Bottom sheet dropdown with 3 options:
  - Descending (Newest first)
  - Ascending (Oldest first)
  - Normal (Default order)

Desktop Dropdown Fix:
- Changed filter container overflow from `overflow-x-auto` to `overflow-x-auto md:overflow-visible`
- Allows desktop dropdowns to extend beyond container without clipping
- Maintains horizontal scroll on mobile

### Git Status

```
Branch: main
Status: Committed and Pushed
Commit: "feat: Improve mobile UI with bottom sheet dropdowns and filter enhancements"
Files Changed: 8 files (+473 insertions, -239 deletions)
```

---

## PREVIOUS SESSION (Dec 30, 2025)

### Recent Changes (Previous Session)

| Feature | Status | Details |
|---------|--------|---------|
| **CSV Export Feature** | ✅ Complete | Export filtered or all properties to CSV |
| **Stats Display Update** | ✅ Complete | Changed "Enriched Properties" to "Total Properties" with showing/total count |
| **UI Cleanup** | ✅ Complete | Removed Beds/Baths/SQFT filters, Tax/Comps/Skip Trace buttons, NY/CA ticker |
| **Property Placeholder** | ✅ Complete | Replaced with transparent icon, removed borders |
| **Split View Component** | ✅ Complete | Added PropertySplitView for property browsing |

### Frontend Changes Summary

**HomePageClient.tsx:**
- Added `exportToCSV()` function with filtered/all options
- Added export dropdown UI with click-outside handler
- Changed stats to show "showing / total" format
- Removed Beds, Baths, SQFT filter state and UI
- Removed Tax History, Comparables, Skip Trace filter buttons
- Removed `ENRICHED_PROPERTY_IDS` hardcoded filter (now ready to show all properties)

**Header.tsx:**
- Removed NY/CA live auction ticker from top right

**PropertyRow.tsx & PropertySplitView.tsx:**
- Removed borders from property thumbnails for transparent placeholder support

**Assets:**
- Replaced `House Placeholder.png` with `house placeholder icon.png` (transparent background)

### Git Status

```
Branch: feature/dashboard-redesign-investor-focus
Status: Committed and Pushed
Commit: "feat(frontend): add CSV export, update stats display, remove filters and ticker"
Files Changed: 10 files (+929 insertions, -249 deletions)
```

### Implementation Status

| Feature | Endpoints | API Status | Service Status | DB Schema |
|---------|-----------|------------|----------------|-----------|
| **Feature Toggle System** | 2 | ✅ Passing | ✅ Complete | ✅ Complete |
| **Investment Strategies** | 6 | ✅ Fixed | ✅ Complete | ✅ Complete |
| **Market Anomaly Detection** | 4 | ✅ Passing | ✅ Complete | ✅ Complete |
| **Comparable Sales Analysis** | 3 | ⚠️ 404* | ✅ Complete | ✅ Complete |
| **Saved Properties + Kanban** | 5 | ✅ Passing | ✅ Complete | ✅ Complete |
| **Watchlist + Alerts** | 9 | ✅ Passing | ✅ Complete | ✅ Complete |
| **Portfolio Tracking** | 5 | ✅ Passing | ✅ Complete | ✅ Complete |
| **Property Notes** | 4 | ✅ Passing | ✅ Complete | ✅ Complete |
| **Due Diligence Checklist** | 3 | ✅ Passing | ✅ Complete | ✅ Complete |
| **Team Collaboration** | 4 | 🟡 TODO | 🟡 TODO | ✅ Complete |
| **Renovation Estimator** | 2 | 🟡 TODO | 🟡 TODO | ✅ Complete |
| **Mobile Push Notifications** | 4 | 🟡 TODO | ✅ Complete | ✅ Complete |
| **CSV Export** | 1 | 🟡 TODO | 🟡 TODO | N/A |

\* *Comps endpoint returns 404 when no analysis exists - expected behavior*

### Core API Test Results

```
Server: http://localhost:8080
Test Date: Dec 28, 2025
Success Rate: 83.3% (10/12 core endpoints)
```

**Passing Endpoints:**
- ✅ GET `/health` - Server health check
- ✅ GET `/api/deal-intelligence/settings/admin` - Admin feature settings
- ✅ POST `/api/deal-intelligence/strategies` - Create investment strategy
- ✅ GET `/api/deal-intelligence/strategies/{user_id}` - List strategies
- ✅ GET `/api/deal-intelligence/watchlist/{user_id}` - Get watchlist
- ✅ POST `/api/deal-intelligence/watchlist` - Add to watchlist
- ✅ GET `/api/deal-intelligence/portfolio/{user_id}` - Get portfolio
- ✅ GET `/api/deal-intelligence/saved/{user_id}` - Get saved properties
- ✅ POST `/api/deal-intelligence/notes` - Add property note
- ✅ GET `/api/deal-intelligence/anomalies` - List market anomalies
- ✅ GET `/api/deal-intelligence/checklist/{property_id}` - Get checklist

**Expected 404s (No Data Yet):**
- ⚠️ GET `/api/deal-intelligence/comps/{property_id}` - Returns 404 when no analysis exists

### Recent Fixes Applied

| Issue | File | Fix |
|-------|------|-----|
| `target_roi` column not found | `investment_service.py` | Changed to `min_fix_and_flip_profit` |
| `max_rehab_cost` column not found | `investment_service.py` | Changed to `max_repair_cost` |
| `strategy_name` vs `name` mismatch | `investment_service.py`, models, routes | Updated to use `name` (DB column) |
| Portfolio entry duplicate error | `portfolio_service.py` | Added upsert logic to update existing entries |

### Three-Tier Feature Toggle Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Level 1: Admin Settings (deal_features_admin_settings)     │
│  ───────────────────────────────────────────────────────────│
│  • Global feature toggles (12 features)                     │
│  • AI quality thresholds                                    │
│  • Lock flags (prevent lower-level overrides)               │
│  • Default: export_csv ✓, save_property ✓, market_anomaly ✓│
└────────────────────────┬────────────────────────────────────┘
                         │ Respects locks
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Level 2: County Settings (deal_features_county_settings)  │
│  ───────────────────────────────────────────────────────────│
│  • Per-county feature overrides                             │
│  • County-level lock flags                                  │
│  • Inherits admin defaults                                  │
└────────────────────────┬────────────────────────────────────┘
                         │ Respects locks
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Level 3: User Preferences (deal_features_user_preferences)│
│  ───────────────────────────────────────────────────────────│
│  • Per-user feature preferences                             │
│  • Opt-in/opt-out for each feature                          │
│  • Inherits county/admin defaults                           │
└─────────────────────────────────────────────────────────────┘
```

### Kanban Pipeline Stages

```
┌─────────────┐    ┌─────────────┐    ┌────────────────┐
│ researching │ →  │ analyzing   │ →  │ due_diligence  │
└─────────────┘    └─────────────┘    └────────┬───────┘
                                            │
                           ┌────────────────┴────────────────┐
                           ▼                                 ▼
                    ┌─────────────┐                  ┌─────────────┐
                    │   bidding   │ ────────────────►│    won      │
                    └─────────────┘                  └─────────────┘
                           │                                 │
                           ▼                                 ▼
                    ┌─────────────┐                  ┌─────────────┐
                    │    lost     │                  │  archived   │
                    └─────────────┘                  └─────────────┘
```

### Next Immediate Steps

| Priority | Task | Dependencies |
|----------|------|--------------|
| 1 | Complete remaining API routes (Team Collab, Renovation, Export) | None |
| 2 | Integration testing for all 38 endpoints | Routes complete |
| 3 | Frontend integration planning | API complete |
| 4 | Production deployment planning | All tests passing |

### Database Migration Status

```sql
-- Applied migrations:
✅ add_deal_intelligence_features.sql   (13 tables)
✅ add_deal_intelligence_api_tables.sql (API tracking)
✅ add_push_notification_tables.sql    (4 tables)
✅ add_ml_ranking_tables.sql            (6 tables)

-- Total new tables: 23
-- All migrations committed to branch
```

### Service Files Status

| File | Status | Notes |
|------|--------|-------|
| `feature_toggle_service.py` | ✅ Complete | 12 features, 3-tier resolution |
| `investment_service.py` | ✅ Fixed | Column name mismatches resolved |
| `market_anomaly_service.py` | ✅ Complete | Z-score detection |
| `comparable_sales_service.py` | ✅ Complete | AI-powered comps |
| `saved_properties_service.py` | ✅ Complete | Kanban stages |
| `watchlist_service.py` | ✅ Complete | Alert generation |
| `portfolio_service.py` | ✅ Complete | Upsert logic added |
| `notes_service.py` | ✅ Complete | CRUD operations |
| `checklist_service.py` | ✅ Complete | Task tracking |
| `collaboration_service.py` | 🟡 TODO | Team sharing |
| `renovation_service.py` | 🟡 TODO | GPT-4o Vision |
| `push_notification_service.py` | ✅ Complete | FCM/APNs |
| `deal_intelligence_routes.py` | 🟡 Partial | 21/38 endpoints |

---

## COMPLETED RECENTLY (Dec 28, 2025)

### Deal Intelligence (4 Features)
- [x] **Screenshot fallback system** - crawl4ai + GPT-4o Vision for quality assurance
- [x] **Deal Intelligence API** - 4 core features with 21 endpoints
- [x] **Feature toggle system** - Three-tier (admin/county/user) with lock flags
- [x] **AI Quality Monitor** - Prevents false positives from minimal data
- [x] **Database migration** - All tables for deal intelligence features
- [x] **Kanban board system** - Pipeline management for saved properties
- [x] **Watchlist + Alerts** - Property tracking with notifications

### ML Ranking System
- [x] **ML Ranking Database** - 6 tables for property scoring
- [x] **ML Ranking Service** - 6 scoring dimensions with confidence weighting
- [x] **Human Feedback Loop** - Continuous learning from user interactions
- [x] **Investor Criteria** - Personalized preferences per user
- [x] **Model Weights** - Configurable scoring weights

### Push Notifications (iOS/Android)
- [x] **FCM Integration** - Full Android push support
- [x] **APNs Integration** - Full iOS push with token-based auth
- [x] **Queue System** - Background processing worker
- [x] **Template System** - Consistent messaging templates
- [x] **Notification Preferences** - User opt-in/out per type
- [x] **Quiet Hours** - Time-based notification scheduling
- [x] **Mobile Integration Guide** - Complete docs for iOS/Android apps

---

## NEXT STEPS (Priority Order)

1. **Complete Scraper Integration** - Connect Playwright scraper to webhook
2. **Build Property API** - GET endpoints for listings, search, details
3. **Build Valuation Engine** - ROI calculator, grading system
4. **Build React Dashboard** - Property listings, filters, detail pages
5. **Add Authentication** - User accounts, subscriptions
6. **Add Payment** - Stripe for premium access

---

## LEGACY: Current Work Section (Dec 27, 2025)

### Active Task: Zillow RapidAPI Enrichment System + Deal Intelligence
Building a comprehensive enrichment system with:
- Three-tier configurable settings (Admin → County → User)
- Adaptive Learning-to-Rank Deal Intelligence System

### Status: Documentation Complete, Implementation Pending
- ✅ All 50+ RapidAPI endpoints explored and cataloged
- ✅ 13 final endpoints selected and tested
- ✅ Three-tier settings system designed (admin, county, user)
- ✅ Template presets defined (Minimal, Flipper, Landlord, Thorough)
- ✅ External skip tracing integration documented
- ✅ **Adaptive Learning-to-Rank Deal Intelligence System designed**
- ✅ Complete implementation workflow created (13 files, 8,400+ lines)
- ⏳ **NEXT: Implement database migration, services, and enrichment logic**

See docs/ for detailed documentation on the planned enrichment system.

---

## LEGACY: AI Extraction Method - LOCKED

**DO NOT change the extraction method without explicit reason and testing.**

- ✅ **USE**: `playwright_scraper.py` with `ai_full_extractor.py`
- ❌ **DO NOT USE**: Any `.DEPRECATED` files
- ❌ **DO NOT ADD**: Fallback to mechanical extraction (regex/BeautifulSoup)
- ❌ **DO NOT SKIP**: AI extraction to save cost

See `EXTRACTION_METHOD_LOCKED.md` for full details.

---

## Related Documentation

- `EXTRACTION_METHOD_LOCKED.md` - Extraction method policy (LOCKED)
- `AI_INTEGRATION_SETUP.md` - OpenAI integration setup
- `TECHNICAL_DOCS.md` - Technical architecture
- `INCREMENTAL_SETUP.md` - Incremental mode setup
- `ENDPOINT_CATALOG.md` - Zillow RapidAPI endpoint catalog
