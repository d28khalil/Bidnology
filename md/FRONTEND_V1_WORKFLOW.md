# V1 Frontend Workflow - DealFlow

**V1 Core Mission:** Feed → Auto-Enrich → Identify Worthwhile Properties Quickly

---

## V1 Scope

### 8 Core Features (V1 Only)

| # | Feature | Frontend Component | Status |
|---|---------|-------------------|--------|
| 1 | **Property Feed** | Properties page with filters | ✅ Backend Ready |
| 2 | **Auto-Enrichment** | Auto-loads on property detail | ✅ Backend Ready |
| 3 | **Market Anomaly Detection** | Hot deal badges + anomaly panel | ✅ Backend Ready |
| 4 | **Comparable Sales** | Comps tab on property detail | ✅ Backend Ready |
| 5 | **Saved Properties + Kanban** | Saved/Kanban page | ✅ Backend Ready |
| 6 | **Watchlist + Alerts** | Watchlist page + alert badges | ✅ Backend Ready |
| 7 | **Deal Criteria** | Deal criteria form + My Matches filter | ⏳ To Build |
| 8 | **AI Data Quality Scoring** | Data quality badge + warnings | ⏳ To Build |

### V1 NOT Includes (V2 Only)
- Portfolio Tracking
- Team Collaboration
- Investment Strategies
- Renovation Estimator (GPT-4o Vision)
- Mobile Push Notifications
- SMS Notifications

---

## V1 Frontend Pages

```
/ (Home/Dashboard)
├── /properties (Feed)
│   ├── List view with filters
│   ├── Map view toggle (Mapbox)
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
│   └── Deal criteria form
│
└── /settings
    ├── Feature preferences
    └── Alert preferences
```

---

## V1 Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | Next.js 14 (App Router) | SSR, API routes |
| **UI Library** | shadcn/ui + Tailwind CSS | Components, dark theme |
| **State** | Zustand + TanStack Query | Client + server state |
| **Maps** | Mapbox GL JS | Property map view |
| **Street View** | Google Maps Static API | Property images |
| **Charts** | Recharts | Simple data viz |
| **Forms** | React Hook Form + Zod | Validation |
| **Icons** | Lucide React | Icon set |
| **Dates** | date-fns | Date formatting |

---

## V1 Project Structure

