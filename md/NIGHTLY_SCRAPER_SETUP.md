# Nightly Scraper Setup Guide

Automated nightly scraping of NJ foreclosure listings with optional Discord reports.

---

## Discord Reports (Optional)

Get a nice summary report in Discord after each nightly scrape!

### Setup Discord Webhook:

1. **Create Discord Webhook**
   - Open your Discord server settings
   - Go to **Integrations** → **Webhooks** → **New Webhook**
   - Copy the webhook URL (format: `https://discord.com/api/webhooks/...`)

2. **Set Environment Variable**

   **Windows (PowerShell):**
   ```powershell
   # Set for current session only
   $env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."

   # Set permanently (system-wide)
   setx DISCORD_WEBHOOK_URL "https://discord.com/api/webhooks/..."
   ```

   **Linux:**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

   # Then reload
   source ~/.bashrc
   ```

3. **Test Discord Notification**
   ```bash
   python discord_notifier.py test
   ```

You'll receive a test message like this:
```
🧪 Scraper Test Message
Status: ✅ Connected
Time: 2025-01-16 14:30:00
```

### Report Example:

After each scrape, you'll get a report like:
```
📊 Nightly Foreclosure Scraper Report

Mode: Incremental
Duration: 45.2 minutes

📈 Results:
✅ New: 16
🔄 Updated: 165
⏭️ Skipped: 300
📦 Total Processed: 481

🏠 NJ Counties:
**Bergen:** +3 new, 45 updated
**Camden:** +5 new, 50 updated
**Essex:** +8 new, 70 updated
...
```

---

## Option 1: Windows Task Scheduler (Recommended for Windows)

### Quick Setup:

1. **Open PowerShell as Administrator**
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. **Navigate to project directory**
   ```powershell
   cd C:\Projects\salesweb-crawl
   ```

3. **Run the setup script**
   ```powershell
   .\setup_scheduled_task.ps1
   ```

4. **Verify the task was created**
   ```powershell
   Get-ScheduledTask -TaskName "Nightly Foreclosure Scraper"
   ```

### Manual Task Scheduler Setup (Alternative):

1. Open Task Scheduler (`taskschd.msc`)
2. Click "Create Basic Task"
3. Name: `Nightly Foreclosure Scraper`
4. Trigger: `Daily` at `2:00 AM`
5. Action: `Start a program`
   - Program: `C:\Projects\salesweb-crawl\run_scraper_nightly.bat`
6. Finish

### Task Management:

```powershell
# View task history
Get-ScheduledTaskInfo -TaskName "Nightly Foreclosure Scraper"

# Manually run the task
Start-ScheduledTask -TaskName "Nightly Foreclosure Scraper"

# Disable the task
Disable-ScheduledTask -TaskName "Nightly Foreclosure Scraper"

# Enable the task
Enable-ScheduledTask -TaskName "Nightly Foreclosure Scraper"

# Delete the task
Unregister-ScheduledTask -TaskName "Nightly Foreclosure Scraper" -Confirm:$false
```

---

## Option 2: Linux Cron (For Linux Servers)

### Setup:

1. **Edit the setup script** with your actual path:
   ```bash
   nano setup_cron.sh
   # Change SCRAPER_DIR="/path/to/salesweb-crawl" to your actual path
   ```

2. **Make script executable and run**:
   ```bash
   chmod +x setup_cron.sh
   ./setup_cron.sh
   ```

### Manual Cron Setup (Alternative):

```bash
# Open crontab editor
crontab -e

# Add this line (runs daily at 2 AM):
# Make sure DISCORD_WEBHOOK_URL is set in your environment first
0 2 * * * cd /path/to/salesweb-crawl && python3 playwright_scraper.py --incremental --discord-webhook $DISCORD_WEBHOOK_URL >> backend.log 2>&1
```

---

## Option 3: Coolify Scheduled Task (For Coolify Deployments)

### Setup in Coolify:

1. **Go to your service** in Coolify dashboard
2. **Add Scheduled Task** with:

| Field | Value |
|-------|-------|
| **Name** | `Nightly Foreclosure Scraper` |
| **Schedule** | `0 2 * * *` (daily at 2 AM) |
| **Command** | `python playwright_scraper.py --incremental --discord-webhook $DISCORD_WEBHOOK_URL` |

3. **Add Environment Variable** in your service:

| Variable | Value |
|----------|-------|
| `DISCORD_WEBHOOK_URL` | Your Discord webhook URL |

4. **Save** and enable the scheduled task

The scraper will run nightly and send a Discord report when complete!

---

## Configuration Options

### Change Run Time:

**Windows (PowerShell):**
```powershell
# Unregister and recreate with different time
Unregister-ScheduledTask -TaskName "Nightly Foreclosure Scraper" -Confirm:$false

# Edit setup_scheduled_task.ps1, line with:
$Trigger = New-ScheduledTaskTrigger -Daily -At 2am
# Change "2am" to desired time (e.g., "3am", "1:30am")
```

**Linux:**
```bash
crontab -e
# Change "0 2" to desired hour (0-23)
# Format: minute hour * * *
```

### Change Scraper Options:

Edit `run_scraper_nightly.bat` (Windows) or crontab entry (Linux):

| Option | Description |
|--------|-------------|
| `--incremental` | Only scrape new/changed (default) |
| `--use-webhook` | Send to webhook server (enrichment) |
| `--auto-enrich` | Auto-trigger Zillow enrichment |
| `--counties Atlantic Bergen` | Specific counties only |

**Example with webhook:**
```bash
py playwright_scraper.py --incremental --use-webhook --auto-enrich
```

---

## Monitoring

### Check Logs:

```bash
# Windows (PowerShell)
Get-Content C:\Projects\salesweb-crawl\backend.log -Tail 50

# Linux
tail -50 /path/to/salesweb-crawl/backend.log
```

### Success Indicators:
- ✅ Properties updated (not just "new")
- ✅ No screenshot fallback errors
- ✅ All 16 NJ counties processed

---

## Troubleshooting

### Issue: Task doesn't run

**Windows:**
1. Check Task Scheduler History
2. Ensure Python is in PATH
3. Test manually: `.\run_scraper_nightly.bat`

**Linux:**
```bash
# Check cron service
sudo systemctl status cron

# Check cron logs
grep CRON /var/log/syslog | tail -20
```

### Issue: Scraper fails

1. Check environment variables are set:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `OPENAI_API_KEY`

2. Test scraper manually first:
   ```bash
   py playwright_scraper.py --incremental
   ```

---

## Files Created:

| File | Purpose |
|------|---------|
| `run_scraper_nightly.bat` | Windows batch script |
| `setup_scheduled_task.ps1` | PowerShell setup script |
| `setup_cron.sh` | Linux cron setup script |
| `NIGHTLY_SCRAPER_SETUP.md` | This documentation |

---

## Recommended Schedule:

| Time | Reason |
|------|--------|
| **2:00 AM** | Off-peak hours, most listings updated by then |
| **3:00 AM** | Alternative if 2 AM conflicts with other tasks |
| **1:00 AM** | Earlier option for early birds |

---

*For questions, check FULL_SCRAPE_PROCESS_PROTOCOL.md for scraper details.*
