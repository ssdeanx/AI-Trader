# Start MCP services script
# Equivalent to main_step2.sh

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
$LogFile = Join-Path $LogsDir "ai-trader-step2.log"
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
Write-Log "=== AI-Trader Step 2 Script Started ==="

# Check UV installation
Test-UVInstalled
Write-Log "UV installation verified"

# Get the project root directory (parent of scripts/)
$ScriptDir = Split-Path -Parent $PSScriptRoot
$ProjectRoot = $ScriptDir

Set-Location $ProjectRoot

try {
    Write-StyledMessage "🔧 Starting MCP services..." "Accent"
    Write-Log "Starting MCP services..."
    Set-Location agent_tools
    uv run python start_mcp_services.py
    Set-Location ..
    Write-StyledMessage "✅ MCP services started!" "Success"
    Write-Log "MCP services started successfully!" "SUCCESS"
} catch {
    Write-StyledMessage "❌ Error starting MCP services: $($_.Exception.Message)" "Error"
    Write-Log "Error starting MCP services: $($_.Exception.Message)" "ERROR"
    exit 1
} finally {
    Write-Log "=== AI-Trader Step 2 Script Finished ==="
}