# Sheriff Sales Scraper - Technical Documentation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        scraper_hybrid.py                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │    httpx     │    │  Playwright  │    │   Supabase   │       │
│  │  (HTTP GET)  │    │  (Browser)   │    │  (Database)  │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ County List  │    │Detail Pages  │    │  Duplicate   │       │
│  │   Fetching   │    │  Scraping    │    │  Detection   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Output Files   │
                    │  CSV / JSON      │
                    └──────────────────┘
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| HTTP Client | `httpx` | Fast async HTTP requests for county list |
| Browser Automation | `playwright` | Headless Chrome for JS-rendered pages |
| HTML Parsing | `beautifulsoup4` | Extract data from HTML |
| Database | `supabase` (PostgreSQL) | Store properties, duplicate detection |
| Config | `python-dotenv` | Environment variable management |

## Why This Architecture?

### The Problem
The target website (salesweb.civilview.com) has **session-based navigation**:
- Direct URL access to detail pages returns a **302 redirect** to homepage
- You must navigate through the county listing page first
- The site validates the referrer/session before serving detail pages

### The Solution
**Hybrid approach:**
1. **httpx** for simple requests (county list) - fast, lightweight
2. **Playwright** for detail pages - real browser that maintains session state

## Data Flow

```
1. STARTUP
   ├── Load .env (SUPABASE_URL, SUPABASE_KEY)
   ├── Connect to Supabase
   └── Load existing addresses for duplicate detection

2. COUNTY DISCOVERY (httpx)
   ├── GET https://salesweb.civilview.com
   ├── Parse HTML with BeautifulSoup
   └── Extract county links (countyId parameter)

3. PROPERTY SCRAPING (Playwright - per county)
   │
   │  ┌─────────────────────────────────────────┐
   │  │  For each county:                       │
   │  │  1. Navigate to county listing page     │
   │  │  2. Find all "View Details" links       │
   │  │  3. For each property:                  │
   │  │     a. Check address against DB         │
   │  │     b. If duplicate → SKIP (fast!)      │
   │  │     c. If new → Click link              │
   │  │     d. Parse detail page                │
   │  │     e. Go back to listing               │
   │  │  4. Save batch to Supabase              │
   │  └─────────────────────────────────────────┘
   │
   └── Repeat for next county

4. OUTPUT
   ├── Save to CSV
   ├── Save to JSON
   └── Properties already in Supabase
```

## Key Components

### 1. Duplicate Detection

```python
# On startup: Load all existing addresses from Supabase
async def load_existing_addresses():
    response = supabase.table('sheriff_sales').select('address').execute()
    for row in response.data:
        existing_addresses.add(normalize_address(row['address']))

# Before scraping each property: Check if exists
def is_duplicate(address: str) -> bool:
    return normalize_address(address) in existing_addresses
```

**Why address-based?**
- User requirement: detect duplicates by property address
- Addresses are normalized (lowercase, trimmed) for consistent matching

### 2. Page Parsing

The detail pages have inconsistent structure across counties. We use multiple strategies:

```python
# Strategy 1: Regex patterns on page text
patterns = [
    (r"Sheriff\s*#\s*:\s*(\S+)", "sheriff_number"),
    (r"Court\s*Case\s*#\s*:\s*(\S+)", "court_case_number"),
    (r"Judgment\s*:?\s*\$?([\d,]+\.?\d*)", "approx_judgment"),
]

# Strategy 2: Label:Value sibling pattern
for label in ["Property Address:", "Plaintiff:", "Defendant:"]:
    label_elem = soup.find(string=label)
    if label_elem:
        value = label_elem.parent.next_sibling.get_text()
```

### 3. Browser Session Management

```python
async def scrape_county(browser, county):
    # Create isolated browser context (like incognito)
    context = await browser.new_context()
    page = await context.new_page()

    # Navigate to county listing (establishes session)
    await page.goto(county_url, wait_until="networkidle")

    # Now we can click through to details
    for link in detail_links:
        await link.click()  # Session preserved
        # ... parse page ...
        await page.go_back()  # Return to listing

    await context.close()
```

