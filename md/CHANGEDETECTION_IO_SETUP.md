# changedetection.io Setup for NJ Sheriff Sales

This guide explains how to configure changedetection.io to monitor all 16 New Jersey county sheriff sale websites and trigger webhooks when new properties are detected.

---

## Overview

**Target URLs Pattern:**
```
https://salesweb.civilview.com/Sales/SalesSearch?countyId={COUNTY_ID}
```

**Webhook Endpoint:**
```
POST https://your-domain.com/webhooks/changedetection
```

**Important:** All counties use the **same webhook endpoint**. The county is extracted from the `watch_title` field in the webhook payload, which must follow the format: `CivilView | {CountyName}`

---

## 16 NJ Counties with County IDs

| County Name | County ID | Watch Title Format | Target URL |
|-------------|-----------|-------------------|------------|
| **Atlantic** | 25 | `CivilView | Atlantic` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=25` |
| **Bergen** | 7 | `CivilView | Bergen` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=7` |
| **Burlington** | 3 | `CivilView | Burlington` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=3` |
| **Camden** | 1 | `CivilView | Camden` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=1` |
| **Cape May** | 52 | `CivilView | Cape May` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=52` |
| **Cumberland** | 6 | `CivilView | Cumberland` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=6` |
| **Essex** | 2 | `CivilView | Essex` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=2` |
| **Gloucester** | 19 | `CivilView | Gloucester` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=19` |
| **Hudson** | 10 | `CivilView | Hudson` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=10` |
| **Hunterdon** | 32 | `CivilView | Hunterdon` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=32` |
| **Middlesex** | 73 | `CivilView | Middlesex` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=73` |
| **Monmouth** | 8 | `CivilView | Monmouth` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=8` |
| **Morris** | 9 | `CivilView | Morris` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=9` |
| **Passaic** | 17 | `CivilView | Passaic` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=17` |
| **Salem** | 20 | `CivilView | Salem` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=20` |
| **Union** | 15 | `CivilView | Union` | `https://salesweb.civilview.com/Sales/SalesSearch?countyId=15` |

> **Note:** County IDs are **not sequential**. The dropdown shows 16 counties total with non-sequential IDs (1, 2, 3, 6, 7, 8, 9, 10, 15, 17, 19, 20, 25, 32, 52, 73)

---

## Step-by-Step Setup

### 1. Install changedetection.io

```bash
# Using Docker
docker run -d \
  --name changedetection \
  -p 5000:5000 \
  -v changedetection-data:/datastore \
  ghcr.io/dgtlmoon/changedetection.io:latest

# Or using Docker Compose
cat > docker-compose.yml <<EOF
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

docker-compose up -d
```

### 2. Access changedetection.io

Open: `http://localhost:5000`

### 3. Add Each County as a Watch

For each county, create a new watch with these settings:

#### General Settings
- **URL:** `https://salesweb.civilview.com/Sales/SalesSearch?countyId={COUNTY_ID}`
- **Title:** `NJ Sheriff Sales - {County Name}`
- **Tags:** `nj-sheriff-sales,{county_name}`

#### Check Settings
- **Check Interval:** Every 4 hours (`0 */4 * * *` cron)
- **Method:** `GET`
- **Headers:** (if needed for authentication)
  ```
  User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
  ```

#### Webhook Notification (Trigger)

For each county, add a webhook notification:

**URL:** `https://your-domain.com/webhooks/trigger/{COUNTY_NAME}`

**Method:** `POST`

**Headers:**
```json
{
  "Content-Type": "application/json",
  "X-Webhook-Secret": "YOUR_WEBHOOK_SECRET"
}
```

**Body Template (JSON):**
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

---

## pg_cron Integration

The `add_pg_cron_jobs.sql` migration sets up pg_cron to trigger scraping every 4 hours:

```sql
SELECT cron.schedule(
    'scrape-all-counties-every-4-hours',
    '0 */4 * * *',  -- Every 4 hours (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
    $$
    SELECT
        net.http_post(
            'https://your-domain.com/webhooks/scheduled'::text,
            headers: '{"X-Schedule-Secret": "YOUR_SCHEDULE_SECRET"}'::jsonb,
            body: '{}'::jsonb,
            timeout_milliseconds := 300000  -- 5 minute timeout
        );
    $$
);
```

This works **in parallel** with changedetection.io:
- **pg_cron:** Scrapes all counties every 4 hours as a fallback
- **changedetection.io:** Triggers immediate scrape when new properties detected

---

## Webhook Endpoints

### Scheduled Scrape (pg_cron)
```
POST /webhooks/scheduled
Headers: X-Schedule-Secret: YOUR_SCHEDULE_SECRET
Body: {}
```
- Scrapes all 16 counties sequentially
- Triggered by pg_cron every 4 hours

