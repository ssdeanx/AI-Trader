# 🚀 AI-Trader Quick Command Reference

## One-Line Setup

```powershell
# Install UV + Sync Dependencies + Configure
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"; cd C:\Users\ssdsk\AI-Trader-main; uv sync; Copy-Item .env.example .env
```

Then edit `.env` with your API keys.

---

## Common Commands

### Complete Workflows

```powershell
# Default (OpenAI)
.\Run-AITrader.ps1 -Action all

# Gemini
.\Run-AITrader.ps1 -Action all -Config configs/gemini_config.json

# OpenRouter (Claude, GPT, Llama, DeepSeek)
.\Run-AITrader.ps1 -Action all -Config configs/openrouter_config.json

# A-Shares (Chinese stocks)
.\Run-AITrader.ps1 -Action all -Market astock

# Crypto
.\Run-AITrader.ps1 -Action all -Market crypto
```

### Individual Steps

```powershell
# 1. Fetch data
.\Run-AITrader.ps1 -Action data

# 2. Start services (background)
.\Run-AITrader.ps1 -Action services

# 3. Run agent (services must be running)
.\Run-AITrader.ps1 -Action agent

# 4. View results
.\Run-AITrader.ps1 -Action ui  # http://localhost:8888
```

### Shortcuts

```powershell
# Skip data (use existing)
.\Run-AITrader.ps1 -Action all -SkipData

# Skip services (already running)
.\Run-AITrader.ps1 -Action all -SkipServices

# Quick agent run (skip data + services)
.\Run-AITrader.ps1 -Action all -SkipData -SkipServices
```

---

## API Key Setup

### Gemini (Google)

```env
# In .env
GOOGLE_API_KEY=your_google_api_key_here
```

Get key: https://makersuite.google.com/app/apikey

### OpenRouter (200+ models)

```env
# In .env
OPENAI_API_KEY=your_openrouter_key_here
OPENAI_API_BASE=https://openrouter.ai/api/v1
```

Get key: https://openrouter.ai/keys

---

## Configuration Files

| Config | Provider | Models |
|--------|----------|--------|
| `configs/gemini_config.json` | Google | Gemini 2.0/1.5 |
| `configs/openrouter_config.json` | OpenRouter | Claude, GPT, Llama, DeepSeek |
| `configs/default_config.json` | OpenAI | GPT-4, GPT-3.5 |
| `configs/astock_config.json` | Various | A-shares |
| `configs/default_crypto_config.json` | Various | Crypto |

---

## Troubleshooting

### UV not found
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Module errors
```powershell
uv sync
```

### Port conflicts
```powershell
# Find what's using port 8000-8007
netstat -ano | findstr "800"

# Kill process
taskkill /PID <pid> /F
```

### Services not starting
```powershell
# Check if already running
Get-Process python

# Kill all Python processes
Get-Process python | Stop-Process -Force

# Restart services
.\Run-AITrader.ps1 -Action services
```

---

## Help

```powershell
# Show all options
.\Run-AITrader.ps1 -Action help

# Full documentation
.\Run-AITrader.ps1 -Action help | more
```

---

## Files to Edit

| File | Purpose |
|------|---------|
| `.env` | API keys and configuration |
| `configs/*.json` | Agent configurations |
| `Run-AITrader.ps1` | Main script (if needed) |

---

## Quick Test

```powershell
# Test with Gemini (fastest setup)
.\Run-AITrader.ps1 -Action all -Config configs/gemini_config.json

# Then view results
.\Run-AITrader.ps1 -Action ui
```

Open: http://localhost:8888

---

**For detailed instructions, see: `WINDOWS_QUICKSTART.md`**
