# AI-Trader Main Launch Script
# Complete automation for Windows
# Equivalent to main.sh

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
$LogFile = Join-Path $LogsDir "ai-trader-main.log"
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
        Write-Host "   Or visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    }
}

# Start logging
Write-Log "=== AI-Trader Main Script Started ==="

# Check UV installation
Test-UVInstalled
Write-Log "UV installation verified"

# Get the project root directory (parent of scripts/)
$ScriptDir = Split-Path -Parent $PSScriptRoot
$ProjectRoot = $ScriptDir

Set-Location $ProjectRoot
Write-Host "📁 Project root: $ProjectRoot" -ForegroundColor Gray
Write-Log "Project root set to: $ProjectRoot"

Write-StyledMessage "🚀 Launching AI-Trader Environment" "Header" -NoTimestamp
Write-Log "Launching AI Trader Environment..." "INFO"

try {
    # Step 1: Data preparation
    Write-Progress -Activity "$($PSStyle.Bold)AI-Trader Setup$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Preparing market data...$($PSStyle.Reset)" -PercentComplete 10
    Write-StyledMessage "📊 Getting and merging price data..." "Info"
    Write-Log "Starting data preparation..."
    Set-Location data
    uv run python get_daily_price.py
    Write-Progress -Activity "$($PSStyle.Bold)AI-Trader Setup$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Merging data files...$($PSStyle.Reset)" -PercentComplete 30
    uv run python merge_jsonl.py
    Set-Location ..
    Write-Progress -Activity "$($PSStyle.Bold)AI-Trader Setup$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Data preparation complete$($PSStyle.Reset)" -PercentComplete 40
    Write-Log "Data preparation completed successfully"

    # Step 2: Start MCP services
    Write-Progress -Activity "$($PSStyle.Bold)AI-Trader Setup$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Starting MCP services...$($PSStyle.Reset)" -PercentComplete 50
    Write-StyledMessage "🔧 Starting MCP services..." "Accent"
    Write-Log "Starting MCP services..."
    Set-Location agent_tools
    # Start services in background
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "uv run python start_mcp_services.py" -WindowStyle Normal
    Set-Location ..
    Write-Log "MCP services started in background"

    # Waiting for MCP services to start
    Write-Progress -Activity "$($PSStyle.Bold)AI-Trader Setup$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Initializing services...$($PSStyle.Reset)" -PercentComplete 60
    Write-StyledMessage "⏳ Waiting for services to initialize (2 seconds)..." "Warning"
    Write-Log "Waiting for services to initialize..."
    Start-Sleep -Seconds 2
    Write-Progress -Activity "$($PSStyle.Bold)AI-Trader Setup$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Services initialized$($PSStyle.Reset)" -PercentComplete 70
    Write-Log "Services initialization wait completed"

    # Step 3: Run trading agent
    Write-Progress -Activity "$($PSStyle.Bold)AI-Trader Setup$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Running trading agent...$($PSStyle.Reset)" -PercentComplete 80
    Write-StyledMessage "🤖 Starting the main trading agent..." "Accent"
    Write-Log "Starting trading agent..."
    uv run python main.py configs/default_config.json
    Write-Progress -Activity "$($PSStyle.Bold)AI-Trader Setup$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Trading agent completed$($PSStyle.Reset)" -PercentComplete 90
    Write-Log "Trading agent execution completed"

    Write-StyledMessage "✅ AI-Trader execution completed!" "Success"
    Write-Log "AI-Trader execution completed successfully!" "SUCCESS"

    # Step 4: Start web UI
    Write-Progress -Activity "$($PSStyle.Bold)AI-Trader Setup$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Starting web interface...$($PSStyle.Reset)" -PercentComplete 95
    Write-StyledMessage "🔄 Starting web server..." "Info"
    Write-Log "Starting web server..."
    Set-Location docs
    uv run python -m http.server 8888
    Write-Progress -Activity "$($PSStyle.Bold)AI-Trader Setup$($PSStyle.Reset)" -Status "$($PSStyle.Italic)Web server started$($PSStyle.Reset)" -PercentComplete 100

    Write-StyledMessage "✅ Web server started successfully!" "Success"
    Write-Host "$($PSStyle.Background.BrightCyan)$($PSStyle.Foreground.Black)🌐 Access the web UI at: http://localhost:8888$($PSStyle.Reset)"
    Write-Log "Web server started on http://localhost:8888" "SUCCESS"

} catch {
    Write-Progress -Activity "$($PSStyle.Bold)AI-Trader Setup$($PSStyle.Reset)" -Status "$($PSStyle.Blink)$($PSStyle.Foreground.Red)Error occurred$($PSStyle.Reset)" -PercentComplete 0 -Completed
    Write-StyledMessage "❌ Error occurred: $($_.Exception.Message)" "Error"
    Write-Log "Critical error occurred: $($_.Exception.Message)" "ERROR"
    exit 1
} finally {
    Write-Progress -Activity "$($PSStyle.Bold)AI-Trader Setup$($PSStyle.Reset)" -Completed
    Write-Log "=== AI-Trader Main Script Finished ==="
}