```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/
│   │   ├── page.tsx              # Dashboard (home)
│   │   ├── properties/
│   │   │   ├── page.tsx          # Feed (list + map)
│   │   │   └── [id]/
│   │   │       └── page.tsx      # Property detail
│   │   ├── saved/
│   │   │   └── page.tsx          # Kanban board
│   │   ├── watchlist/
│   │   │   └── page.tsx          # Watchlist + alerts + criteria
│   │   ├── settings/
│   │   │   └── page.tsx          # User preferences
│   │   └── layout.tsx            # Sidebar layout
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Landing page
│
├── components/
│   ├── ui/                       # shadcn/ui base components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── dialog.tsx
│   │   ├── tabs.tsx
│   │   ├── badge.tsx
│   │   └── ...
│   │
│   ├── layout/
│   │   ├── sidebar.tsx           # Main navigation
│   │   ├── header.tsx            # Top bar with search
│   │   └── mobile-nav.tsx        # Bottom nav (mobile)
│   │
│   ├── dashboard/
│   │   ├── metrics-card.tsx      # Stat cards
│   │   ├── hot-deals-section.tsx # Anomaly highlights
│   │   └── recent-properties.tsx # Recently added
│   │
│   ├── properties/
│   │   ├── property-card.tsx     # Card component
│   │   ├── filters-sidebar.tsx   # Filter controls
│   │   ├── property-grid.tsx     # Grid view
│   │   ├── property-list.tsx     # List view
│   │   └── map-view.tsx          # Mapbox integration
│   │
│   ├── property-detail/
│   │   ├── image-gallery.tsx     # Photos
│   │   ├── property-info.tsx     # Basic info
│   │   ├── zillow-data-panel.tsx # Enrichment data
│   │   ├── street-view.tsx       # Google Street View
│   │   ├── anomaly-panel.tsx     # Market anomaly flag
│   │   ├── comps-tab.tsx         # Comparable sales
│   │   ├── quality-badge.tsx     # Data quality score
│   │   ├── action-buttons.tsx    # Save/Watchlist
│   │   └── notes-section.tsx     # User notes
│   │
│   ├── kanban/
│   │   ├── kanban-board.tsx      # Board container
│   │   ├── kanban-column.tsx     # Column component
│   │   └── kanban-card.tsx       # Draggable card
│   │
│   ├── watchlist/
│   │   ├── watchlist-table.tsx   # Watchlist items
│   │   ├── alert-badge.tsx       # Notification badge
│   │   ├── deal-criteria-form.tsx # Criteria builder
│   │   └── matches-filter.tsx    # "My Matches" toggle
│   │
│   └── export/
│       └── export-button.tsx     # CSV export
│
├── lib/
│   ├── api/
│   │   ├── client.ts             # Axios setup
│   │   ├── properties.ts         # Property endpoints
│   │   ├── enrichment.ts         # Enrichment endpoints
│   │   ├── deal-intelligence.ts  # Anomalies/comps
│   │   ├── saved.ts              # Saved/Kanban endpoints
│   │   ├── watchlist.ts          # Watchlist/alerts endpoints
│   │   └── settings.ts           # Settings endpoints
│   │
│   ├── store/
│   │   ├── use-property-store.ts # Property filters
│   │   ├── use-kanban-store.ts   # Kanban state
│   │   └── use-user-store.ts     # User preferences
│   │
│   ├── hooks/
│   │   ├── use-properties.ts     # Fetch properties
│   │   ├── use-property-detail.ts # Fetch single property
│   │   ├── use-kanban.ts         # Kanban operations
│   │   ├── use-watchlist.ts      # Watchlist operations
│   │   └── use-deal-criteria.ts  # Deal criteria
│   │
│   ├── types/
│   │   ├── property.ts           # Property types
│   │   ├── enrichment.ts         # Zillow data types
│   │   ├── anomaly.ts            # Anomaly types
│   │   ├── kanban.ts             # Kanban types
│   │   └── watchlist.ts          # Watchlist types
│   │
│   └── utils/
│       ├── currency.ts           # Format currency
│       ├── dates.ts              # Format dates
│       └── validation.ts         # Zod schemas
│
├── styles/
│   └── globals.css               # Global styles + dark theme
│
└── package.json
```

---

## V1 Build Phases

### Phase 1: Foundation (Week 1)

| # | Task | File(s) | Acceptance |
|---|------|---------|------------|
| 1 | Next.js setup + shadcn/ui | `package.json`, `tailwind.config.ts` | Dev server runs |
| 2 | Dark theme globals | `styles/globals.css` | Dark colors applied |
| 3 | API client setup | `lib/api/client.ts` | Axios configured |
| 4 | Sidebar layout | `app/(dashboard)/layout.tsx`, `components/layout/sidebar.tsx` | Nav renders |
| 5 | Property types | `lib/types/property.ts` | Types defined |

**API Endpoints Used:**
- `GET /api/health` - Health check

---

### Phase 2: Dashboard (Week 1)

| # | Task | File(s) | Acceptance |
|---|------|---------|------------|
| 1 | Dashboard page | `app/(dashboard)/page.tsx` | Page renders |
| 2 | Metrics cards | `components/dashboard/metrics-card.tsx` | 4 cards show |
| 3 | Hot deals section | `components/dashboard/hot-deals-section.tsx` | Anomalies load |
| 4 | Recent properties | `components/dashboard/recent-properties.tsx` | Latest show |

