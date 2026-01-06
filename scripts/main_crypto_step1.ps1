# Cryptocurrency data preparation script
# Equivalent to main_crypto_step1.sh

param()

# Set error action preference
$ErrorActionPreference = "Stop"

# Advanced styling setup
$Host.PrivateData.ProgressBackgroundColor = "DarkGray"
$Host.PrivateData.ProgressForegroundColor = "Green"

# Custom color palette
$Colors = @{
    Success    = $PSStyle.Foreground.FromRGB(0x00AA00)  # Professional Green
    Warning    = $PSStyle.Foreground.FromRGB(0xFFAA00)  # Orange
    Error      = $PSStyle.Foreground.FromRGB(0xCC0000)  # Deep Red
    Info       = $PSStyle.Foreground.FromRGB(0x0088CC)  # Blue
    Accent     = $PSStyle.Foreground.FromRGB(0xAA00AA)  # Purple
    Header     = "$($PSStyle.Bold)$($PSStyle.Foreground.BrightCyan)$($PSStyle.Underline)"
}

# Logging setup
$LogsDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}
$LogFile = Join-Path $LogsDir "ai-trader-crypto-step1.log"
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

function Write-StyledMessage {
    param([string]$Message, [string]$Type = "Info")
    
    $Style = switch ($Type) {
        "Success" { "$($PSStyle.Foreground.BrightGreen)$($PSStyle.Bold)" }
        "Error"   { "$($PSStyle.Foreground.BrightRed)$($PSStyle.Blink)" }
        "Warning" { "$($PSStyle.Foreground.BrightYellow)$($PSStyle.Underline)" }
        "Header"  { "$($PSStyle.Bold)$($PSStyle.Foreground.BrightMagenta)$($PSStyle.Underline)" }
        default   { "$($PSStyle.Foreground.Cyan)" }
    }
    
    Write-Host "$Style$Message$($PSStyle.Reset)"
}

function Test-UVInstalled {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-StyledMessage "UV not found! Please install UV first:" "Error"
        Write-Host "   curl -LsSf https://astral.sh/uv/install.ps1 | powershell"
        exit 1
    }
}

# Start logging
Write-Log "=== AI-Trader Crypto Step 1 Script Started ==="

# Check UV installation
Test-UVInstalled
Write-Log "UV installation verified"

# Get the project root directory (parent of scripts/)
$ScriptDir = Split-Path -Parent $PSScriptRoot
$ProjectRoot = $ScriptDir

Set-Location $ProjectRoot

try {
    Write-StyledMessage "🪙 Starting Cryptocurrency Data Preparation" "Header"
    
    # Ensure data/crypto exists and enter the directory
    New-Item -ItemType Directory -Force -Path "data/crypto" | Out-Null
    Set-Location "data/crypto"
    Write-Log "Entered data/crypto directory"

    # Enhanced progress with styled text
    Write-Progress -Activity "$($PSStyle.Bold)Cryptocurrency Data Preparation$($PSStyle.Reset)" `
                   -Status "$($PSStyle.Italic)$($PSStyle.Foreground.BrightYellow)Fetching data...$($PSStyle.Reset)" `
                   -PercentComplete 25
    Write-StyledMessage "📊 Fetching cryptocurrency data..." "Info"
    Write-Log "Starting cryptocurrency data fetch..."
    uv run python get_daily_price_crypto.py

    Write-Progress -Activity "$($PSStyle.Bold)Cryptocurrency Data Preparation$($PSStyle.Reset)" `
                   -Status "$($PSStyle.Italic)$($PSStyle.Foreground.BrightYellow)Merging data...$($PSStyle.Reset)" `
                   -PercentComplete 75
    Write-StyledMessage "🔄 Merging cryptocurrency data..." "Info"
    Write-Log "Starting cryptocurrency data merging..."
    uv run python merge_crypto_jsonl.py

    Set-Location ../..
    Write-Progress -Activity "$($PSStyle.Bold)Cryptocurrency Data Preparation$($PSStyle.Reset)" `
                   -Status "$($PSStyle.Foreground.BrightGreen)Complete!$($PSStyle.Reset)" `
                   -PercentComplete 100
    Write-StyledMessage "✅ Cryptocurrency data preparation completed successfully!" "Success"
    Write-Log "Cryptocurrency data preparation completed successfully!" "SUCCESS"
} catch {
    Write-Progress -Activity "$($PSStyle.Bold)Cryptocurrency Data Preparation$($PSStyle.Reset)" `
                   -Status "$($PSStyle.Foreground.BrightRed)Error occurred!$($PSStyle.Reset)" `
                   -PercentComplete 0 -Completed
    Write-StyledMessage "❌ Error in cryptocurrency data preparation: $($_.Exception.Message)" "Error"
    Write-Log "Error in cryptocurrency data preparation: $($_.Exception.Message)" "ERROR"
    exit 1
} finally {
    Write-Progress -Activity "$($PSStyle.Bold)Cryptocurrency Data Preparation$($PSStyle.Reset)" -Completed
    Write-Log "=== AI-Trader Crypto Step 1 Script Finished ==="
}