## Database Schema

```sql
CREATE TABLE sheriff_sales (
    id BIGSERIAL PRIMARY KEY,

    -- Core info
    county TEXT,
    sheriff_number TEXT,
    court_case_number TEXT,
    sale_date TEXT,

    -- Parties
    plaintiff TEXT,
    defendant TEXT,

    -- Property (address used for duplicate detection)
    address TEXT,
    description TEXT,

    -- Financial
    approx_judgment TEXT,
    upset_amount TEXT,
    minimum_bid TEXT,

    -- Attorney
    attorney TEXT,
    attorney_phone TEXT,

    -- Status tracking (JSONB array)
    status_history JSONB,
    current_status TEXT,

    -- Metadata
    detail_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast duplicate lookups
CREATE INDEX idx_sheriff_sales_address ON sheriff_sales (address);
```

## Performance Characteristics

| Scenario | Time | Notes |
|----------|------|-------|
| First run (118 properties) | ~4 min | Must fetch all detail pages |
| Re-run (all duplicates) | ~4 sec | Skips at listing level, no clicks |
| Mixed (some new) | Varies | Only fetches new property details |

### Why duplicates are fast:
```python
# Before clicking (slow operation), check address from listing row
row_text = await link.evaluate("el => el.closest('tr').innerText")
address_preview = extract_address_from_row(row_text)

if is_duplicate(address_preview):
    continue  # Skip without clicking!
```

## File Structure

```
salesweb-crawl/
├── scraper_hybrid.py      # Main scraper with Supabase integration
├── scraper_fast.py        # HTTP-only version (listings only, no details)
├── scraper.py             # Original crawl4ai version (deprecated)
├── .env                   # Supabase credentials
├── .env.example           # Template for credentials
├── requirements.txt       # Python dependencies
├── supabase_schema.sql    # Database table creation script
└── TECHNICAL_DOCS.md      # This file
```

## Environment Variables

```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key
```

## CLI Usage

```bash
# Scrape specific county
python scraper_hybrid.py --counties "Middlesex"

# Scrape multiple counties
python scraper_hybrid.py --counties "Middlesex" "Bergen" "Essex"

# Scrape all counties
python scraper_hybrid.py

# Limit properties per county (for testing)
python scraper_hybrid.py --max-per-county 10

# Disable Supabase (local files only)
python scraper_hybrid.py --no-supabase

# Output options
python scraper_hybrid.py --output my_data.csv --json
```

## Error Handling

1. **Network timeouts**: Retries by navigating back to county page
2. **Missing fields**: Gracefully returns empty string
3. **Supabase errors**: Logs error, continues scraping
4. **Table not found**: Creates graceful warning, disables DB features

## Extending the Scraper

### Add new field extraction:
```python
# In _parse_detail_page(), add to patterns list:
patterns = [
    # ... existing patterns ...
    (r"New\s*Field\s*:\s*(.+)", "new_field"),
]
```

### Add new county-specific parsing:
```python
# Different counties may have different label names
for label_text, attr in [
    ("Property Address:", "address"),  # NJ counties
    ("Address:", "address"),           # PA counties
    # Add more variations as discovered
]:
```

## Dependencies

```txt
httpx>=0.27.0          # Async HTTP client
playwright>=1.40.0     # Browser automation
beautifulsoup4>=4.12.0 # HTML parsing
supabase>=2.0.0        # Database client
python-dotenv>=1.0.0   # Environment variables
lxml>=5.0.0            # Fast HTML parser backend
```

## Security Notes

1. **Credentials**: Never commit `.env` file (add to `.gitignore`)
2. **Rate limiting**: Scraper has built-in delays to avoid overwhelming server
3. **Row Level Security**: Enable RLS on Supabase table for production
