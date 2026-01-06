# Regenerate Frontend Cache
# Equivalent to regenerate_cache.sh
# Run this script after updating trading data to regenerate the pre-computed cache files

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
$LogFile = Join-Path $LogsDir "ai-trader-regenerate-cache.log"
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
Write-Log "=== AI-Trader Regenerate Cache Script Started ==="

# Check UV installation
Test-UVInstalled
Write-Log "UV installation verified"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Regenerating Frontend Cache" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $PSScriptRoot
$ProjectRoot = $ScriptDir

Set-Location $ProjectRoot
Write-Log "Project root set to: $ProjectRoot"

try {
    # Run the cache generation script
    Write-Host "$(Get-Date -Format 'HH:mm:ss') 🔄 Running cache generation script..." -ForegroundColor Yellow
    Write-Log "Starting cache generation..."
    uv run python scripts/precompute_frontend_cache.py
    Write-Log "Cache generation completed successfully!" "SUCCESS"

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Cache regeneration complete!" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Generated files:" -ForegroundColor Yellow
    Write-Host "  - docs/data/us_cache.json"
    Write-Host "  - docs/data/cn_cache.json"
    Write-Host ""
    Write-Host "These files will be automatically used by the frontend for faster loading." -ForegroundColor Green
    Write-Host "Commit these files to your repository for GitHub Pages deployment." -ForegroundColor Green
} catch {
    Write-Host "$(Get-Date -Format 'HH:mm:ss') ❌ Error regenerating cache: $($_.Exception.Message)" -ForegroundColor Red
    Write-Log "Error regenerating cache: $($_.Exception.Message)" "ERROR"
    exit 1
} finally {
    Write-Log "=== AI-Trader Regenerate Cache Script Finished ==="
}