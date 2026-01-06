# Start MCP services script (Cryptocurrency)
# Equivalent to main_crypto_step2.sh

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
$LogFile = Join-Path $LogsDir "ai-trader-crypto-step2.log"
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
Write-Log "=== AI-Trader Crypto Step 2 Script Started ==="

# Check UV installation
Test-UVInstalled
Write-Log "UV installation verified"

# Get the project root directory (parent of scripts/)
$ScriptDir = Split-Path -Parent $PSScriptRoot
$ProjectRoot = $ScriptDir

Set-Location $ProjectRoot

try {
    Write-Host "$(Get-Date -Format 'HH:mm:ss') 🔧 Starting MCP services..." -ForegroundColor Yellow
    Write-Log "Starting MCP services..."
    Set-Location agent_tools
    uv run python start_mcp_services.py
    Set-Location ..
    Write-Log "MCP services started successfully!" "SUCCESS"
} catch {
    Write-Host "$(Get-Date -Format 'HH:mm:ss') ❌ Error starting MCP services: $($_.Exception.Message)" -ForegroundColor Red
    Write-Log "Error starting MCP services: $($_.Exception.Message)" "ERROR"
    exit 1
} finally {
    Write-Log "=== AI-Trader Crypto Step 2 Script Finished ==="
}