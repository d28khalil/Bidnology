@echo off
REM Nightly Foreclosure Scraper
REM Runs incremental scrape for all NJ counties
REM Log output to backend.log with timestamp
REM Sends Discord report if DISCORD_WEBHOOK_URL is set

echo.
echo ============================================
echo Starting Nightly Foreclosure Scraper
echo Date: %date%
echo Time: %time%
echo ============================================
echo.

cd /d C:\Projects\salesweb-crawl

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist venv_win\Scripts\activate.bat (
    call venv_win\Scripts\activate.bat
)

REM Run the scraper with incremental mode
REM Discord webhook URL is read from DISCORD_WEBHOOK_URL environment variable
py playwright_scraper.py --incremental --discord-webhook %DISCORD_WEBHOOK_URL% >> backend.log 2>&1

echo.
echo ============================================
echo Scraper completed at %time%
echo ============================================
echo.
