# Coolify Deployment Guide

## Quick Start

### 1. Push to Git Repository

Make sure your code is pushed to GitHub/GitLab:

```bash
git add Dockerfile docker-compose.yml .dockerignore
git commit -m "Add Docker support for Coolify deployment"
git push origin main
```

### 2. Create New Resource in Coolify

1. Go to your Coolify dashboard
2. Click **"+ Add New Resource"**
3. Select **"Docker"** → **"Dockerfile"**
4. Connect your Git repository

### 3. Configure Environment Variables

In Coolify's **Environment Variables** section, add:

| Variable | Value | Required |
|----------|-------|----------|
| `WEBHOOK_SECRET` | Your secure secret string | Yes |
| `SUPABASE_URL` | `https://your-project.supabase.co` | Yes |
| `SUPABASE_KEY` | Your Supabase anon/service key | Yes |

### 4. Configure Port

- **Exposed Port:** `8080`
- Coolify will auto-detect from the Dockerfile

### 5. Configure Domain (Optional)

If you want a custom domain:
1. Go to **Domains** tab
2. Add your domain: `webhook.yourdomain.com`
3. Enable **HTTPS** (recommended)

### 6. Deploy

Click **Deploy** and wait for the build to complete.

---

## Coolify Settings

### Recommended Configuration

| Setting | Value |
|---------|-------|
| Build Pack | Dockerfile |
| Dockerfile Location | `/Dockerfile` |
| Health Check Path | `/health` |
| Port | 8080 |

### Resource Limits

For stable Playwright operation:

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 0.5 cores | 2 cores |
| Memory | 512 MB | 2 GB |

---

## Webhook URL for changedetection.io

After deployment, your webhook URL will be:

```
https://your-coolify-domain.com/webhooks/changedetection
```

### changedetection.io Notification Setup

**Notification URL (Apprise format):**
```
jsons://your-coolify-domain.com/webhooks/changedetection?+X-Webhook-Secret=your-secret
```

**Or for direct webhook (if available):**
```
URL: https://your-coolify-domain.com/webhooks/changedetection
Headers:
  Content-Type: application/json
  X-Webhook-Secret: your-secret
```

---

## Verify Deployment

### Check Health

```bash
curl https://your-coolify-domain.com/health
# Expected: {"status":"ok"}
```

### Check Status

```bash
curl https://your-coolify-domain.com/status
# Expected: {"running_scrapes":{},"locked_counties":[]}
```

### Test Webhook

```bash
curl -X POST https://your-coolify-domain.com/webhooks/changedetection \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{"watch_title": "CivilView | Middlesex", "watch_url": "https://salesweb.civilview.com"}'
```

---

## Troubleshooting

### Container won't start

1. Check Coolify logs for errors
2. Verify all environment variables are set
3. Ensure Supabase credentials are correct

### Playwright errors

- Increase memory limit to 2GB+
- Check that Chromium dependencies installed correctly

### Webhook not receiving

1. Verify domain is accessible publicly
2. Check `X-Webhook-Secret` header matches
3. Test with curl from external network

### Scraper timeouts

- Default timeout is 10 minutes
- For large counties, monitor `/status` endpoint
- Only one scrape runs per county at a time

---

## Logs

View logs in Coolify dashboard or:

```bash
# If using Coolify CLI
coolify logs sheriff-sales-webhook
```

Key log messages:
- `Sheriff Sales Webhook Server starting...` - Server started
- `Scrape completed for {county}: True` - Successful scrape
- `Scrape already in progress for {county}` - Duplicate request blocked