**API Endpoints Used:**
- `GET /api/deal-intelligence/market-anomalies` - Hot deals
- `GET /api/properties?limit=5` - Recent properties

**Dashboard Metrics:**
- Total Properties (from foreclosure_listings)
- Hot Deals (from market_anomalies count)
- Saved Properties (from saved_properties count)
- Watchlist Items (from user_watchlist count)

---

### Phase 3: Property Feed (Week 1-2)

| # | Task | File(s) | Acceptance |
|---|------|---------|------------|
| 1 | Properties page | `app/(dashboard)/properties/page.tsx` | Page renders |
| 2 | Filters sidebar | `components/properties/filters-sidebar.tsx` | All filters work |
| 3 | Property card | `components/properties/property-card.tsx` | Card shows data |
| 4 | Property grid | `components/properties/property-grid.tsx` | Grid view works |
| 5 | Property list | `components/properties/property-list.tsx` | List view works |
| 6 | Properties hook | `lib/hooks/use-properties.ts` | Fetches from API |
| 7 | View toggle | `components/properties/view-toggle.tsx` | Grid/List switch |
| 8 | Mapbox integration | `components/properties/map-view.tsx` | Map shows markers |

**API Endpoints Used:**
- `GET /api/properties?county={id}&min_price={}&max_price={}` - Search/filter
- `GET /api/counties` - County list for filters

**Filters:**
- County (multi-select)
- Price Range (opening_bid min/max)
- Sale Date Range
- Beds/Baths
- Square Footage
- Hot Deals Only (toggle)
- My Matches (toggle - requires Deal Criteria)

**Property Card Shows:**
```
┌─────────────────────────────────────┐
│ [Thumbnail]  🔥 Hot Deal            │
│                                      │
│ 123 Main St, Newark, NJ 07102        │
│ Opening Bid: $75,000                 │
│ Zestimate: $185,000                  │
│ Potential Equity: $110,000 (59%)     │
│                                      │
│ Sale Date: Jan 15, 2025              │
│ Beds: 3 | Baths: 2 | Sqft: 1,450    │
│                                      │
│ [View Details] [💾 Save] [👁️ Watch] │
└─────────────────────────────────────┘
```

---

### Phase 4: Property Detail (Week 2)

| # | Task | File(s) | Acceptance |
|---|------|---------|------------|
| 1 | Property detail page | `app/(dashboard)/properties/[id]/page.tsx` | Page renders |
| 2 | Image gallery | `components/property-detail/image-gallery.tsx` | Photos show |
| 3 | Property info | `components/property-detail/property-info.tsx` | Basic data |
| 4 | Zillow data panel | `components/property-detail/zillow-data-panel.tsx` | Enrichment |
| 5 | Street View embed | `components/property-detail/street-view.tsx` | Street view |
| 6 | Anomaly panel | `components/property-detail/anomaly-panel.tsx` | Flag shows |
| 7 | Comps tab | `components/property-detail/comps-tab.tsx` | Comps load |
| 8 | Quality badge | `components/property-detail/quality-badge.tsx` | Score shows |
| 9 | Action buttons | `components/property-detail/action-buttons.tsx` | Save/Watch |
| 10 | Notes section | `components/property-detail/notes-section.tsx` | Add notes |

**API Endpoints Used:**
- `GET /api/properties/{id}` - Property details
- `GET /api/enrichment/properties/{id}` - Zillow enrichment
- `GET /api/deal-intelligence/market-anomalies/property/{id}` - Anomaly data
- `GET /api/deal-intelligence/comparable-sales/{property_id}` - Comps
- `GET /api/enrichment/quality/{property_id}` - Quality score
- `POST /api/deal-intelligence/notes` - Add note

