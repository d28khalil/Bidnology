# BIDNOLOGY - NJ Sheriff Sale Foreclosure Platform

AI-powered web scraper for New Jersey sheriff sale foreclosure listings with Zillow enrichment and deal intelligence.

---

## Quick Start

```bash
# Frontend (localhost:3000)
cd frontend && npm run dev

# Backend (localhost:8080)
cd webhook_server && ../venv/bin/python -m uvicorn app:app --reload --port 8080

# Scraper (single county)
./venv/bin/python playwright_scraper.py --counties Essex
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI (Python 3.12), Supabase (PostgreSQL) |
| **Scraping** | Playwright + GPT-4o (AI extraction) |
| **Enrichment** | RapidAPI Zillow (8 endpoints) |

---

## Project Structure

```
salesweb-crawl/
├── frontend/              # Next.js 14 frontend
│   ├── app/              # App Router pages
│   ├── components/       # React components
│   └── lib/              # Utilities, API client
├── webhook_server/       # FastAPI backend (port 8080)
│   ├── app.py            # Main application
│   └── services/         # Business logic
├── migrations/           # Database migrations
└── venv/                 # Python virtual environment
```

---

## Key API Endpoints

```
# Health & Enrichment
GET  /health                                    # Server health check
POST /api/enrichment/properties/{id}/enrich    # Trigger Zillow enrichment

# Deal Intelligence (21+ endpoints)
GET  /api/deal-intelligence/settings/admin      # Admin feature settings
GET  /api/deal-intelligence/anomalies           # Market anomalies
GET  /api/deal-intelligence/comps/{id}          # Comparable sales
POST /api/deal-intelligence/saved               # Save property
GET  /api/deal-intelligence/watchlist/{user_id} # Get watchlist
```

---

## Environment Variables

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key
RAPIDAPI_KEY=ddc80cadcamsh4b4716e724116a2p122560jsnfcec8e2250a9
OPENAI_API_KEY=your_openai_key
```

---

## County ID Mapping

| County | ID | County | ID |
|--------|-----|--------|-----|
| Camden | 1 | Essex | 2 | Burlington | 3 | Cumberland | 6 |
| Bergen | 7 | Monmouth | 8 | Morris | 9 | Hudson | 10 |
| Passaic | 17 | Union | 15 | Salem | 20 | Gloucester | 19 |
| Atlantic | 25 | Cape May | 52 | Hunterdon | 32 | Middlesex | 73 |

---

## Current Status

| Component | Status |
|-----------|--------|
| Data Source (Sheriff Sales) | ✅ Complete |
| Playwright Scraper | ✅ Complete |
| FastAPI Webhook Server | ✅ Complete |
| Supabase Database | ✅ Complete |
| Zillow Enrichment (8 endpoints) | ✅ Complete |
| Deal Intelligence API (21 endpoints) | ✅ Complete |
| ML Ranking System | ✅ Complete |
| Push Notifications (iOS/Android) | ✅ Complete |
| Property Feed UI | 🟡 Partial |
| Authentication | 🟡 Partial |

---

## Deal Intelligence Features

| Feature | Endpoints | Status |
|---------|-----------|--------|
| Feature Toggle System | 2 | ✅ Complete |
| Market Anomaly Detection | 4 | ✅ Complete |
| Comparable Sales Analysis | 3 | ✅ Complete |
| Investment Strategies | 6 | ✅ Complete |
| Saved Properties + Kanban | 5 | ✅ Complete |
| Watchlist + Alerts | 9 | ✅ Complete |
| Portfolio Tracking | 5 | ✅ Complete |
| Property Notes | 4 | ✅ Complete |
| Due Diligence Checklist | 3 | ✅ Complete |
| ML Ranking | 7 | ✅ Complete |
| Push Notifications | 4 | ✅ Complete |
| Team Collaboration | 4 | 🟡 TODO |
| Renovation Estimator | 2 | 🟡 TODO |

---

## Kanban Pipeline Stages

```
researching → analyzing → due_diligence → bidding → won/lost/archived
```

---

## Important Files

| File | Purpose |
|------|---------|
| `playwright_scraper.py` | Main scraper with GPT-4o AI extraction |
| `ai_full_extractor.py` | AI extraction with screenshot fallback |
| `webhook_server/app.py` | FastAPI application (all routes) |
| `webhook_server/zillow_enrichment.py` | Zillow API integration |
| `webhook_server/deal_intelligence_routes.py` | 21+ deal intelligence endpoints |

---

## AI Extraction (Quality-First)

- **Primary**: GPT-4o mini extracts from HTML (~$0.15/1M tokens)
- **Fallback**: GPT-4o Vision extracts from screenshot (if quality check fails)
- **Quality Threshold**: Must have `property_address` + at least one monetary/date field

---

## Webhook Integration

**changedetection.io:**
- Endpoint: `POST /webhooks/changedetection`
- Watch Title Format: `CivilView | {CountyName}`
- All counties use the SAME endpoint

---

## Recent Frontend Changes (Dec 31, 2025)

- ✅ Mobile pagination with compact text and chevron icons
- ✅ Bottom sheet filter dropdowns on mobile
- ✅ Filter labels next to icons on mobile
- ✅ Mobile-only "Order" sort filter
- ✅ Desktop dropdown positioning fix
- ✅ CSV export functionality
- ✅ "Total Properties" stats display

---

## For Full Documentation

See **`CLAUDE_REFERENCE.md`** for complete project documentation including:
- Detailed system architecture
- All API endpoint specifications
- Database schemas
- Service layer documentation
- Implementation guides
- Complete data flow diagrams

---

## Locked Policy

**DO NOT change the AI extraction method.**
- ✅ **USE**: `playwright_scraper.py` with `ai_full_extractor.py`
- ❌ **DO NOT USE**: Any `.DEPRECATED` files
- ❌ **DO NOT SKIP**: AI extraction to save cost

See `EXTRACTION_METHOD_LOCKED.md` for details.
