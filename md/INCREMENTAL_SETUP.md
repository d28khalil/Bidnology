# Incremental Scraping Setup Guide

## PR Summary

### Files Added
- `webhook_server/app.py` - FastAPI webhook server
- `webhook_server/README.md` - Webhook server documentation
- `supabase_migration_incremental.sql` - Database migration for incremental tracking

### Files Modified
- `scraper_hybrid.py` - Added incremental mode, hash-based change detection
- `requirements.txt` - Added FastAPI, uvicorn, pydantic
- `.env.example` - Added WEBHOOK_SECRET

---

## 1. Run Database Migration

**In Supabase SQL Editor, run:**

```sql
-- Add incremental tracking columns
ALTER TABLE sheriff_sales
ADD COLUMN IF NOT EXISTS normalized_address TEXT,
ADD COLUMN IF NOT EXISTS listing_row_hash TEXT,
ADD COLUMN IF NOT EXISTS detail_hash TEXT,
ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS is_removed BOOLEAN DEFAULT FALSE;

-- Create indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_sheriff_sales_county_norm_addr
ON sheriff_sales (county, normalized_address)
WHERE normalized_address IS NOT NULL AND normalized_address != '';

CREATE INDEX IF NOT EXISTS idx_sheriff_sales_county_last_seen
ON sheriff_sales (county, last_seen_at);

-- Backfill existing records
UPDATE sheriff_sales
SET normalized_address = LOWER(TRIM(REGEXP_REPLACE(address, '\s+', ' ', 'g')))
WHERE normalized_address IS NULL AND address IS NOT NULL AND address != '';

UPDATE sheriff_sales
SET first_seen_at = COALESCE(created_at, NOW()),
    last_seen_at = COALESCE(updated_at, created_at, NOW())
WHERE first_seen_at IS NULL;
```

Or run the full migration file:
```bash
# Copy supabase_migration_incremental.sql contents to Supabase SQL Editor
```

---

## 2. Install Dependencies

```bash
source venv/bin/activate
pip install fastapi uvicorn pydantic
```

---

## 3. Configure Environment

Add to `.env`:
```bash
WEBHOOK_SECRET=your-secure-secret-here
```

---

## 4. Test Commands

### Manual Incremental Run
```bash
python scraper_hybrid.py --counties "Middlesex" --incremental
```

### Dry Run (No DB Writes)
```bash
python scraper_hybrid.py --counties "Middlesex" --incremental --dry-run
```

### Full Scrape (Non-Incremental)
```bash
python scraper_hybrid.py --counties "Middlesex"
```

### With Tombstoning
```bash
python scraper_hybrid.py --counties "Middlesex" --incremental --tombstone-missing
```

---

## 5. Start Webhook Server

```bash
export WEBHOOK_SECRET="your-secure-secret-here"
uvicorn webhook_server.app:app --host 0.0.0.0 --port 8080
```

---

## 6. Simulate Webhook Locally

```bash
curl -X POST http://localhost:8080/webhooks/changedetection \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secure-secret-here" \
  -d '{
    "watch_title": "CivilView | Middlesex",
    "watch_url": "https://salesweb.civilview.com/?countyId=73",
    "diff_added": "New listing detected",
    "diff_removed": ""
  }'
```

---

## 7. changedetection.io Setup

### Watch Naming Convention
```
CivilView | {CountyName}
```

Examples:
- `CivilView | Middlesex`
- `CivilView | Bergen`
- `CivilView | Essex`

### Webhook Body Template (Jinja2)
```json
{
  "watch_uuid": {{ watch_uuid|tojson }},
  "watch_title": {{ watch_title|tojson }},
  "watch_url": {{ watch_url|tojson }},
  "diff_added": {{ diff_added|tojson }},
  "diff_removed": {{ diff_removed|tojson }},
  "current_snapshot": {{ current_snapshot|tojson }},
  "triggered_text": {{ triggered_text|tojson }},
  "ts": {{ now|tojson }}
}
```

### Webhook Headers
```
Content-Type: application/json
X-Webhook-Secret: your-secure-secret-here
```

---

## Incremental Algorithm

```
For each property in listing:

1. Extract preview from row (address, date, status, sheriff#)
2. Compute listing_row_hash = SHA256(county|address|date|sheriff#|status)
3. Lookup by normalized_address in database

Decision:
├── NOT FOUND → NEW
│   └── Click details, parse, INSERT
│
├── FOUND + hash MATCHES → SKIP
│   └── Just update last_seen_at (no click!)
│
└── FOUND + hash DIFFERS → CHANGED
    └── Click details, parse, UPDATE + append status_history
```

---

## Acceptance Criteria

| Requirement | Status |
|-------------|--------|
| Webhook triggers county-specific scrape | ✅ |
| Duplicate webhooks don't create dupes | ✅ |
| Changed listings update row + append history | ✅ |
| No deletes (soft tombstone optional) | ✅ |
| Detail clicks only for NEW/CHANGED | ✅ |
| Per-county locking prevents overlaps | ✅ |

---

## CLI Flags Reference

| Flag | Description |
|------|-------------|
| `--incremental` | Only scrape new/changed properties |
| `--dry-run` | Log actions without database writes |
| `--no-output` | Skip CSV/JSON file generation |
| `--tombstone-missing` | Mark unseen records as `is_removed=true` |
| `--counties` | Filter to specific counties |
| `--max-per-county` | Limit properties per county |

---

## Notes & Assumptions

1. **Watch Title Format**: Must be exactly `CivilView | {CountyName}` for webhook to work
2. **Concurrency**: Single worker recommended to ensure locking works
3. **Tombstoning**: Disabled by default; enable with `--tombstone-missing`
4. **Hash Stability**: Same data always produces same hash (deterministic)
5. **Status History**: Appended as JSONB array with timestamps
