# Webhook Server for changedetection.io

FastAPI server that receives webhooks from changedetection.io when county listings change, and triggers incremental scrapes.

## Setup

### 1. Install Dependencies

```bash
pip install fastapi uvicorn
```

Or add to your virtual environment:

```bash
source venv/bin/activate
pip install fastapi uvicorn
```

### 2. Configure Environment Variables

```bash
export WEBHOOK_SECRET="your-secure-secret-here"
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-supabase-key"
```

### 3. Run the Server

```bash
# From project root
cd /path/to/salesweb-crawl

# Development
uvicorn webhook_server.app:app --reload --host 0.0.0.0 --port 8080

# Production
uvicorn webhook_server.app:app --host 0.0.0.0 --port 8080 --workers 1
```

**Note:** Use `--workers 1` to ensure per-county locking works correctly.

## changedetection.io Configuration

### Watch Setup

Create one watch per county with this naming convention:

```
CivilView | {CountyName}
```

Examples:
- `CivilView | Middlesex`
- `CivilView | Bergen`
- `CivilView | Essex`

### Webhook Configuration

In changedetection.io, configure the webhook:

**URL:** `https://your-server.com/webhooks/changedetection`

**Headers:**
```
Content-Type: application/json
X-Webhook-Secret: your-secure-secret-here
```

**Body Template (Jinja2):**
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

## API Endpoints

### `GET /`
Health check, returns running scrapes.

### `GET /health`
Simple health check for load balancers.

### `POST /webhooks/changedetection`
Main webhook endpoint for changedetection.io.

**Headers:**
- `X-Webhook-Secret`: Your configured secret

**Response Codes:**
- `200`: Scrape queued successfully
- `202`: Scrape already running for this county
- `400`: Invalid watch_title format
- `401`: Invalid webhook secret

### `GET /status`
Get current scraper status and running jobs.

### `POST /trigger/{county}`
Manually trigger a scrape for a specific county.

## Testing

### Simulate Webhook Locally

```bash
curl -X POST http://localhost:8080/webhooks/changedetection \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secure-secret-here" \
  -d '{
    "watch_title": "CivilView | Middlesex",
    "watch_url": "https://salesweb.civilview.com/?countyId=73",
    "diff_added": "New property at 123 Main St",
    "diff_removed": ""
  }'
```

### Check Status

```bash
curl http://localhost:8080/status
```

### Manual Trigger

```bash
curl -X POST http://localhost:8080/trigger/Middlesex \
  -H "X-Webhook-Secret: your-secure-secret-here"
```

## Concurrency

The server uses per-county locks to prevent overlapping browser sessions:

- If a scrape is already running for a county, new webhooks return `202 Accepted`
- The webhook is not retried; changedetection.io will send another on the next change
- This prevents resource exhaustion from rapid changes

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps

ENV WEBHOOK_SECRET=""
ENV SUPABASE_URL=""
ENV SUPABASE_KEY=""

EXPOSE 8080
CMD ["uvicorn", "webhook_server.app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Systemd Service

```ini
[Unit]
Description=Sheriff Sales Webhook Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/salesweb-crawl
Environment=WEBHOOK_SECRET=your-secret
Environment=SUPABASE_URL=https://your-project.supabase.co
Environment=SUPABASE_KEY=your-key
ExecStart=/opt/salesweb-crawl/venv/bin/uvicorn webhook_server.app:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

## Logs

The server logs to stdout:
- Webhook received events
- Scrape start/completion
- Errors and warnings

For production, consider piping to a log aggregator or file.
