# Setup script for Windows Task Scheduler
# Run this script as Administrator to create the scheduled task

$TaskName = "Nightly Foreclosure Scraper"
$ScriptPath = "C:\Projects\salesweb-crawl\run_scraper_nightly.bat"
$Description = "Runs incremental scrape of NJ foreclosure listings nightly at 2 AM"

# Check if script exists
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Batch script not found at: $ScriptPath"
    exit 1
}

# Remove existing task if it exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Removing existing scheduled task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the scheduled task trigger (run daily at 2 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At 2am

# Create the action
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ScriptPath`"" -WorkingDirectory "C:\Projects\salesweb-crawl"

# Create the principal (run with highest privileges)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest

# Create the settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the scheduled task
try {
    Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Principal $Principal -Settings $Settings -Description $Description
    Write-Host "✓ Scheduled task created successfully!" -ForegroundColor Green
    Write-Host "  Task Name: $TaskName"
    Write-Host "  Schedule: Daily at 2:00 AM"
    Write-Host "  Script: $ScriptPath"
    Write-Host ""
    Write-Host "To manually run the task:" -ForegroundColor Cyan
    Write-Host "  Start-ScheduledTask -TaskName `"$TaskName`""
    Write-Host ""
    Write-Host "To view task history:" -ForegroundColor Cyan
    Write-Host "  Get-ScheduledTaskInfo -TaskName `"$TaskName`""
} catch {
    Write-Error "Failed to create scheduled task: $_"
    exit 1
}

Write-Host ""
Write-Host "To disable the task:" -ForegroundColor Yellow
Write-Host "  Disable-ScheduledTask -TaskName `"$TaskName`""
Write-Host ""
Write-Host "To delete the task:" -ForegroundColor Yellow
Write-Host "  Unregister-ScheduledTask -TaskName `"$TaskName`" -Confirm:`$false"
