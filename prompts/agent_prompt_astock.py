# -*- coding: utf-8 -*-
"""
A-shares specific agent prompt module
Chinese A-shares specific agent prompt module
"""

import os

from dotenv import load_dotenv

load_dotenv()
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from tools.general_tools import get_config_value
from tools.price_tools import (all_sse_50_symbols,
                               format_price_dict_with_names, get_open_prices,
                               get_today_init_position,
                               get_yesterday_open_and_close_price,
                               get_yesterday_profit)

STOP_SIGNAL = "<FINISH_SIGNAL>"

agent_system_prompt_astock = """
You are an A-share fundamental analysis trading assistant.


Your goals are:
- Think and reason by calling available tools
- You need to consider the price and profit situation of each stock
- Your long-term goal is to maximize returns through this investment portfolio
- Before making decisions, collect as much information as possible through search tools to assist decision-making

Thinking standards:
- Clearly show key intermediate steps:
  - Read current positions and current price inputs
  - Update valuations and adjust weights for each target (if strategy requires)

Notes:
- You do not need to request user permission when operating, you can execute directly
- You must execute operations by calling tools, direct output operations will not be accepted
- **Currently trading hours, market is open, you can actually execute buy/sell operations**
- **If there is a specific current time, even if the time is 11:30:00 or 15:00:00 (looks like closing time), but the market is still open, you can still trade normally**

⚠️ Important behavior requirements:
1. **Must actually call buy() or sell() tools**, do not just give suggestions or analysis
2. **Prohibit fabricating false information**, if tool calls fail, real errors will be returned, you just need to report them
3. **Prohibit saying "due to trading system restrictions", "currently unable to execute", "Symbol not found", etc. self-assumed restrictions**
4. **If you think you should buy a certain stock, directly call buy("stock_code.SH", quantity)**
5. **If you think you should sell a certain stock, directly call sell("stock_code.SH", quantity)**
6. Only report errors when tools return errors; do not assume errors will occur without calling tools

🇨🇳 Important - A-share trading rules (applies to all .SH and .SZ stock codes):
1. **Stock code format - extremely important!**:
   - symbol parameter must be string type, must include .SH or .SZ suffix

2. **Lot trading requirement**: All buy/sell orders must be multiples of 100 shares (1 lot = 100 shares)
   - ✅ Correct: buy("600519.SH", 100), buy("600519.SH", 300), sell("600519.SH", 200)
   - ❌ Wrong: buy("600519.SH", 13), buy("600519.SH", 497), sell("600519.SH", 50)

3. **T+1 settlement rule**: Stocks bought today cannot be sold today
   - You can only sell stocks purchased before today
   - If you buy 100 shares of 600519.SH today, you must wait until tomorrow to sell
   - You can still sell previously held stocks

4. **Price limit restrictions**:
   - Regular stocks: ±10%
   - ST stocks: ±5%
   - STAR Market/Chinext: ±20%

Here is the information you need:

Current time:
{date}

Current positions (numbers after stock codes represent shares you hold, number after CASH represents available cash):
{positions}

Current position value (previous time point closing prices):
{yesterday_close_price}

Current buy prices:
{today_buy_price}

Previous period profit situation (daily = yesterday's profit, hourly = previous hour's profit):
{current_profit}

When you think the task is completed, output
{STOP_SIGNAL}
"""


def get_agent_system_prompt_astock(today_date: str, signature: str, stock_symbols: Optional[List[str]] = None) -> str:
    """
    Generate A-shares specific system prompt

    Args:
        today_date: Today's date
        signature: Agent signature
        stock_symbols: Stock code list, defaults to SSE 50 constituent stocks

    Returns:
        Formatted system prompt string
    """
    print(f"signature: {signature}")
    print(f"today_date: {today_date}")
    print(f"market: cn (A-shares)")

    # Default to SSE 50 constituent stocks
    if stock_symbols is None:
        stock_symbols = all_sse_50_symbols

    # Get previous time point buy and sell prices, hardcoded market="cn"
    # For daily trading: get yesterday's opening and closing prices
    # For hourly trading: get previous hour's opening and closing prices
    yesterday_buy_prices, yesterday_sell_prices = get_yesterday_open_and_close_price(
        today_date, stock_symbols, market="cn"
    )
    # Get current time point buy prices
    today_buy_price = get_open_prices(today_date, stock_symbols, market="cn")
    # Get current positions
    today_init_position = get_today_init_position(today_date, signature)
    
    # Calculate profit: (previous time point closing price - previous time point opening price) × position quantity
    # For daily trading: calculate yesterday's profit
    # For hourly trading: calculate previous hour's profit
    current_profit = get_yesterday_profit(
        today_date, yesterday_buy_prices, yesterday_sell_prices, today_init_position, stock_symbols
    )

    # A-share market displays Chinese stock names
    yesterday_sell_prices_display = format_price_dict_with_names(yesterday_sell_prices, market="cn")
    today_buy_price_display = format_price_dict_with_names(today_buy_price, market="cn")

    return agent_system_prompt_astock.format(
        date=today_date,
        positions=today_init_position,
        STOP_SIGNAL=STOP_SIGNAL,
        yesterday_close_price=yesterday_sell_prices_display,
        today_buy_price=today_buy_price_display,
        current_profit=current_profit,
    )


if __name__ == "__main__":
    today_date = get_config_value("TODAY_DATE")
    signature = get_config_value("SIGNATURE")
    if today_date is None:
        raise ValueError("TODAY_DATE environment variable is not set")
    if signature is None:
        raise ValueError("SIGNATURE environment variable is not set")
    print(get_agent_system_prompt_astock(today_date, signature))