**Property Detail Layout:**
```
┌──────────────────────────────────────────────────────────────────┐
│  ← Back to Properties        123 Main St, Newark, NJ    [Edit]   │
├─────────────────────┬────────────────────────────────────────────┤
│                     │                                            │
│  [Main Image]       │  Property Information        🔥 Hot Deal   │
│  [Thumb1] [Thumb2]  │  ───────────────────────────────────────  │
│  [Thumb3] [Thumb4]  │  Address: 123 Main St                      │
│                     │  City: Newark, NJ 07102                    │
│  ─────────────────  │  County: Essex (ID: 2)                     │
│  Street View        │                                            │
│  ─────────────────  │  Foreclosure Details                       │
│  [Google Map        │  Opening Bid: $75,000                      │
│   Street View]      │  Approx Upset: $85,000                     │
│                     │  Sale Date: Jan 15, 2025                   │
│  ─────────────────  │  Attorney: John Smith, Esq.                │
│  Quick Actions      │  Case #: 2025-000123                       │
│  ─────────────────  │                                            │
│  [💾 Save] [👁️ Watch]│  Property Specs                           │
│  [📤 Export]        │  Beds: 3 | Baths: 2 | Sqft: 1,450          │
│                     │  Lot Size: 5,000 sqft                      │
│                     │  Year Built: 1985                          │
│                     │  Property Type: Single Family             │
├─────────────────────┴────────────────────────────────────────────┤
│ Zillow Enrichment Data                                     [Refresh]│
│ ──────────────────────────────────────────────────────────────── │
│ Zestimate: $185,000 | ZPID: 12345678                             │
│ Walk Score: 78 | Transit Score: 65 | Bike Score: 72              │
│ Last Updated: Dec 28, 2025                                       │
├──────────────────────────────────────────────────────────────────┤
│ Market Anomaly Analysis                                          │
│ ──────────────────────────────────────────────────────────────── │
│ ⚠️ This property is priced 2.3 standard deviations BELOW market │
│                                                                    │
│ • Avg Comp Price: $195,000                                        │
│ • Standard Deviation: $8,500                                      │
│ • Z-Score: -2.35                                                  │
│ • Confidence: 87%                                                 │
│                                                                    │
│ Comps Used: 3 similar properties within 1 mile                   │
├──────────────────────────────────────────────────────────────────┤
│ [Comparable Sales] [Notes] [Quality Score]                       │
│ ──────────────────────────────────────────────────────────────── │
│                                                                   │
│ [Tab Content Area...]                                            │
└──────────────────────────────────────────────────────────────────┘
```

---

### Phase 5: Saved Properties + Kanban (Week 2)

| # | Task | File(s) | Acceptance |
|---|------|---------|------------|
| 1 | Kanban page | `app/(dashboard)/saved/page.tsx` | Page renders |
| 2 | Kanban board | `components/kanban/kanban-board.tsx` | Columns show |
| 3 | Kanban column | `components/kanban/kanban-column.tsx` | Stage header |
| 4 | Kanban card | `components/kanban/kanban-card.tsx` | Draggable |
| 5 | dnd-kit setup | `package.json` | Drag works |
| 6 | Kanban store | `lib/store/use-kanban-store.ts` | State mgmt |
| 7 | Kanban hook | `lib/hooks/use-kanban.ts` | API calls |

**API Endpoints Used:**
- `GET /api/deal-intelligence/saved/{user_id}/kanban` - Get board
- `POST /api/deal-intelligence/saved` - Save property
- `PUT /api/deal-intelligence/saved/stage` - Move stage
- `DELETE /api/deal-intelligence/saved/{id}` - Unsave

**Kanban Columns:**
| Stage | Description | Color |
|-------|-------------|-------|
| `researching` | Initial research | Gray |
| `analyzing` | Analysis in progress | Blue |
| `due_diligence` | Due diligence tasks | Yellow |
| `bidding` | Active bidding | Orange |
| `won` | Deal acquired | Green |
| `lost` | Deal lost | Red |
| `archived` | No longer relevant | Muted |

