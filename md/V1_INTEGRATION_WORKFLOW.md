# V1 Backend Integration with Frontend - Complete Workflow

**Purpose:** Integrate V1 backend (FastAPI) with frontend (Next.js 14) for MVP launch
**Date:** December 29, 2025
**Status:** Phase 1 - Backend Setup

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         V1 INTEGRATION WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  PHASE 1: BACKEND WEBHOOK SETUP (Current Focus)                                 │
│  ├─ 1.1 changedetection.io Setup                                               │
│  ├─ 1.2 Coolify Deployment for Swagger Docs                                    │
│  └─ 1.3 Webhook Testing & Verification                                         │
│                                                                                 │
│  PHASE 2: FRONTEND INTEGRATION                                                  │
│  ├─ 2.1 Scraper Integration Display                                            │
│  ├─ 2.2 Enrichment Data Display                                               │
│  ├─ 2.3 Property Feed Page                                                    │
│  ├─ 2.4 Deal Intelligence Features                                            │
│  └─ 2.5 Kanban & Watchlist                                                    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: Backend Webhook Setup

### Goal
Set up automated data ingestion pipeline with changedetection.io and deploy Swagger documentation via Coolify.

### 1.1 changedetection.io Setup

**Background:**
- 16 NJ Counties with non-sequential IDs (1, 2, 3, 6, 7, 8, 9, 10, 15, 17, 19, 20, 25, 32, 52, 73)
- Target URL pattern: `https://salesweb.civilview.com/Sales/SalesSearch?countyId={COUNTY_ID}`
- Single webhook endpoint: `POST /webhooks/changedetection`
- County extracted from `watch_title` format: `CivilView | {CountyName}`

**16 Counties Configuration:**

| County | ID | Watch Title | Target URL |
|--------|-----|-------------|------------|
| Atlantic | 25 | `CivilView | Atlantic` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=25` |
| Bergen | 7 | `CivilView | Bergen` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=7` |
| Burlington | 3 | `CivilView | Burlington` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=3` |
| Camden | 1 | `CivilView | Camden` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=1` |
| Cape May | 52 | `CivilView | Cape May` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=52` |
| Cumberland | 6 | `CivilView | Cumberland` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=6` |
| Essex | 2 | `CivilView | Essex` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=2` |
| Gloucester | 19 | `CivilView | Gloucester` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=19` |
| Hudson | 10 | `CivilView | Hudson` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=10` |
| Hunterdon | 32 | `CivilView | Hunterdon` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=32` |
| Middlesex | 73 | `CivilView | Middlesex` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=73` |
| Monmouth | 8 | `CivilView | Monmouth` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=8` |
| Morris | 9 | `CivilView | Morris` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=9` |
| Passaic | 17 | `CivilView | Passaic` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=17` |
| Salem | 20 | `CivilView | Salem` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=20` |
| Union | 15 | `CivilView | Union` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=15` |

**Installation:**

```bash
# Using Docker Compose
cat > docker-compose.changedetection.yml <<EOF
services:
  changedetection:
    image: ghcr.io/dgtlmoon/changedetection.io:latest
    container_name: changedetection
    ports:
      - "5000:5000"
    volumes:
      - changedetection-data:/datastore
    restart: unless-stopped

volumes:
  changedetection-data:
EOF

docker-compose -f docker-compose.changedetection.yml up -d
```

**Configuration Steps:**

1. Access changedetection.io at `http://localhost:5000`

2. For each county, create a watch with:
   - **URL:** `https://salesweb.civilview.com/Sales/SalesSearch?countyId={COUNTY_ID}`
   - **Title:** `CivilView | {CountyName}`
   - **Check Interval:** Every 4 hours (`0 */4 * * *`)

3. Add webhook notification for each watch:
   - **Webhook URL:** `https://your-domain.com/webhooks/changedetection`
   - **Method:** POST
   - **Headers:**
     ```json
     {
       "Content-Type": "application/json",
       "X-Webhook-Secret": "YOUR_WEBHOOK_SECRET"
     }
     ```

