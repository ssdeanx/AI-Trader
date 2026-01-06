# AI-Trader Copilot Instructions

## Architecture Overview
AI-Trader is a Python-based automated trading simulation system using AI agents for stock/crypto decisions. Core design:
- **Modular Agents**: Base classes (`agent/base_agent/`) extended for markets (US: `base_agent.py`, Crypto: `base_agent_crypto.py`, A-shares: `base_agent_astock.py`, Hourly A-shares: `base_agent_astock_hour.py`). Inheritance enables market-specific rules (e.g., T+1 settlement for A-shares).
- **MCP Tool Integration**: Agents use Model Context Protocol for external tools (math, price fetching, trading). Tools run as HTTP servers (see `agent_tools/start_mcp_services.py`).
- **Data Flow**: Agents query MCP tools, log actions to JSONL files (`data/agent_data*/signature/log/date/log.jsonl`), update positions (`position/position.jsonl`).
- **Why This Structure**: Async design for API efficiency; MCP for pluggable tools; inheritance for market specialization without duplication.

## Key Components
- **Agents**: `agent/base_agent*/` - Handle initialization, trading loops, retries. Example: `BaseAgentAStock` uses SSE 50 symbols and Chinese prompts.
- **Tools**: `agent_tools/` (MCP servers) + `tools/` (utilities). Example: `tool_get_price_local.py` fetches local JSON data.
- **Prompts**: `prompts/agent_prompt*.py` - Market-specific system prompts with trading rules.
- **Data**: `data/` - Historical prices (JSON), positions (JSONL). Example: Positions track cash + holdings per symbol.

## Developer Workflows
- **Setup**: Install deps with `pip install -r requirements.txt` (use Python 3.12+; resolve conflicts via `uv python install 3.12`). Start MCP: `python agent_tools/start_mcp_services.py`.
- **Run Simulations**: `python main.py` (sequential) or `main_parrallel.py` (parallel). Agents process trading dates, log steps.
- **Debug**: Check JSONL logs for agent responses/tool calls. Position updates in `position.jsonl`. Errors often from missing MCP services or API keys.
- **Test**: No formal tests; validate by running sessions and inspecting logs/positions.

## Conventions & Patterns
- **DeepSeek Wrapper**: Use `DeepSeekChatOpenAI` (duplicated across agents) for tool_calls JSON parsing. Example: Fixes `arguments` as string vs. dict.
- **Market-Specific Logic**: A-shares use ¥ currency, 100-share lots; crypto uses USDT, float holdings. Prompts in Chinese for A-shares.
- **Async with Retry**: All API calls use `_ainvoke_with_retry` with exponential backoff. Example: `await asyncio.sleep(self.base_delay * attempt)`.
- **Logging**: JSONL entries with timestamp, signature, messages. Example: `{"timestamp": "2026-01-06T...", "signature": "agent1", "new_messages": [...]}`.
- **Config Management**: Via `tools/general_tools.py` (write_config_value/get_config_value) for runtime state.

## Integration Points
- **External APIs**: OpenAI/Google GenAI (via `langchain_*`), Alpha Vantage (news), Jina (search). Keys from `.env`.
- **MCP Servers**: Local HTTP on ports (e.g., 8000 math, 8002 trade). Config in `_get_default_mcp_config()`.
- **Cross-Component**: Agents call tools via MCP client; prompts reference market symbols/rules.

Reference: `README.md` for setup; `agent/base_agent/base_agent.py` for core logic; `prompts/agent_prompt_astock.py` for A-share rules.