**Kanban Card Shows:**
```
┌─────────────────────────────────┐
│ 123 Main St, Newark             │
│ Opening Bid: $75,000            │
│ Zestimate: $185,000             │
│                                  │
│ [Add Note] [Assign]             │
└─────────────────────────────────┘
```

---

### Phase 6: Watchlist + Deal Criteria (Week 2-3)

| # | Task | File(s) | Acceptance |
|---|------|---------|------------|
| 1 | Watchlist page | `app/(dashboard)/watchlist/page.tsx` | Page renders |
| 2 | Watchlist table | `components/watchlist/watchlist-table.tsx` | Table shows |
| 3 | Alert badge | `components/watchlist/alert-badge.tsx` | Unread count |
| 4 | Deal criteria form | `components/watchlist/deal-criteria-form.tsx` | Form works |
| 5 | Matches filter | `components/watchlist/matches-filter.tsx` | Toggle works |
| 6 | Watchlist hook | `lib/hooks/use-watchlist.ts` | API calls |

**API Endpoints Used:**
- `GET /api/deal-intelligence/watchlist/{user_id}` - Get watchlist
- `POST /api/deal-intelligence/watchlist` - Add to watchlist
- `DELETE /api/deal-intelligence/watchlist/{id}` - Remove
- `GET /api/deal-intelligence/alerts/{user_id}` - Get alerts
- `PUT /api/deal-intelligence/alerts/{id}/read` - Mark read
- `GET /api/deal-intelligence/criteria/{user_id}` - Get criteria
- `POST /api/deal-intelligence/criteria` - Save criteria
- `GET /api/deal-intelligence/matches/{user_id}` - Get matches

**Deal Criteria Form Fields:**
| Field | Type | Example |
|-------|------|---------|
| Max Opening Bid | Number | $150,000 |
| Min Equity Spread | Number | $50,000 |
| Counties | Multi-select | [1, 2, 7] (Camden, Essex, Bergen) |
| Min/Max Beds | Range | 2 - 4 |
| Min/Max Baths | Range | 1+ |
| Min SqFt | Number | 1,200 |
| Property Types | Multi-select | [house, townhome] |
| Sale Date Window | Date Range | Next 30 days |
| Anomalies Only | Toggle | Yes |

**Watchlist Page:**
```
┌──────────────────────────────────────────────────────────────────┐
│ 🔔 Alerts (3)                              [Mark All Read]       │
├──────────────────────────────────────────────────────────────────┤
│ Watchlist                                     [My Matches: On]   │
│ ──────────────────────────────────────────────────────────────── │
│                                                                   │
│ [Deal Criteria Form] [Edit Criteria]                             │
│ Max Bid: $150k | Min Equity: $50k | Counties: Essex, Bergen    │
├──────────────────────────────────────────────────────────────────┤
│ Property              | Opening Bid | Zestimate | Alert          │
│ ──────────────────────┼─────────────┼───────────┼─────────────── │
│ 123 Main St, Newark   | $75,000     | $185,000  | Price Drop!    │
│ 456 Oak Ave, Jersey   | $95,000     | $210,000  | New Comps      │
│ 789 Pine Rd, Hoboken  | $120,000    | $280,000  | Sale Tomorrow  │
└──────────────────────────────────────────────────────────────────┘
```

---

### Phase 7: Settings (Week 3)

| # | Task | File(s) | Acceptance |
|---|------|---------|------------|
| 1 | Settings page | `app/(dashboard)/settings/page.tsx` | Page renders |
| 2 | Feature toggles | `components/settings/feature-toggles.tsx` | Toggle works |
| 3 | Alert preferences | `components/settings/alert-prefs.tsx` | Form works |

**API Endpoints Used:**
- `GET /api/deal-intelligence/settings/user/{user_id}` - Get prefs
- `POST /api/deal-intelligence/settings/user` - Create prefs
- `PUT /api/deal-intelligence/settings/user/{user_id}` - Update prefs