### Individual County Trigger (changedetection.io)
```
POST /webhooks/trigger/{county_name}
Headers: X-Webhook-Secret: YOUR_WEBHOOK_SECRET
Body: { "county": "Atlantic", "county_id": 1 }
```
- Scrapes a specific county
- Triggered by changedetection.io when changes detected

---

## Environment Variables

Set these in your `.env` file:

```bash
# Webhook Secrets
WEBHOOK_SECRET=your_secure_webhook_secret_here
SCHEDULE_SECRET=your_secure_schedule_secret_here

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# RapidAPI Zillow Enrichment
RAPIDAPI_KEY=your_rapidapi_key_here

# OpenAI (for AI data extraction)
OPENAI_API_KEY=your_openai_api_key_here
```

---

## Testing Your Setup

### 1. Test pg_cron Job
```sql
-- Manually trigger the scheduled scrape
SELECT net.http_post(
    'https://your-domain.com/webhooks/scheduled',
    headers: '{"X-Schedule-Secret": "YOUR_SCHEDULE_SECRET"}'::jsonb,
    body: '{}'::jsonb
);
```

### 2. Test Individual County Webhook
```bash
curl -X POST "https://your-domain.com/webhooks/trigger/Atlantic" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: YOUR_WEBHOOK_SECRET" \
  -d '{"county": "Atlantic", "county_id": 1}'
```

### 3. Verify changedetection.io Watch
1. Go to changedetection.io
2. Click on a county watch
3. Click "Check now" to trigger immediate check
4. Verify webhook is called in server logs

---

## Monitoring

### View pg_cron Job History
```sql
-- View recent job runs
SELECT * FROM cron.job_run_details
WHERE jobid = (
    SELECT jobid FROM cron.schedule
    WHERE jobname = 'scrape-all-counties-every-4-hours'
)
ORDER BY start_time DESC
LIMIT 20;
```

### View Scheduled Jobs
```sql
SELECT * FROM cron.schedule;
```

---

## Troubleshooting

### Webhook Not Firing
1. Check `WEBHOOK_SECRET` matches in both changedetection.io and `.env`
2. Check server logs: `tail -f server.log`
3. Test webhook manually with curl
4. Verify changedetection.io can reach your server (firewall/NGROK if local)

### pg_cron Not Running
1. Verify pg_cron extension is installed:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'pg_cron';
   ```
2. Check job is scheduled:
   ```sql
   SELECT * FROM cron.schedule;
   ```
3. Check for errors in job run details

### County ID Incorrect
1. Visit https://salesweb.civilview.com/Sales/SalesSearch
2. Open browser DevTools (F12)
3. Check the Network tab while selecting counties
4. Note the actual countyId values used in requests

---

## Changedetection.io JSON Filter (Optional)

If you want to only trigger on actual NEW listings (not just any page change), use a JSON filter:

```
$.data.listings[*]
```

This will only trigger the webhook when the listings array changes significantly.

---

## Security Best Practices

1. **Use HTTPS** for all webhook URLs
2. **Rotate secrets** regularly
3. **Set up firewall rules** to only allow requests from changedetection.io
4. **Use environment variables** for secrets (never commit to git)
5. **Rate limiting:** Ensure your server can handle 16 simultaneous scrape requests

---

## Quick Start Script

```bash
#!/bin/bash
# setup-changedetection.sh

DOMAIN="https://your-domain.com"
WEBHOOK_SECRET="YOUR_WEBHOOK_SECRET"

# County list (from actual dropdown IDs)
COUNTIES=(
  "Atlantic:25"
  "Bergen:7"
  "Burlington:3"
  "Camden:1"
  "CapeMay:52"
  "Cumberland:6"
  "Essex:2"
  "Gloucester:19"
  "Hudson:10"
  "Hunterdon:32"
  "Middlesex:73"
  "Monmouth:8"
  "Morris:9"
  "Passaic:17"
  "Salem:20"
  "Union:15"
)

echo "Changedetection.io Webhook URLs:"
echo "=================================="

for county in "${COUNTIES[@]}"; do
  IFS=':' read -r name id <<< "$county"
  url="$DOMAIN/webhooks/trigger/$name"
  echo "County: $name (ID: $id)"
  echo "Watch URL: https://salesweb.civilview.com/Sales/SalesSearch?countyId=$id"
  echo "Webhook: $url"
  echo "Headers: {\"X-Webhook-Secret\": \"$WEBHOOK_SECRET\"}"
  echo ""
done
```

---

## Related Files

| File | Purpose |
|------|---------|
| `migrations/add_pg_cron_jobs.sql` | Database migration for pg_cron jobs |
| `webhook_server/app.py` | Main FastAPI application with webhook routes |
| `webhook_server/webhook_handlers.py` | Webhook endpoint handlers |
| `playwright_scraper.py` | Scraper that processes county triggers |