4. Body Template (JSON):
   ```json
   {
     "county": "{COUNTY_NAME}",
     "county_id": {COUNTY_ID},
     "triggered_by": "changedetection.io",
     "timestamp": "{{timestamp}}",
     "url": "{{url}}",
     "status": "{{status_code}}"
   }
   ```

**Webhook Endpoint Implementation:**

The backend already has the webhook endpoint at `webhook_server/app.py`:

```python
@app.post("/webhooks/changedetection")
async def handle_changedetection_webhook(
    payload: Dict[str, Any],
    x_webhook_secret: Optional[str] = Header(None)
):
    """Handle changedetection.io webhook - trigger scraper for detected county"""
    # Validate secret
    if x_webhook_secret != os.getenv("WEBHOOK_SECRET"):
        raise HTTPException(401, "Invalid webhook secret")

    # Extract county from payload
    county = payload.get("county")
    county_id = payload.get("county_id")

    # Trigger scraper for this county
    result = await scrape_county(county, county_id)
    return result
```

**pg_cron Fallback:**

Already configured in database (migration `add_pg_cron_jobs.sql`):

```sql
-- Runs every 4 hours as fallback
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

---

### 1.2 Coolify Deployment for Swagger Docs

**Goal:** Deploy FastAPI server with Swagger documentation accessible via Coolify.

**Prerequisites:**
- Coolify instance (self-hosted or managed)
- Domain configured (e.g., `api.yourdomain.com`)
- Environment variables set

**Dockerfile for FastAPI:**

```dockerfile
# webhook_server/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

**requirements.txt:**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
supabase==2.3.4
pydantic==2.5.3
python-dotenv==1.0.0
playwright==1.40.0
httpx==0.26.0
openai==1.10.0
```

**Coolify Configuration:**

1. **Create New Application:**
   - Source: Git
   - Repository: `your-repo/salesweb-crawl`
   - Branch: `main` (or `feature/v1-integration`)
   - Build Path: `/webhook_server`

2. **Environment Variables:**
   ```bash
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   WEBHOOK_SECRET=your_webhook_secret
   SCHEDULE_SECRET=your_schedule_secret
   RAPIDAPI_KEY=your_rapidapi_key
   OPENAI_API_KEY=your_openai_key
   ```

3. **Port Configuration:**
   - Container Port: `8080`
   - Health Check: `/health`

4. **Domain:**
   - Assign domain: `api.yourdomain.com`
   - Enable HTTPS (Let's Encrypt)

**Swagger Documentation Access:**

After deployment, access Swagger docs at:
- `https://api.yourdomain.com/docs` - Swagger UI
- `https://api.yourdomain.com/openapi.json` - OpenAPI JSON

**V1/V2 Tags in Swagger:**

- **V1 Tags:** `Enrichment (V1)`, `Deal Intelligence (V1)`
  - Core MVP features (40 endpoints)
  - Property feed, enrichment, anomalies, comps, saved, kanban, watchlist, alerts

- **V2 Tags:** `Enrichment (V2)`, `Deal Intelligence (V2)`
  - Advanced features (24 endpoints)
  - Portfolio, collaboration, investment strategies, renovation, mobile push

---

### 1.3 Webhook Testing & Verification

**Testing changedetection.io Webhook:**

```bash
# Manual webhook test
curl -X POST "https://your-domain.com/webhooks/changedetection" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: YOUR_WEBHOOK_SECRET" \
  -d '{
    "county": "Essex",
    "county_id": 2,
    "triggered_by": "manual_test",
    "timestamp": "2025-12-29T10:00:00Z",
    "url": "https://salesweb.civilview.com/Sales/SalesSearch?countyId=2",
    "status": 200
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "county": "Essex",
  "county_id": 2,
  "properties_scraped": 42,
  "properties_added": 15,
  "properties_updated": 27
}
```

**Testing pg_cron Scheduled Scrape:**

```bash
# Trigger scheduled scrape manually
curl -X POST "https://your-domain.com/webhooks/scheduled" \
  -H "Content-Type: application/json" \
  -H "X-Schedule-Secret": "YOUR_SCHEDULE_SECRET" \
  -d '{}'
```

**Expected Response:**
```json
{
  "status": "success",
  "counties_scraped": 16,
  "total_properties": 653,
  "duration_seconds": 245
}
```