**User Preferences (V1):**
| Preference | Type | Options |
|------------|------|---------|
| Anomaly Detection | Toggle | On/Off |
| Comps Analysis | Toggle | On/Off |
| Save Properties | Toggle | On/Off |
| Kanban Board | Toggle | On/Off |
| Watchlist Alerts | Toggle | On/Off |
| Export CSV | Toggle | On/Off |
| Email Alerts | Toggle | On/Off |
| Alert Frequency | Select | Instant, Daily, Weekly |

---

### Phase 8: Polish & Testing (Week 3)

| # | Task | Acceptance |
|---|------|------------|
| 1 | Loading states | Skeletons show |
| 2 | Error handling | Error boundaries |
| 3 | Mobile responsive | All pages mobile-friendly |
| 4 | CSV export | Download works |
| 5 | E2E testing | User flows work |
| 6 | Performance | < 3s page load |

---

## V1 Design System

### Color Palette (Dark Theme)

```css
/* Tailwind config */
{
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#0a0a0a',    /* Primary */
          secondary: '#141414',   /* Secondary */
          card: '#1e1e1e',        /* Cards */
        },
        border: '#2a2a2a',
        primary: '#3b82f6',       /* Electric blue */
        success: '#10b981',       /* Emerald */
        warning: '#f59e0b',       /* Amber */
        error: '#ef4444',         /* Red */
        text: {
          primary: '#f5f5f5',
          secondary: '#a3a3a3',
          muted: '#737373',
        }
      }
    }
  }
}
```

### Typography

- **Font:** Inter
- **Sizes:** 12px (small), 14px (base), 16px (body), 20px (h3)

---

## V1 Responsive Breakpoints

| Breakpoint | Width | Layout Changes |
|------------|-------|----------------|
| Mobile | < 640px | Single column, bottom nav |
| Tablet | 640px - 1024px | 2 columns, collapsible sidebar |
| Desktop | > 1024px | Full layouts, permanent sidebar |

---

## V1 Getting Started

```bash
# Create Next.js project
npx create-next-app@latest dealflow-v1 --typescript --tailwind --app

cd dealflow-v1

# Install dependencies
npm install axios @tanstack/react-query zustand
npm install @dnd-kit/core @dnd-kit/sortable
npm install mapbox-gl react-map-gl recharts
npm install react-hook-form zod @hookform/resolvers
npm install date-fns lucide-react

# Initialize shadcn/ui
npx shadcn-ui@latest init

# Add shadcn components
npx shadcn-ui@latest add button card input select dialog tabs badge

# Run dev
npm run dev
```

---

## V1 Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_key
```

---

## V1 Testing Checklist

| Page | Desktop | Tablet | Mobile | API |
|------|---------|--------|--------|-----|
| Dashboard | ☐ | ☐ | ☐ | ☐ |
| Properties Feed | ☐ | ☐ | ☐ | ☐ |
| Property Detail | ☐ | ☐ | ☐ | ☐ |
| Kanban Board | ☐ | ☐ | ☐ | ☐ |
| Watchlist | ☐ | ☐ | ☐ | ☐ |
| Settings | ☐ | ☐ | ☐ | ☐ |
| Map View | ☐ | N/A | ☐ | ☐ |
| CSV Export | ☐ | ☐ | ☐ | ☐ |

---

## V1 Launch Metrics

| Metric | Target |
|--------|--------|
| Page Load Time | < 3 seconds |
| Time to Hot Deals | < 5 seconds |
| Data Quality | > 95% enrichment |
| False Positive Rate | < 5% |
| Mobile Responsive | 100% pages |

---

## V1 Total Timeline: 3 Weeks

| Week | Focus |
|------|-------|
| 1 | Foundation, Dashboard, Properties Feed |
| 2 | Property Detail, Kanban, Watchlist |
| 3 | Settings, Deal Criteria, Polish |
