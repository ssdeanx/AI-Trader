# A-share data preparation script
# Equivalent to main_a_stock_step1.sh

param()

# Set error action preference
$ErrorActionPreference = "Stop"

# Customize progress bar colors
$Host.PrivateData.ProgressBackgroundColor = "DarkGray"
$Host.PrivateData.ProgressForegroundColor = "Green"

# Logging setup
$LogsDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}
$LogFile = Join-Path $LogsDir "ai-trader-astock-step1.log"
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

function Test-UVInstalled {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Log "UV not found! Please install UV first:" "ERROR"
        Write-Host "   curl -LsSf https://astral.sh/uv/install.ps1 | powershell"
        exit 1
    }
}

# Start logging
Write-Log "=== AI-Trader A-Share Step 1 Script Started ==="

# Check UV installation
Test-UVInstalled
Write-Log "UV installation verified"

# Get the project root directory (parent of scripts/)
$ScriptDir = Split-Path -Parent $PSScriptRoot
$ProjectRoot = $ScriptDir

Set-Location $ProjectRoot

try {
    Write-Progress -Activity "A-Share Data Preparation" -Status "Fetching daily price data..." -PercentComplete 25
    Write-Host "$(Get-Date -Format 'HH:mm:ss') 📊 Fetching A-share daily price data..." -ForegroundColor Yellow
    Write-Log "Starting A-share daily price data fetch..."
    Set-Location data/A_stock

    # for tushare (matching Run-AITrader.ps1)
    uv run python get_daily_price_tushare.py

    Write-Progress -Activity "A-Share Data Preparation" -Status "Merging data files..." -PercentComplete 75
    Write-Host "$(Get-Date -Format 'HH:mm:ss') 🔄 Merging A-share data files..." -ForegroundColor Yellow
    Write-Log "Starting A-share data file merging..."
    uv run python merge_jsonl_tushare.py

    Set-Location ../..

    Write-Progress -Activity "A-Share Data Preparation" -Status "A-share data preparation complete" -PercentComplete 100
    Write-Host "$(Get-Date -Format 'HH:mm:ss') ✅ A-share data preparation completed successfully!" -ForegroundColor Green
    Write-Log "A-share data preparation completed successfully!" "SUCCESS"
} catch {
    Write-Progress -Activity "A-Share Data Preparation" -Status "Error occurred" -PercentComplete 0 -Completed
    Write-Host "$(Get-Date -Format 'HH:mm:ss') ❌ Error in A-share data preparation: $($_.Exception.Message)" -ForegroundColor Red
    Write-Log "Error in A-share data preparation: $($_.Exception.Message)" "ERROR"
    exit 1
} finally {
    Write-Progress -Activity "A-Share Data Preparation" -Completed
    Write-Log "=== AI-Trader A-Share Step 1 Script Finished ==="
}