# Quick Start Guide for Windows

## Prerequisites

1. **Python 3.12+**: Install from [python.org](https://python.org)
2. **UV Package Manager**: Install with:

   ```powershell
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

## One-Time Setup

### 1. Install Dependencies

```powershell
# Navigate to project root
cd AI-Trader-main

# Install with UV (automatically creates venv and installs dependencies)
uv sync
```

### 2. Configure API Keys

Copy the example environment file and fill in your API keys:

```powershell
# Copy example to .env
Copy-Item .env.example .env

# Edit .env with your favorite editor
notepad .env
```

**Required API Keys:**

- **Google Gemini**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **OpenRouter** (optional): Get from [OpenRouter Keys](https://openrouter.ai/keys)
- **Alpha Vantage**: Get from [Alpha Vantage](https://www.alphavantage.co/support/#api-key)

**Example .env configuration for Gemini:**

```env
GOOGLE_API_KEY=your_google_api_key_here
ALPHAADVANTAGE_API_KEY=your_alphavantage_key
```

**Example .env configuration for OpenRouter:**

```env
OPENAI_API_KEY=your_openrouter_key_here
OPENAI_API_BASE=https://openrouter.ai/api/v1
ALPHAADVANTAGE_API_KEY=your_alphavantage_key
```

### 3. Activate Virtual Environment (Optional)

UV automatically manages the virtual environment, but if you want to activate it manually:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Running AI-Trader

### Quick Start - Complete Workflow

Run everything with one command:

```powershell
# Complete workflow (data → services → agent)
.\Run-AITrader.ps1 -Action all
```

This will:

1. ✅ Fetch and prepare market data
2. ✅ Start MCP services (7 microservices)
3. ✅ Run trading agent with default config
4. ✅ Generate trading decisions

### Individual Commands

#### Fetch Market Data Only

```powershell
# US stocks
.\Run-AITrader.ps1 -Action data -Market us

# Chinese A-shares (daily)
.\Run-AITrader.ps1 -Action data -Market astock

# Cryptocurrencies
.\Run-AITrader.ps1 -Action data -Market crypto
```

#### Start Services Only

```powershell
.\Run-AITrader.ps1 -Action services
```

This starts 7 MCP services:

- Math (Port 8000)
- Search (Port 8001)
- Trade (Port 8002)
- Price (Port 8003)
- Crypto (Port 8005)
- Sentiment Analysis (Port 8006)
- Technical Indicators (Port 8007)

#### Run Trading Agent

```powershell
# With default config
.\Run-AITrader.ps1 -Action agent

# With Gemini
.\Run-AITrader.ps1 -Action agent -Config configs/gemini_config.json

# With OpenRouter (Claude, GPT, etc.)
.\Run-AITrader.ps1 -Action agent -Config configs/openrouter_config.json

# With custom config
.\Run-AITrader.ps1 -Action agent -Config configs/my_custom_config.json
```

#### View Results in Web UI

```powershell
.\Run-AITrader.ps1 -Action ui
```

Opens web interface at: <http://localhost:8888>

#### Regenerate Frontend Cache

```powershell
.\Run-AITrader.ps1 -Action cache
```

### Advanced Usage

#### Skip Data Preparation (Use Existing Data)

```powershell
.\Run-AITrader.ps1 -Action all -SkipData
```

#### Skip Services (Already Running)

```powershell
.\Run-AITrader.ps1 -Action all -SkipServices
```

#### Hourly Trading (A-Shares)

```powershell
.\Run-AITrader.ps1 -Action all -Market astock -Frequency hourly
```

## Configuration Files

### Available Configs

| Config File | Provider | Models | Use Case |
|------------|----------|--------|----------|
| `default_config.json` | OpenAI | GPT-4, GPT-3.5 | US stocks |
| `gemini_config.json` | Google | Gemini 2.0 Flash, 1.5 Pro | All markets |
| `openrouter_config.json` | OpenRouter | Claude, GPT, Gemini, Llama, DeepSeek | All markets |
| `astock_config.json` | Various | - | Chinese A-shares |
| `default_crypto_config.json` | Various | - | Cryptocurrencies |

### Create Custom Config

```json
{
  "agent_type": "BaseAgent",
  "market": "us",
  "provider": "google",
  "date_range": {
    "init_date": "2025-10-01",
    "end_date": "2025-10-30"
  },
  "models": [
    {
      "name": "gemini-2.0-flash",
      "basemodel": "gemini-2.0-flash-exp",
      "signature": "my-gemini-agent",
      "enabled": true
    }
  ],
  "agent_config": {
    "max_steps": 30,
    "max_retries": 3,
    "initial_cash": 10000.0
  }
}
```

## Using Different LLM Providers

### Google Gemini

**Setup:**

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add to .env: `GOOGLE_API_KEY=your_key`
3. Use config: `configs/gemini_config.json`

**Run:**

```powershell
.\Run-AITrader.ps1 -Action all -Config configs/gemini_config.json
```

**Available Models:**

- `gemini-2.0-flash-exp` (Fastest, latest)
- `gemini-1.5-pro` (Most capable)
- `gemini-1.5-flash` (Balanced)

### OpenRouter (Multiple Providers)

**Setup:**

1. Get API key from [OpenRouter](https://openrouter.ai/keys)
2. Add to .env:

   ```env
   OPENAI_API_KEY=your_openrouter_key
   OPENAI_API_BASE=https://openrouter.ai/api/v1
   ```

3. Use config: `configs/openrouter_config.json`

**Run:**

```powershell
.\Run-AITrader.ps1 -Action all -Config configs/openrouter_config.json
```

**Available Models (200+):**

- `anthropic/claude-3.5-sonnet` (Best reasoning)
- `openai/gpt-4o` (OpenAI's best)
- `deepseek/deepseek-chat` (Cost-effective)
- `google/gemini-pro-1.5` (Gemini via OpenRouter)
- `meta-llama/llama-3.3-70b-instruct` (Open source)

**Advantages:**

- ✅ Access 200+ models with one API key
- ✅ Easy A/B testing between models
- ✅ Automatic failover
- ✅ Cost optimization

## Troubleshooting

### "UV not found"

Install UV package manager:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### "Module not found" errors

Sync dependencies:

```powershell
uv sync
```

### Services won't start

Check if ports are already in use:

```powershell
netstat -ano | findstr "8000 8001 8002 8003 8005 8006 8007"
```

Kill conflicting processes:

```powershell
# Find process ID from netstat output, then:
taskkill /PID <process_id> /F
```

### API Key errors

1. Check `.env` file exists (not `.env.example`)
2. Verify API keys are correct
3. Ensure no extra spaces in `.env` file
4. Check API key quotas (especially Alpha Vantage: 25 calls/day free tier)

### "Config file not found"

Ensure config file path is correct:

```powershell
# List available configs
Get-ChildItem configs\*.json
```

## File Structure

```
AI-Trader-main/
├── Run-AITrader.ps1          # 🌟 Master script (use this!)
├── .env                       # Your API keys (create from .env.example)
├── configs/                   # Configuration files
│   ├── gemini_config.json    # Google Gemini setup
│   ├── openrouter_config.json # OpenRouter setup
│   └── default_config.json    # OpenAI setup
├── data/                      # Market data
│   ├── agent_data/           # US stock trading results
│   ├── agent_data_astock/    # A-share trading results
│   └── agent_data_crypto/    # Crypto trading results
├── agent_tools/              # MCP services
├── tools/                     # Utility functions
└── docs/                      # Web UI
```

## Help

Show all available commands:

```powershell
.\Run-AITrader.ps1 -Action help
```

## Next Steps

1. **Run your first simulation:**

   ```powershell
   .\Run-AITrader.ps1 -Action all -Config configs/gemini_config.json
   ```

2. **View results:**

   ```powershell
   .\Run-AITrader.ps1 -Action ui
   ```

   Open browser to: <http://localhost:8888>

3. **Try different models:**
   - Edit `configs/gemini_config.json` or `configs/openrouter_config.json`
   - Enable/disable different models
   - Run again and compare results!

## Additional Resources

- **Full Documentation**: See [README.md](../README.md)
- **New Features**: See [NEW_FEATURES_v0.2.md](docs/NEW_FEATURES_v0.2.md)
- **Configuration Guide**: See [CONFIG_GUIDE.md](docs/CONFIG_GUIDE.md)
- **Caching System**: See [CACHING.md](docs/CACHING.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/HKUDS/AI-Trader/issues)
- **Discussions**: [GitHub Discussions](https://github.com/HKUDS/AI-Trader/discussions)

---

**Happy Trading! 🚀📈**
