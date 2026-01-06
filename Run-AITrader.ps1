# AI-Trader Master Script
# Complete automation for Windows with UV support
# Run this file with: .\Run-AITrader.ps1

param(
    [ValidateSet('all', 'data', 'services', 'agent', 'ui', 'cache', 'help')]
    [string]$Action = 'help',
    
    [string]$Config = 'configs/default_config.json',
    
    [ValidateSet('us', 'astock', 'crypto')]
    [string]$Market = 'us',
    
    [ValidateSet('daily', 'hourly')]
    [string]$Frequency = 'daily',
    
    [switch]$SkipData,
    [switch]$SkipServices,
    [switch]$NoWait
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-ColorOutput "═══════════════════════════════════════════════════" "Cyan"
    Write-ColorOutput "  $Title" "Cyan"
    Write-ColorOutput "═══════════════════════════════════════════════════" "Cyan"
    Write-Host ""
}

function Show-Help {
    Write-Section "AI-Trader Master Script - Help"
    
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  .\Run-AITrader.ps1 -Action <action> [options]" -ForegroundColor White
    Write-Host ""
    
    Write-Host "ACTIONS:" -ForegroundColor Yellow
    Write-Host "  all       - Run complete pipeline (data → services → agent)" -ForegroundColor Green
    Write-Host "  data      - Fetch and prepare market data" -ForegroundColor Green
    Write-Host "  services  - Start MCP services only" -ForegroundColor Green
    Write-Host "  agent     - Run trading agent (requires services)" -ForegroundColor Green
    Write-Host "  ui        - Start web UI server" -ForegroundColor Green
    Write-Host "  cache     - Regenerate frontend cache" -ForegroundColor Green
    Write-Host "  help      - Show this help message" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "OPTIONS:" -ForegroundColor Yellow
    Write-Host "  -Config <path>     Config file path (default: configs/default_config.json)" -ForegroundColor White
    Write-Host "  -Market <type>     Market type: us, astock, crypto (default: us)" -ForegroundColor White
    Write-Host "  -Frequency <freq>  Trading frequency: daily, hourly (default: daily)" -ForegroundColor White
    Write-Host "  -SkipData          Skip data preparation" -ForegroundColor White
    Write-Host "  -SkipServices      Skip starting MCP services" -ForegroundColor White
    Write-Host "  -NoWait            Don't wait after starting services" -ForegroundColor White
    Write-Host ""
    
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  # Complete workflow with default settings" -ForegroundColor Cyan
    Write-Host "  .\Run-AITrader.ps1 -Action all" -ForegroundColor White
    Write-Host ""
    Write-Host "  # Run only data preparation" -ForegroundColor Cyan
    Write-Host "  .\Run-AITrader.ps1 -Action data -Market astock" -ForegroundColor White
    Write-Host ""
    Write-Host "  # Start services and run agent (skip data)" -ForegroundColor Cyan
    Write-Host "  .\Run-AITrader.ps1 -Action all -SkipData" -ForegroundColor White
    Write-Host ""
    Write-Host "  # Start web UI" -ForegroundColor Cyan
    Write-Host "  .\Run-AITrader.ps1 -Action ui" -ForegroundColor White
    Write-Host ""
    Write-Host "  # Regenerate frontend cache" -ForegroundColor Cyan
    Write-Host "  .\Run-AITrader.ps1 -Action cache" -ForegroundColor White
    Write-Host ""
    
    Write-Host "MARKET-SPECIFIC CONFIGS:" -ForegroundColor Yellow
    Write-Host "  US Stocks:    configs/default_config.json" -ForegroundColor White
    Write-Host "  A-Shares:     configs/astock_config.json" -ForegroundColor White
    Write-Host "  Crypto:       configs/default_crypto_config.json" -ForegroundColor White
    Write-Host ""
}

function Test-UVInstalled {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-ColorOutput "❌ UV not found! Please install UV first:" "Red"
        Write-Host "   curl -LsSf https://astral.sh/uv/install.ps1 | powershell"
        Write-Host "   Or visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    }
}

function Invoke-DataPreparation {
    param([string]$MarketType)
    
    Write-Section "📊 Data Preparation - $MarketType Market"
    
    switch ($MarketType) {
        'us' {
            Write-ColorOutput "Fetching US stock data..." "Yellow"
            Set-Location data
            uv run python get_daily_price.py
            uv run python merge_jsonl.py
            Set-Location ..
        }
        'astock' {
            Write-ColorOutput "Fetching A-share data..." "Yellow"
            Set-Location data/A_stock
            
            # Choose data source based on frequency
            if ($Frequency -eq 'hourly') {
                uv run python get_interdaily_price_astock.py
                uv run python merge_jsonl_hourly.py
            } else {
                uv run python get_daily_price_tushare.py
                uv run python merge_jsonl_tushare.py
            }
            Set-Location ../..
        }
        'crypto' {
            Write-ColorOutput "Fetching cryptocurrency data..." "Yellow"
            Set-Location data/crypto
            uv run python get_daily_price_crypto.py
            uv run python merge_crypto_jsonl.py
            Set-Location ../..
        }
    }
    
    Write-ColorOutput "✅ Data preparation complete!" "Green"
}