**Verification Checklist:**

- [ ] changedetection.io accessible at `http://localhost:5000`
- [ ] All 16 county watches created
- [ ] Webhook notifications configured for each watch
- [ ] Manual webhook test returns success
- [ ] Scraper triggered by webhook
- [ ] Properties added to database
- [ ] Enrichment triggered for new properties
- [ ] pg_cron job scheduled in database
- [ ] Coolify deployment successful
- [ ] Swagger docs accessible at deployed domain
- [ ] V1/V2 tags visible in Swagger UI

---

## PHASE 2: Frontend Integration

### Goal
Build Next.js 14 frontend to display scraped properties, enriched data, and deal intelligence features.

### 2.1 Frontend Setup

**Tech Stack:**
- Next.js 14 (App Router)
- React 18
- TypeScript 5
- Tailwind CSS 3.4
- shadcn/ui components
- Zustand 4.5 (state management)
- Tanstack Query 5.17 (server state)
- Recharts 2.10 (charts)

**Installation:**

```bash
# Create Next.js project
cd "/mnt/c/Projects Gits/salesweb-crawl"
npx create-next-app@14 frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*"

cd frontend

# Install dependencies
npm install zustand @tanstack/react-query recharts lucide-react clsx tailwind-merge

# Install shadcn/ui
npx shadcn-ui@latest init -y

# Add required shadcn components
npx shadcn-ui@latest add button card input select table badge dialog dropdown-menu
npx shadcn-ui@latest add tabs skeleton toast alert separator
```

**Project Structure:**

```
frontend/
├── app/
│   ├── layout.tsx                 # Root layout with providers
│   ├── page.tsx                   # Dashboard (stats, hot deals)
│   ├── properties/
│   │   ├── page.tsx               # Property feed with filters
│   │   └── [id]/
│   │       └── page.tsx           # Property detail page
│   ├── saved/
│   │   └── page.tsx               # Kanban board
│   ├── watchlist/
│   │   └── page.tsx               # Watchlist + alerts
│   └── settings/
│       └── page.tsx               # User settings
├── components/
│   ├── ui/                        # shadcn/ui base components
│   ├── PropertyCard.tsx           # Property listing card
│   ├── PropertyGrid.tsx           # Grid/table view toggle
│   ├── FilterBar.tsx              # County, price, date filters
│   ├── KanbanBoard.tsx            # Kanban board component
│   ├── KanbanColumn.tsx           # Kanban stage column
│   ├── EnrichmentDisplay.tsx      # Zillow data display
│   ├── AnomalyBadge.tsx           # "Hot Deal" indicator
│   └── StatCard.tsx               # Dashboard stat card
├── lib/
│   ├── api.ts                     # API client (axios)
│   ├── utils.ts                   # Utility functions
│   └── types.ts                   # TypeScript types
└── stores/
    ├── propertyStore.ts           # Property state
    └── userStore.ts               # User state
```

**API Client Setup (`lib/api.ts`):**

```typescript
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      window.location.href = '/auth/signin';
    }
    return Promise.reject(error);
  }
);

// API Methods
export const propertyApi = {
  list: (params?: any) => api.get('/api/properties', { params }),
  get: (id: number) => api.get(`/api/properties/${id}`),
  search: (query: string) => api.get('/api/properties/search', { params: { q: query } }),
  hot: () => api.get('/api/properties/hot'),
};

export const enrichmentApi = {
  trigger: (id: number) => api.post(`/api/enrichment/properties/${id}/enrich`),
  get: (id: number) => api.get(`/api/enrichment/properties/${id}`),
  status: (id: number) => api.get(`/api/enrichment/status/${id}`),
};

export const dealIntelApi = {
  anomalies: () => api.get('/api/deal-intelligence/market-anomalies'),
  comps: (propertyId: number) => api.get(`/api/deal-intelligence/comparable-sales/${propertyId}`),
  saved: (userId: string) => api.get(`/api/deal-intelligence/saved/${userId}`),
  save: (data: any) => api.post('/api/deal-intelligence/saved', data),
  unsave: (id: number) => api.delete(`/api/deal-intelligence/saved/${id}`),
  kanban: (userId: string) => api.get(`/api/deal-intelligence/saved/${userId}/kanban`),
  watchlist: (userId: string) => api.get(`/api/deal-intelligence/watchlist/${userId}`),
  addToWatchlist: (data: any) => api.post('/api/deal-intelligence/watchlist', data),
  alerts: (userId: string) => api.get(`/api/deal-intelligence/alerts/${userId}`),
};
```

