# Prepare data script
# Equivalent to main_step1.sh

param()

# Set error action preference
$ErrorActionPreference = "Stop"

# Advanced styling setup
$Colors = @{
    Success    = $PSStyle.Foreground.FromRGB(0x00AA00)  # Professional Green
    Warning    = $PSStyle.Foreground.FromRGB(0xFFAA00)  # Orange
    Error      = $PSStyle.Foreground.FromRGB(0xCC0000)  # Deep Red
    Info       = $PSStyle.Foreground.FromRGB(0x0088CC)  # Blue
    Accent     = $PSStyle.Foreground.FromRGB(0xAA00AA)  # Purple
    Header     = "$($PSStyle.Bold)$($PSStyle.Foreground.BrightCyan)$($PSStyle.Underline)"
    Reset      = $PSStyle.Reset
}

# Customize progress bar colors with RGB
$Host.PrivateData.ProgressBackgroundColor = "DarkGray"
$Host.PrivateData.ProgressForegroundColor = "Green"

# Enhanced progress bar styling
$PSStyle.Progress.Style = "$($PSStyle.Foreground.BrightMagenta)$($PSStyle.Bold)"

function Write-StyledMessage {
    param([string]$Message, [string]$Type = "Info", [switch]$NoTimestamp)
    
    $Style = switch ($Type) {
        "Success" { "$($Colors.Success)$($PSStyle.Bold)" }
        "Error"   { "$($Colors.Error)$($PSStyle.Bold)$($PSStyle.Blink)" }
        "Warning" { "$($Colors.Warning)$($PSStyle.Italic)" }
        "Header"  { $Colors.Header }
        "Accent"  { "$($Colors.Accent)$($PSStyle.Bold)" }
        default   { "$($Colors.Info)$($PSStyle.Bold)" }
    }
    
    $Timestamp = if (-not $NoTimestamp) { "$(Get-Date -Format 'HH:mm:ss') " } else { "" }
    Write-Host "$Timestamp$Style$Message$($Colors.Reset)"
}

# Logging setup
$LogsDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}
$LogFile = Join-Path $LogsDir "ai-trader-step1.log"
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
Write-Log "=== AI-Trader Step 1 Script Started ==="

# Check UV installation
Test-UVInstalled
Write-Log "UV installation verified"

# Get the project root directory (parent of scripts/)
$ScriptDir = Split-Path -Parent $PSScriptRoot
$ProjectRoot = $ScriptDir

Set-Location $ProjectRoot

try {
    Write-Progress -Activity "$($PSStyle.Bold)Data Preparation$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Fetching interdaily price data...$($PSStyle.Reset)" -PercentComplete 25
    Write-StyledMessage "📊 Fetching interdaily price data..." "Info"
    Write-Log "Starting interdaily price data fetch..."
    Set-Location data
    uv run python get_interdaily_price.py

    Write-Progress -Activity "$($PSStyle.Bold)Data Preparation$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Merging JSONL files...$($PSStyle.Reset)" -PercentComplete 75
    Write-StyledMessage "🔄 Merging data files..." "Info"
    Write-Log "Starting data file merging..."
    uv run python merge_jsonl.py
    Set-Location ..

    Write-Progress -Activity "$($PSStyle.Bold)Data Preparation$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Data preparation complete$($PSStyle.Reset)" -PercentComplete 100
    Write-StyledMessage "✅ Data preparation completed successfully!" "Success"
    Write-Log "Data preparation completed successfully!" "SUCCESS"
} catch {
    Write-Progress -Activity "$($PSStyle.Bold)Data Preparation$($PSStyle.Reset)" -Status "$($PSStyle.Blink)$($PSStyle.Foreground.Red)Error occurred$($PSStyle.Reset)" -PercentComplete 0 -Completed
    Write-StyledMessage "❌ Error in data preparation: $($_.Exception.Message)" "Error"
    Write-Log "Error in data preparation: $($_.Exception.Message)" "ERROR"
    exit 1
} finally {
    Write-Progress -Activity "$($PSStyle.Bold)Data Preparation$($PSStyle.Reset)" -Completed
    Write-Log "=== AI-Trader Step 1 Script Finished ==="
}