function Start-MCPServices {
    Write-Section "🔧 Starting MCP Services"
    
    Set-Location agent_tools
    
    Write-ColorOutput "Launching MCP services in background..." "Yellow"
    
    # Start services in background
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "uv run python start_mcp_services.py" -WindowStyle Normal
    
    Set-Location ..
    
    if (-not $NoWait) {
        Write-ColorOutput "⏳ Waiting for services to initialize (5 seconds)..." "Yellow"
        Start-Sleep -Seconds 5
    }
    
    Write-ColorOutput "✅ MCP services started!" "Green"
    Write-ColorOutput "   Services running on ports: 8000-8007" "Gray"
}

function Invoke-TradingAgent {
    param([string]$ConfigPath)
    
    Write-Section "🤖 Running Trading Agent"
    
    if (-not (Test-Path $ConfigPath)) {
        Write-ColorOutput "❌ Config file not found: $ConfigPath" "Red"
        Write-Host "Available configs:"
        Get-ChildItem configs/*.json | ForEach-Object { Write-Host "  - $($_.Name)" }
        exit 1
    }
    
    Write-ColorOutput "Using config: $ConfigPath" "Yellow"
    Write-Host ""
    
    uv run python main.py $ConfigPath
    
    Write-ColorOutput "✅ Trading agent completed!" "Green"
}

function Start-WebUI {
    Write-Section "🌐 Starting Web UI"
    
    Set-Location docs
    
    Write-ColorOutput "Web UI will be available at:" "Green"
    Write-ColorOutput "  http://localhost:8888" "Cyan"
    Write-Host ""
    Write-ColorOutput "Press Ctrl+C to stop the server" "Yellow"
    Write-Host ""
    
    uv run python -m http.server 8888
    
    Set-Location ..
}

function Invoke-CacheRegeneration {
    Write-Section "🔄 Regenerating Frontend Cache"
    
    Write-ColorOutput "Generating cache files for all markets..." "Yellow"
    
    uv run python scripts/precompute_frontend_cache.py
    
    Write-Host ""
    Write-ColorOutput "✅ Cache regeneration complete!" "Green"
    Write-Host ""
    Write-Host "Generated files:" -ForegroundColor Yellow
    Write-Host "  - docs/data/us_cache.json"
    Write-Host "  - docs/data/cn_cache.json"
    Write-Host "  - docs/data/cn_hour_cache.json"
    Write-Host ""
    Write-ColorOutput "Frontend will now load much faster!" "Green"
}

# Main script logic
Write-Host ""
Write-ColorOutput "╔═══════════════════════════════════════════════════╗" "Cyan"
Write-ColorOutput "║          AI-Trader Automation Script              ║" "Cyan"
Write-ColorOutput "║              Windows + UV Edition                 ║" "Cyan"
Write-ColorOutput "╚═══════════════════════════════════════════════════╝" "Cyan"
Write-Host ""

# Check UV installation
Test-UVInstalled

# Get project root (script directory)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

Set-Location $ProjectRoot
Write-ColorOutput "📁 Project root: $ProjectRoot" "Gray"

# Execute requested action
try {
    switch ($Action) {
        'help' {
            Show-Help
        }
        
        'all' {
            if (-not $SkipData) {
                Invoke-DataPreparation -MarketType $Market
            } else {
                Write-ColorOutput "⏭️  Skipping data preparation" "Yellow"
            }
            
            if (-not $SkipServices) {
                Start-MCPServices
            } else {
                Write-ColorOutput "⏭️  Skipping MCP services" "Yellow"
            }
            
            Invoke-TradingAgent -ConfigPath $Config
            
            Invoke-CacheRegeneration
            
            Write-Section "🌐 Starting Web UI"
            Write-ColorOutput "Launching web UI in background..." "Yellow"
            Write-ColorOutput "Web UI will be available at: http://localhost:8888" "Green"
            
            # Start web UI in background
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location docs; uv run python -m http.server 8888" -WindowStyle Normal
            
            Write-Section "✅ Complete Workflow Finished!"
            Write-ColorOutput "🎉 AI-Trader is now running!" "Green"
            Write-ColorOutput "📊 View results at: http://localhost:8888" "Cyan"
        }
        
        'data' {
            Invoke-DataPreparation -MarketType $Market
        }
        
        'services' {
            Start-MCPServices
        }
        
        'agent' {
            Invoke-TradingAgent -ConfigPath $Config
        }
        
        'ui' {
            Start-WebUI
        }
        
        'cache' {
            Invoke-CacheRegeneration
        }
        
        default {
            Write-ColorOutput "❌ Unknown action: $Action" "Red"
            Write-Host "Run '.\Run-AITrader.ps1 -Action help' for usage information"
            exit 1
        }
    }
}
catch {
    Write-ColorOutput "❌ Error occurred: $($_.Exception.Message)" "Red"
    Write-Host $_.ScriptStackTrace
    exit 1
}

Write-Host ""
Write-ColorOutput "═══════════════════════════════════════════════════" "Cyan"
Write-ColorOutput "  Script completed successfully!" "Green"
Write-ColorOutput "═══════════════════════════════════════════════════" "Cyan"
Write-Host ""