---

### 2.2 Scraper Integration Display

**Component: PropertyFeed (`app/properties/page.tsx`)**

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { propertyApi } from '@/lib/api';
import { PropertyCard } from '@/components/PropertyCard';
import { FilterBar } from '@/components/FilterBar';
import { useState } from 'react';

export default function PropertyFeedPage() {
  const [filters, setFilters] = useState({
    county: null,
    minPrice: null,
    maxPrice: null,
    startDate: null,
    endDate: null,
  });

  const { data: properties, isLoading } = useQuery({
    queryKey: ['properties', filters],
    queryFn: () => propertyApi.list(filters).then(res => res.data),
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Foreclosure Properties</h1>

      <FilterBar
        filters={filters}
        onFiltersChange={setFilters}
      />

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {properties?.map(property => (
            <PropertyCard key={property.id} property={property} />
          ))}
        </div>
      )}
    </div>
  );
}
```

**Component: PropertyCard (`components/PropertyCard.tsx`)**

```typescript
'use client';

import Link from 'next/link';
import { Property } from '@/lib/types';
import { AnomalyBadge } from './AnomalyBadge';
import { MapPin, DollarSign, Calendar } from 'lucide-react';

interface PropertyCardProps {
  property: Property;
}

export function PropertyCard({ property }: PropertyCardProps) {
  return (
    <Link href={`/properties/${property.id}`}>
      <div className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
        <div className="flex justify-between items-start mb-3">
          <h3 className="font-semibold text-lg truncate flex-1">
            {property.property_address}
          </h3>
          <AnomalyBadge propertyId={property.id} />
        </div>

        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            <span>{property.city}, {property.county_name}</span>
          </div>

          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4" />
            <span>Opening Bid: ${property.opening_bid?.toLocaleString()}</span>
          </div>

          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            <span>Sale: {new Date(property.sale_date).toLocaleDateString()}</span>
          </div>
        </div>

        {/* Enrichment Status */}
        {property.zillow_enrichment_status === 'fully_enriched' && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex gap-2 text-xs">
              <span className="bg-green-100 text-green-700 px-2 py-1 rounded">
                Zillow Data
              </span>
              {property.is_anomaly && (
                <span className="bg-red-100 text-red-700 px-2 py-1 rounded">
                  Hot Deal
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </Link>
  );
}
```

---

### 2.3 Enrichment Data Display

**Component: EnrichmentDisplay (`components/EnrichmentDisplay.tsx`)**

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { enrichmentApi } from '@/lib/api';
import { Home, Maximize, Bath, Bed } from 'lucide-react';

interface EnrichmentDisplayProps {
  propertyId: number;
}

export function EnrichmentDisplay({ propertyId }: EnrichmentDisplayProps) {
  const { data: enrichment, isLoading } = useQuery({
    queryKey: ['enrichment', propertyId],
    queryFn: () => enrichmentApi.get(propertyId).then(res => res.data),
    enabled: !!propertyId,
  });

  if (isLoading) return <div>Loading Zillow data...</div>;
  if (!enrichment) return null;

  return (
    <div className="space-y-4">
      {/* Zestimate */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <h3 className="font-semibold text-lg">Zestimate</h3>
        <p className="text-3xl font-bold text-blue-600">
          ${enrichment.zestimate?.toLocaleString()}
        </p>
      </div>

      {/* Property Details */}
      <div className="grid grid-cols-3 gap-4">
        <div className="flex items-center gap-2">
          <Bed className="w-5 h-5" />
          <span>{enrichment.bedrooms} beds</span>
        </div>
        <div className="flex items-center gap-2">
          <Bath className="w-5 h-5" />
          <span>{enrichment.bathrooms} baths</span>
        </div>
        <div className="flex items-center gap-2">
          <Maximize className="w-5 h-5" />
          <span>{enrichment.sqft?.toLocaleString()} sqft</span>
        </div>
      </div>

      {/* Property Images */}
      {enrichment.images && enrichment.images.length > 0 && (
        <div>
          <h3 className="font-semibold mb-2">Photos</h3>
          <div className="grid grid-cols-3 gap-2">
            {enrichment.images.slice(0, 6).map((img, i) => (
              <img key={i} src={img} alt={`Photo ${i+1}`} className="rounded-lg" />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

### 2.4 Deal Intelligence Features

**Market Anomaly Badge (`components/AnomalyBadge.tsx`)**

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { dealIntelApi } from '@/lib/api';
import { Flame } from 'lucide-react';

interface AnomalyBadgeProps {
  propertyId: number;
}

export function AnomalyBadge({ propertyId }: AnomalyBadgeProps) {
  const { data: anomaly } = useQuery({
    queryKey: ['anomaly', propertyId],
    queryFn: () => dealIntelApi.anomalies().then(res =>
      res.data.find(a => a.property_id === propertyId)
    ),
    enabled: !!propertyId,
  });

  if (!anomaly) return null;

  return (
    <div className="flex items-center gap-1 bg-red-500 text-white px-2 py-1 rounded-full text-xs font-medium">
      <Flame className="w-3 h-3" />
      <span>Hot Deal</span>
      <span className="ml-1 opacity-80">
        {anomaly.price_difference_percent.toFixed(0)}% below
      </span>
    </div>
  );
}
```

**Comparable Sales Display (`components/CompsDisplay.tsx`)**

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { dealIntelApi } from '@/lib/api';

interface CompsDisplayProps {
  propertyId: number;
}

export function CompsDisplay({ propertyId }: CompsDisplayProps) {
  const { data: comps, isLoading } = useQuery({
    queryKey: ['comps', propertyId],
    queryFn: () => dealIntelApi.comps(propertyId).then(res => res.data),
    enabled: !!propertyId,
  });

  if (isLoading) return <div>Loading comparable sales...</div>;
  if (!comps) return null;

  return (
    <div className="bg-white p-4 rounded-lg border">
      <h3 className="font-semibold mb-3">Comparable Sales Analysis</h3>

      {/* ARV Estimate */}
      <div className="bg-green-50 p-3 rounded mb-4">
        <div className="text-sm text-gray-600">After-Repair Value (ARV)</div>
        <div className="text-2xl font-bold text-green-600">
          ${comps.arv_estimate?.toLocaleString()}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Confidence: {(comps.confidence_score * 100).toFixed(0)}%
        </div>
      </div>

      {/* Comparable Properties */}
      <div>
        <h4 className="font-medium mb-2">Comparable Properties</h4>
        <div className="space-y-2">
          {comps.comparable_properties?.map((comp: any, i: number) => (
            <div key={i} className="text-sm border-b pb-2">
              <div className="font-medium">{comp.address}</div>
              <div className="text-gray-600">
                Sold: ${comp.sold_price?.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">
                {comp.distance_miles?.toFixed(1)} miles away • {comp.days_ago} days ago
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

### 2.5 Kanban Board

**Component: KanbanBoard (`components/KanbanBoard.tsx`)**

```typescript
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dealIntelApi } from '@/lib/api';
import { DndContext, DragEndEvent } from '@dnd-kit/core';
import { KanbanColumn } from './KanbanColumn';

const STAGES = ['researching', 'analyzing', 'due_diligence', 'bidding', 'won', 'lost', 'archived'];

export function KanbanBoard({ userId }: { userId: string }) {
  const queryClient = useQueryClient();

  const { data: kanbanData, isLoading } = useQuery({
    queryKey: ['kanban', userId],
    queryFn: () => dealIntelApi.kanban(userId).then(res => res.data),
  });

  const moveStage = useMutation({
    mutationFn: ({ savedId, newStage }: { savedId: number; newStage: string }) =>
      dealIntelApi.save({ id: savedId, kanban_stage: newStage }),
    onSuccess: () => queryClient.invalidateQueries(['kanban']),
  });

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const savedId = Number(active.id);
    const newStage = over.id.toString();

    moveStage.mutate({ savedId, newStage });
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div className="flex gap-4 overflow-x-auto pb-4">
        {STAGES.map(stage => (
          <KanbanColumn
            key={stage}
            stage={stage}
            properties={kanbanData?.[stage] || []}
          />
        ))}
      </div>
    </DndContext>
  );
}
```

**Component: KanbanColumn (`components/KanbanColumn.tsx`)**

```typescript
'use client';

import { useDroppable } from '@dnd-kit/core';
import { KanbanCard } from './KanbanCard';

interface KanbanColumnProps {
  stage: string;
  properties: any[];
}

const STAGE_LABELS: Record<string, string> = {
  researching: 'Researching',
  analyzing: 'Analyzing',
  due_diligence: 'Due Diligence',
  bidding: 'Bidding',
  won: 'Won',
  lost: 'Lost',
  archived: 'Archived',
};

export function KanbanColumn({ stage, properties }: KanbanColumnProps) {
  const { setNodeRef } = useDroppable({ id: stage });

  return (
    <div className="flex-shrink-0 w-72">
      <div className="bg-gray-100 rounded-lg p-3">
        <h3 className="font-semibold mb-2 capitalize">
          {STAGE_LABELS[stage] || stage}
          <span className="ml-2 text-sm text-gray-500">
            ({properties.length})
          </span>
        </h3>

        <div ref={setNodeRef} className="space-y-2 min-h-[200px]">
          {properties.map(property => (
            <KanbanCard key={property.id} property={property} />
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## Implementation Order

### Week 1: Foundation
1. **Day 1-2:** Frontend project setup, shadcn/ui installation, design system
2. **Day 3-4:** Property feed page with filters
3. **Day 5:** Property detail page with Zillow data

### Week 2: Core Features
1. **Day 6-7:** Market anomaly detection UI, "Hot Deals" badges
2. **Day 8-9:** Saved properties + Kanban board
3. **Day 10:** Watchlist + alerts

### Week 3: Polish
1. **Day 11-12:** Settings page, user preferences
2. **Day 13:** Mobile responsive optimization
3. **Day 14:** Testing, bug fixes, deployment

---

## Environment Variables

**Backend (.env):**
```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Webhook Secrets
WEBHOOK_SECRET=your_webhook_secret
SCHEDULE_SECRET=your_schedule_secret

# External APIs
RAPIDAPI_KEY=your_rapidapi_key
OPENAI_API_KEY=your_openai_key
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
# Production: NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## Testing Checklist

### Phase 1 Testing
- [ ] changedetection.io webhooks trigger scraper
- [ ] Properties saved to database
- [ ] Enrichment auto-triggers
- [ ] pg_cron fallback works
- [ ] Coolify deployment successful
- [ ] Swagger docs accessible

### Phase 2 Testing
- [ ] Property feed loads with filters
- [ ] Property detail page shows enrichment
- [ ] Market anomalies display correctly
- [ ] Comparable sales analysis works
- [ ] Kanban board drag-and-drop works
- [ ] Watchlist alerts display
- [ ] Mobile responsive works

---

## Current Status

**Completed:**
- ✅ V1 backend API (40 endpoints)
- ✅ Database schema (all V1 tables)
- ✅ Service layer (all V1 services)
- ✅ V2 tables renamed with V2_ prefix
- ✅ V1/V2 endpoint tags in Swagger
- ✅ changedetection.io documentation
- ✅ pg_cron scheduled jobs

**In Progress:**
- 🔄 changedetection.io setup
- 🔄 Coolify deployment

**Pending:**
- ⏳ Frontend project setup
- ⏳ Property feed implementation
- ⏳ Deal intelligence UI
- ⏳ Kanban board
- ⏳ Watchlist & alerts

---

## Next Steps

1. **Immediate:** Set up changedetection.io with all 16 counties
2. **This Week:** Deploy to Coolify with Swagger docs
3. **Next Week:** Start frontend implementation with property feed
4. **Following Weeks:** Build deal intelligence features
