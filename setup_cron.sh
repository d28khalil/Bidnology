#!/bin/bash
# Setup script for Linux cron job
# For running on Linux servers or VPS

# Directory where scraper is located
SCRAPER_DIR="/path/to/salesweb-crawl"
PYTHON_CMD="python3"
LOG_FILE="$SCRAPER_DIR/backend.log"

# Create the cron entry
# Runs daily at 2:00 AM
CRON_ENTRY="0 2 * * * cd $SCRAPER_DIR && $PYTHON_CMD playwright_scraper.py --incremental >> $LOG_FILE 2>&1"

echo "================================================"
echo "Setting up Nightly Foreclosure Scraper Cron Job"
echo "================================================"
echo ""
echo "Cron entry to be added:"
echo "$CRON_ENTRY"
echo ""

# Check if scraper directory exists
if [ ! -d "$SCRAPER_DIR" ]; then
    echo "⚠️  Warning: Scraper directory not found: $SCRAPER_DIR"
    echo "Please edit SCRAPER_DIR in this script to match your actual path."
    exit 1
fi

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null

# Add the cron job (avoid duplicates)
if crontab -l 2>/dev/null | grep -q "playwright_scraper.py"; then
    echo "⚠️  Cron job for playwright_scraper.py already exists."
    echo "Skipping installation to avoid duplicates."
    echo ""
    echo "To view existing cron jobs:"
    echo "  crontab -l"
    echo ""
    echo "To edit cron jobs:"
    echo "  crontab -e"
else
    # Add the new cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✓ Cron job added successfully!"
    echo ""
    echo "Cron job details:"
    echo "  Schedule: Daily at 2:00 AM"
    echo "  Command: cd $SCRAPER_DIR && $PYTHON_CMD playwright_scraper.py --incremental"
    echo "  Log file: $LOG_FILE"
    echo ""
    echo "To view all cron jobs:"
    echo "  crontab -l"
    echo ""
    echo "To edit cron jobs:"
    echo "  crontab -e"
    echo ""
    echo "To remove the cron job:"
    echo "  crontab -e"
    echo "  Then delete the line containing 'playwright_scraper.py'"
fi

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
