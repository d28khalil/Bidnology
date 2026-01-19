# Scraper Investigation: Not Saving to Database

**Started:** 2026-01-15
**Status:** ✅ **RESOLVED** - All fixes deployed and working

---

## Final Status (2026-01-15 16:00)

### ✅ All Systems Operational:

1. **Scraper → Database** ✅ WORKING
   - Fixed: Scraper now checks `SUPABASE_SERVICE_ROLE_KEY` env var
   - Properties are being saved to database
   - Last update: `2026-01-15 15:28:54` (confirmed working)

2. **Auto-Enrichment** ✅ WORKING (for new properties only)
   - Scraper runs in webhook mode (`--use-webhook` flag)
   - New properties trigger automatic Zillow enrichment
   - Updated properties do NOT re-enrich (saves API calls)

3. **Timeout** ✅ FIXED
   - Increased from 10 minutes → 20 minutes
   - Sufficient for AI extraction with GPT-4o

4. **pg_cron Jobs** ✅ CONFIGURED
   - Daily scrape: `0 7 * * *` (7 AM every day)
   - Hourly Discord reports: `0 * * * *` (every hour at :00)

5. **Discord Reports** ⚠️ NEEDS CONFIGURATION
   - pg_cron job configured correctly
   - **User must add** `DISCORD_WEBHOOK_URL` in Coolify environment variables

---

## Complete Timeline of Fixes

### Fix #1: Database Connection Issue (Commit `8fb1d42`)
**Problem:** Scraper looked for `SUPABASE_KEY` but env had `SUPABASE_SERVICE_ROLE_KEY`
```python
# playwright_scraper.py line 252 (AFTER FIX)
key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
```

### Fix #2: Timeout Too Short (Commit `9454a1e`)
**Problem:** 10-minute timeout insufficient for AI extraction
```python
# webhook_server/app.py line 691
timeout=1200,  # 20 minute timeout (increased from 10 min)
```

### Fix #3: Auto-Enrichment Not Triggering (Commit `2defcc1`)
**Problem:** Scraper saved directly to DB, bypassing enrichment
```python
# webhook_server/app.py
cmd = [
    PYTHON_PATH,
    str(SCRAPER_PATH),
    "--counties", county,
    "--incremental" if incremental else "",
    "--no-output" if no_output else "",
    "--use-webhook",  # Enable webhook mode for auto-enrichment
]

# Set WEBHOOK_SERVER_URL for callback
env["WEBHOOK_SERVER_URL"] = webhook_url
```

---

## How It Works Now

### Scraping Flow:
```
changedetection.io (detects changes)
    ↓
webhook: POST /webhooks/changedetection
    ↓
scraper runs (subprocess with --use-webhook)
    ↓
scraper sends properties to: POST /webhook/property
    ↓
property saved to database
    ↓
if NEW property: auto-enrichment triggered
    ↓
Zillow enrichment runs in background
```

### Scheduled Jobs:
```
Daily @ 7 AM:  pg_cron → /webhooks/scheduled → scrape all 16 counties
Hourly @ :00:  pg_cron → /webhooks/hourly-report → Discord summary
```

---

## Configuration Checklist

### ✅ Done (in code):
- [x] Scraper checks correct Supabase env var
- [x] Scraper timeout increased to 20 minutes
- [x] Scraper uses webhook mode for auto-enrichment
- [x] WEBHOOK_SERVER_URL set for scraper callback
- [x] pg_cron jobs configured correctly

### ⚠️ User Action Required:
- [ ] Add `DISCORD_WEBHOOK_URL` in Coolify environment variables

---

## Environment Variables Required

### Already Set:
```
SUPABASE_URL=https://oppolxuvxaifruigosty.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service_role_key>
WEBHOOK_SECRET=162999e4d811bbf671042bc9580b8a693e63b895c44dca7198a734537470bac7
SCHEDULE_SECRET=a7f3d9e2c8b41f6a5e3d7c9b2f8a4e1d3c5b7a9e6f2d4c8b1a3e5f7d9c2b4a6e8
OPENAI_API_KEY=<openai_key>
WEBHOOK_SERVER_URL=https://app.bidnology.com
```

### Need to Add in Coolify:
```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

---

## Testing Commands

### Test Scraper Directly:
```bash
curl -X POST "https://app.bidnology.com/webhooks/changedetection" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: 162999e4d811bbf671042bc9580b8a693e63b895c44dca7198a734537470bac7" \
  -d '{"watch_title": "CivilView | Essex", "watch_url": "https://salesweb.civilview.com/Sales/SalesSearch?countyId=2"}'
```

### Test Discord Report:
```bash
curl -X POST "https://app.bidnology.com/webhooks/hourly-report" \
  -H "X-Schedule-Secret: a7f3d9e2c8b41f6a5e3d7c9b2f8a4e1d3c5b7a9e6f2d4c8b1a3e5f7d9c2b4a6e8"
```

### Check Database Status:
```sql
SELECT
    COUNT(*) as total_properties,
    MAX(updated_at) as last_update,
    COUNT(CASE WHEN updated_at > NOW() - INTERVAL '24 hours' THEN 1 END) as updated_last_24h
FROM foreclosure_listings;
```

---

## Git Commits Deployed

| Commit | Message |
|--------|---------|
| `2defcc1` | Fix: Enable auto-enrichment when scraper runs via webhook |
| `9454a1e` | Fix: Increase scraper timeout from 10 to 20 minutes |
| `8fb1d42` | Fix: Scraper not saving to database - check SUPABASE_SERVICE_ROLE_KEY |
| `68970de` | Fix: Change webhook to run scraper synchronously |
| `60e2b52` | Docs: Update investigation with root cause finding |

---

## Resources

- **changedetection.io:** https://change.emprezario.com
- **Webhook Server:** https://app.bidnology.com
- **Coolify Dashboard:** https://emprezario.com
- **GitHub Repo:** https://github.com/d28khalil/salesweb-crawl

---

## Historical Investigation Notes

### Original Problem (2026-01-15 14:00)
The scraper runs successfully (logs show "Scrape completed: True") but **properties are not being saved to the database**. Last database update was **January 11, 2026** (4+ days ago).

### pg_cron Jobs Fixed (2026-01-15 14:15)
**Found Issues:**
1. **Job 1** was calling `schedule_daily_scrape()` which only created queue records
2. **Job 2** had SQL syntax error in JSONB headers

**Fixes Applied:**
- Replaced Job 1 with proper HTTP webhook call to `/webhooks/scheduled`
- Fixed Job 2 SQL syntax for hourly Discord reports

### Root Cause Discovery (2026-01-15 15:30)
**Root Cause:** Scraper (`playwright_scraper.py:250`) looked for `SUPABASE_KEY` but the webhook server environment has `SUPABASE_SERVICE_ROLE_KEY`, causing Supabase connection to be disabled.

**Solution:** Scraper now checks both environment variables:
```python
key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
```
