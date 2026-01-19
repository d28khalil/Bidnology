# Full Scrape Process Protocol

**Architecture:** Playwright + GPT-4o Scraping → Zillow Enrichment → Supabase Storage

**Last Updated:** 2025-01-16

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 1: AI-Augmented Web Scraping](#phase-1-ai-augmented-web-scraping)
3. [Phase 2: Zillow Enrichment](#phase-2-zillow-enrichment)
4. [Data Flow Diagram](#data-flow-diagram)
5. [Configuration](#configuration)
6. [Cost Analysis](#cost-analysis)
7. [Troubleshooting](#troubleshooting)

---

## Overview

This protocol describes the complete data pipeline for acquiring, enriching, and storing foreclosure listing data from New Jersey sheriff sales.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE DATA PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  salesweb.civilview.com → Playwright → GPT-4o → Webhook → Zillow → Supabase │
│                             (Scrape)      (Extract)   (Enrich)   (Store)    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Term | Definition |
|------|------------|
| **AI-Augmented Scraping** | Using LLMs to extract structured data from HTML instead of brittle regex patterns |
| **Screenshot Fallback** | When HTML extraction fails, capturing a screenshot and using GPT-4o Vision |
| **Zillow Enrichment** | Fetching additional property data (Zestimate, beds, baths, etc.) via RapidAPI |
| **Pro/ByAddress** | The primary Zillow endpoint that returns ZPID and basic property info |
| **Auto-Enrichment** | Automatically triggering enrichment after a property is scraped |

---

## Phase 1: AI-Augmented Web Scraping

### 1.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: SCRAPING & EXTRACTION                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. COUNTY DISCOVERY                                                        │
│     ├── GET salesweb.civilview.com                                         │
│     ├── Parse HTML for county links                                         │
│     └── Build county list with URLs                                         │
│                                                                             │
│  2. LISTING PAGE SCRAPE (Per County)                                        │
│     ├── Navigate to county listing URL                                      │
│     ├── Query all 'a[href*="SaleDetails"]' links                            │
│     └── For each listing row:                                               │
│         │                                                                   │
│         ├── Extract preview data (address, dates, numbers)                  │
│         ├── Compute listing_row_hash (SHA256)                               │
│         ├── INCREMENTAL CHECK:                                              │
│         │   ├── If hash unchanged → SKIP                                    │
│         │   └── If hash changed → FETCH DETAILS                             │
│         │                                                                   │
│         └── [CONTINUE TO STEP 3]                                            │
│                                                                             │
│  3. DETAIL PAGE EXTRACTION                                                  │
│     ├── Click SaleDetails link                                              │
│     ├── Wait for networkidle                                                │
│     ├── Capture raw HTML                                                    │
│     └── Store raw_html for AI processing                                    │
│                                                                             │
│  4. AI EXTRACTION (Primary + Fallback)                                      │
│     ├── PRIMARY: extract_all_data_from_html()                              │
│     │   ├── Send HTML to GPT-4o-mini                                        │
│     │   ├── Prompt includes full unified schema (27+ fields)               │
│     │   ├── Response format: JSON                                           │
│     │   └── Return unified_data + ai_metadata                              │
│     │                                                                       │
│     ├── QUALITY CHECK:                                                      │
│     │   ├── Check property_address exists                                   │
│     │   ├── Check at least 1 monetary/date field                           │
│     │   └── Calculate quality score (0.0-1.0)                              │
│     │                                                                       │
│     └── FALLBACK (if quality fails):                                        │
│         ├── capture_screenshot_crawl4ai()                                   │
│         │   └── Return base64 screenshot                                   │
│         └── extract_from_screenshot()                                       │
│             ├── Send screenshot + prompt to GPT-4o (vision)                │
│             └── Return unified_data + ai_metadata                          │
│                                                                             │
│  5. DATA MAPPING & STORAGE                                                  │
│     ├── Map AI fields to database columns                                   │
│     ├── Convert monetary strings to float                                  │
│     ├── Store full AI result in raw_data JSONB                             │
│     └── UPGERT to Supabase OR send to Webhook                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Files

| File | Purpose |
|------|---------|
| `playwright_scraper.py` | Main scraper with Playwright browser automation |
| `ai_full_extractor.py` | GPT-4o extraction with screenshot fallback |
| `scraper_helper.py` | Field normalization and monetary extraction |
| `webhook_client.py` | Client for sending data to webhook server |

### 1.3 Unified Schema (27+ Fields)

The AI extracts all fields mapped to a unified schema:

#### Core Identifiers
- `property_id` - Unique ID from source website
- `sheriff_number` - Sheriff sale number (e.g., "F-25000160")
- `case_number` - Court case/docket number
- `parcel_id` - Parcel/lot number from description

#### Parties
- `plaintiff` - Lender/bank name
- `defendant` - Property owner name
- `plaintiff_attorney` - Attorney for plaintiff

#### Address Information (Critical for Zillow API)
- `property_address` - Full address in Title Case (e.g., "123 Main Street")
- `city` - City in Title Case (e.g., "Cherry Hill")
- `state` - State (default "NJ")
- `zip_code` - ZIP code (5 digits only)

#### Dates
- `sale_date` - Auction date (YYYY-MM-DD)
- `filing_date` - Date lawsuit filed
- `judgment_date` - Date judgment entered
- `writ_date` - Date writ issued

#### Monetary Fields (3 Categories)

**Category A: Court/Debt Amounts (What Is Owed)**
- `judgment_amount` - Court-awarded debt
- `writ_amount` - Writ enforcement amount
- `costs` - Court costs/fees

**Category B: Auction/Sale Floor Amounts (What Bidding Starts At)**
- `opening_bid` - Minimum bid to start auction
- `minimum_bid` - Minimum acceptable bid

**Category C: Estimated/Approximate Amounts (Reserve Prices)**
- `approx_upset` - Reserve/UPSET price (MINIMUM court will accept)
- `sale_price` - Final sale price (if sold)

#### Other Fields
- `property_status` - scheduled, adjourned_plaintiff, adjourned_court, sold, cancelled
- `description` - Legal description, notes
- `property_type` - residential, commercial, vacant land
- `lot_size` - Property size
- `sale_terms` - Special terms

### 1.4 Incremental Mode

Hash-based change detection skips unchanged listings:

```python
# Composite key: (normalized_address, sheriff_number)
listing_hash = SHA256(county + address + dates + numbers)

if existing.listing_row_hash == listing_hash:
    # SKIP - no changes, just update last_seen_at
else:
    # CHANGED - fetch details and update
```

### 1.5 Running the Scraper

```bash
# Basic scrape (all counties) - Direct Supabase mode
python playwright_scraper.py

# Incremental mode (only new/changed)
python playwright_scraper.py --incremental

# Webhook mode (triggers auto-enrichment)
python playwright_scraper.py --use-webhook

# Specific counties
python playwright_scraper.py --counties Salem Cumberland

# Dry run (no database writes)
python playwright_scraper.py --dry-run

# Schedule mode (polls database for jobs)
python playwright_scraper.py --schedule-mode --poll-interval 300
```

---

## Phase 2: Zillow Enrichment (Pro/ByAddress Only)

### 2.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: ZILLOW ENRICHMENT (Pro/ByAddress Only)          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Webhook receives property data → Queue enrichment → Call RapidAPI          │
│                                                                             │
│  SINGLE ENDPOINT:                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ pro_byaddress - Get ZPID + basic property info                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ENRICHMENT FLOW:                                                           │
│  1. Receive property via webhook (property_address, city, state, zip)       │
│  2. Call GET /pro/byaddress with full address                               │
│  3. Store results in zillow_enrichment table                               │
│  4. Update foreclosure_listings with status and zpid                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Pro/ByAddress Endpoint

```
GET https://private-zillow.p.rapidapi.com/pro/byaddress
Parameters: propertyaddress (full address)
Cost: 1 RapidAPI request per property
```

**Returns:**
| Field | Description |
|-------|-------------|
| `zpid` | Zillow Property ID (unique identifier) |
| `zestimate` | Zillow's estimated market value |
| `rentZestimate` | Zillow's estimated rent |
| `bedrooms` | Number of bedrooms |
| `bathrooms` | Number of bathrooms |
| `sqft` | Square footage |
| `year_built` | Year property was built |
| `lot_size` | Lot size in acres |
| `property_type` | Property type (SINGLE_FAMILY, MULTI_FAMILY, etc.) |
| `last_sold_price` | Most recent sale price |
| `last_sold_date` | Most recent sale date |

### 2.3 Key Files

| File | Purpose |
|------|---------|
| `bulk_enrich_pro_only.py` | Manual bulk enrichment script (pro/byaddress only) |
| `webhook_client.py` | Client for sending data to webhook server |
| `webhook_server/enrichment_routes.py` | FastAPI routes for enrichment |

### 2.4 Enrichment Status Values

| Status | Description |
|--------|-------------|
| `pending` | Property scraped, not yet enriched |
| `auto_enriched` | Pro/byaddress enrichment completed |
| `failed` | Enrichment failed |
| `not_enriched` | Explicitly marked for manual enrichment |

### 2.5 Triggering Enrichment

#### Automatic (via Webhook)

```bash
# Run scraper with webhook mode
python playwright_scraper.py --use-webhook --auto-enrich

# Flow:
# 1. Scraper sends data to http://localhost:8080/webhook/property
# 2. Webhook stores property and queues enrichment if auto_enrich=true
# 3. Background task calls Zillow pro/byaddress endpoint
# 4. Results stored in zillow_enrichment table
```

#### Manual (Bulk Script)

```bash
# Enrich all properties that need enrichment
python bulk_enrich_pro_only.py

# Features:
# - Fetches properties with status 'not_enriched', 'pending', or null
# - Processes in batches (default: 5 concurrent)
# - Only calls pro/byaddress endpoint (1 request per property)
# - Updates enrichment status to 'auto_enriched' after completion
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              COMPLETE END-TO-END FLOW                                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│ salesweb.civilview   │
│   .com               │
└──────────┬───────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PLAYWRIGHT SCRAPER                                         │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │  1. Launch headless Chromium browser                                             │  │
│  │  2. Navigate county listings                                                    │  │
│  │  3. Extract listing preview data                                                 │  │
│  │  4. Compute hash for change detection                                            │  │
│  │  5. Click detail pages (if NEW or CHANGED)                                       │  │
│  │  6. Capture raw HTML                                                             │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                               │
│                                        ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                     AI FULL EXTRACTOR (ai_full_extractor.py)                      │  │
│  │  ┌────────────────────────────────────────────────────────────────────────────┐   │  │
│  │  │ PRIMARY: GPT-4o-mini text extraction                                        │   │  │
│  │  │   Input: Raw HTML + County name + Schema definition (27+ fields)            │   │  │
│  │  │   Output: unified_data dict + ai_metadata                                    │   │  │
│  │  └────────────────────────────────────────────────────────────────────────────┘   │  │
│  │                                        │                                          │  │
│  │  ┌────────────────────────────────────────────────────────────────────────────┐   │  │
│  │  │ QUALITY CHECK                                                                │   │  │
│  │  │   - Has property_address?                                                    │   │  │
│  │  │   - Has 1+ monetary/date field?                                              │   │  │
│  │  │   - Score: 0.0 - 1.0                                                         │   │  │
│  │  └────────────────────────────────────────────────────────────────────────────┘   │  │
│  │                                        │                                          │  │
│  │  ┌────────────────────────────────────────────────────────────────────────────┐   │  │
│  │  │ FALLBACK (if quality check fails)                                            │   │  │
│  │  │   1. capture_screenshot_crawl4ai() → base64 image                           │   │  │
│  │  │   2. extract_from_screenshot() → GPT-4o Vision → unified_data               │   │  │
│  │  └────────────────────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                       │
                    ▼                                       ▼
┌───────────────────────────────┐           ┌───────────────────────────────────────────┐
│   DIRECT SUPABASE MODE        │           │         WEBHOOK MODE (Recommended)          │
│                               │           │                                               │
│  ┌─────────────────────────┐  │           │  ┌─────────────────────────────────────────┐ │
│  │ upsert_property()       │  │           │  │ POST /webhook/property                 │ │
│  │   ↓                     │  │           │  │   ↓                                    │ │
│  │ foreclosure_listings    │  │           │  │ Webhook receives property data          │ │
│  │   table                 │  │           │  │   ↓                                    │ │
│  └─────────────────────────┘  │           │  │ Store in foreclosure_listings           │ │
└───────────────────────────────┘           │  │   ↓                                    │
                                            │  │ IF auto_enrich=true:                   │
                                            │  │   ↓                                    │
                                            │  │ Queue background enrichment task       │
                                            │  └─────────────────────────────────────────┘ │
                                            │                    │                        │
                                            └────────────────────┼────────────────────────┘
                                                                 │
                    ┌────────────────────────────────────────────┼────────────────────────┐
                    │                                            │                        │
                    │ IF WEBHOOK MODE                            │                        │
                    │                                            │                        │
                    ▼                                            ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              ZILLOW ENRICHMENT SERVICE                                         │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  1. Resolve Settings (Admin → County → User)                                            │  │
│  │  2. GET /pro/byaddress (propertyaddress) → Get ZPID + basic info                         │  │
│  │  3. Call additional endpoints based on settings:                                         │  │
│  │     - /custom_ad/byzpid (zpid) → Photos, details                                         │  │
│  │     - /similar (byzpid) → Active comps for ARV                                           │  │
│  │     - /nearby (byzpid) → Nearby properties                                                │  │
│  │     - /pricehistory (byzpid) → Price history                                              │  │
│  │     - /taxinfo (byzpid) → Tax history                                                     │  │
│  │     - /climate (byzpid) → Climate risk                                                    │  │
│  │     - /walk_transit_bike (zpid) → Location scores                                         │  │
│  │     - /housing_market (regionId) → Market trends                                          │  │
│  │     - /rental_market (regionId) → Rental trends                                           │  │
│  │     - /ownerinfo (zpid) → Owner/agent info                                                │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                                        │
│                                        ▼                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  STORE RESULTS                                                                           │  │
│  │   ↓                                                                                      │  │
│  │  zillow_enrichment table (JSONB columns for complex data)                                │  │
│  │   - zpid, zestimate, bedrooms, bathrooms, sqft, year_built                               │  │
│  │   - comps, similar_properties, nearby_properties                                         │  │
│  │   - price_history, tax_history, climate_risk                                             │  │
│  │   - images, walk_score, transit_score, bike_score                                        │  │
│  │   - api_call_count, endpoints_attempted, endpoints_succeeded                             │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                                        │
│                                        ▼                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  UPDATE foreclosure_listings                                                              │  │
│  │   - zillow_zpid = zpid                                                                    │  │
│  │   - zillow_enrichment_status = 'auto_enriched' or 'fully_enriched'                        │  │
│  │   - zillow_enriched_at = NOW()                                                            │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# Supabase (Required)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGc...  # or SUPABASE_SERVICE_ROLE_KEY

# OpenAI (Required for scraping)
OPENAI_API_KEY=sk-...

# RapidAPI (Required for enrichment)
RAPIDAPI_KEY=xxx...

# Webhook Server (Optional)
WEBHOOK_SERVER_URL=http://localhost:8080
WEBHOOK_SECRET=your_secret_here
```

### Dependencies

```
playwright>=1.40.0       # Browser automation
httpx>=0.27.0            # Fast HTTP client
beautifulsoup4>=4.12.0   # HTML parsing
supabase>=2.0.0          # Database client
openai>=1.0.0            # GPT-4o / GPT-4o-mini
crawl4ai>=0.4.0          # Screenshot capture
fastapi>=0.109.0         # Webhook server
uvicorn>=0.27.0          # ASGI server
```

---

## Cost Analysis

### Scraping Costs (GPT-4o-mini)

| Metric | Value |
|--------|-------|
| Model | gpt-4o-mini |
| Input Cost | $0.15 per 1M tokens |
| Output Cost | $0.60 per 1M tokens |
| Avg Input/Property | ~1,000 tokens |
| Avg Output/Property | ~500 tokens |

**Estimated: ~$0.0005 per property (~$0.25 for 500 properties)**

### Enrichment Costs (RapidAPI)

| Endpoint | Requests Per Property | Notes |
|----------|----------------------|-------|
| pro_byaddress | 1 | Required (gets ZPID) |
| custom_ad_byzpid | 1 | Optional (photos) |
| similar | 1 | Optional (comps) |
| nearby | 1 | Optional |
| pricehistory | 1 | Optional |
| taxinfo | 1 | Optional |
| climate | 1 | Optional |
| walk_transit_bike | 1 | Optional |
| housing_market | 1 | Optional |
| rental_market | 1 | Optional |
| ownerinfo | 1 | Optional |

**Cost varies by RapidAPI plan. Pro/byaddress only = 1 request/property.**

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Scraper fails to connect | Check SUPABASE_URL and KEY are set |
| AI extraction returns empty | Verify OPENAI_API_KEY is valid |
| Screenshot fallback fails | Ensure crawl4ai is installed and browser available |
| Enrichment status stuck "pending" | Check webhook server is running and RAPIDAPI_KEY is valid |
| Properties not auto-enriching | Ensure `--use-webhook` flag is set and webhook server is accessible |
| Hash mismatch causing re-scrapes | Check normalized_address format consistency |

### Debug Mode

```bash
# Enable verbose output
python playwright_scraper.py --counties Salem --dry-run

# Check webhook server logs
# Logs printed to console with timestamp and detail level

# Test specific property enrichment
curl -X POST http://localhost:8080/api/enrichment/properties/123/enrich
```

---

## Appendix: API Endpoints Reference

### Webhook Server Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook/property` | Receive scraped property data |
| GET | `/api/enrichment/status` | Get enrichment statistics |
| GET | `/api/enrichment/properties` | List foreclosure properties |
| GET | `/api/enrichment/properties/{id}` | Get property details |
| POST | `/api/enrichment/properties/{id}/enrich` | Trigger enrichment |
| POST | `/api/enrichment/properties/{id}/skip-trace` | Skip trace property |
| GET | `/api/enrichment/settings/admin` | Get admin settings |
| PUT | `/api/enrichment/settings/admin` | Update admin settings |
| GET | `/api/enrichment/settings/county` | List county settings |
| POST | `/api/enrichment/settings/county` | Create county settings |
| PUT | `/api/enrichment/settings/county/{id}/{state}` | Update county settings |

---

*Document Version: 1.0*
*For questions or updates, refer to the source code documentation.*
