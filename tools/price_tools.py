import os

from dotenv import load_dotenv

load_dotenv()
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add project root directory to Python path for easy execution from subdirectories
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from tools.general_tools import get_config_value

def _normalize_timestamp_str(ts: str) -> str:
    """
    Normalize timestamp string to zero-padded HH for robust string/chrono comparisons.
    - If ts has time part like 'YYYY-MM-DD H:MM:SS', pad hour to 'HH'.
    - If ts is date-only, return as-is.
    """
    try:
        if " " not in ts:
            return ts
        date_part, time_part = ts.split(" ", 1)
        parts = time_part.split(":")
        if len(parts) != 3:
            return ts
        hour, minute, second = parts
        hour = hour.zfill(2)
        return f"{date_part} {hour}:{minute}:{second}"
    except Exception:
        return ts

def _parse_timestamp_to_dt(ts: str) -> datetime:
    """
    Parse timestamp string to datetime, supporting both date-only and datetime.
    Assumes ts is already normalized if time exists.
    """
    if " " in ts:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    return datetime.strptime(ts, "%Y-%m-%d")


def get_market_type() -> str:
    """
    Get market type intelligently, supports multiple detection methods:
    1. Priority: read MARKET from config
    2. If not set, infer from LOG_PATH (agent_data_astock -> cn, agent_data_crypto -> crypto, agent_data -> us)
    3. Finally defaults to us

    Returns:
        "cn" for A-shares market, "us" for US market, "crypto" for cryptocurrency market
    """
    # Method 1: Read from config
    market = get_config_value("MARKET", None)
    if market in ["cn", "us", "crypto"]:
        return market

    # Method 2: Infer from LOG_PATH
    log_path = get_config_value("LOG_PATH", "./data/agent_data")
    if log_path:
        if "astock" in log_path.lower() or "a_stock" in log_path.lower():
            return "cn"
        elif "crypto" in log_path.lower():
            return "crypto"

    # Method 3: Default to US stocks
    return "us"


all_nasdaq_100_symbols = [
    "NVDA",
    "MSFT",
    "AAPL",
    "GOOG",
    "GOOGL",
    "AMZN",
    "META",
    "AVGO",
    "TSLA",
    "NFLX",
    "PLTR",
    "COST",
    "ASML",
    "AMD",
    "CSCO",
    "AZN",
    "TMUS",
    "MU",
    "LIN",
    "PEP",
    "SHOP",
    "APP",
    "INTU",
    "AMAT",
    "LRCX",
    "PDD",
    "QCOM",
    "ARM",
    "INTC",
    "BKNG",
    "AMGN",
    "TXN",
    "ISRG",
    "GILD",
    "KLAC",
    "PANW",
    "ADBE",
    "HON",
    "CRWD",
    "CEG",
    "ADI",
    "ADP",
    "DASH",
    "CMCSA",
    "VRTX",
    "MELI",
    "SBUX",
    "CDNS",
    "ORLY",
    "SNPS",
    "MSTR",
    "MDLZ",
    "ABNB",
    "MRVL",
    "CTAS",
    "TRI",
    "MAR",
    "MNST",
    "CSX",
    "ADSK",
    "PYPL",
    "FTNT",
    "AEP",
    "WDAY",
    "REGN",
    "ROP",
    "NXPI",
    "DDOG",
    "AXON",
    "ROST",
    "IDXX",
    "EA",
    "PCAR",
    "FAST",
    "EXC",
    "TTWO",
    "XEL",
    "ZS",
    "PAYX",
    "WBD",
    "BKR",
    "CPRT",
    "CCEP",
    "FANG",
    "TEAM",
    "CHTR",
    "KDP",
    "MCHP",
    "GEHC",
    "VRSK",
    "CTSH",
    "CSGP",
    "KHC",
    "ODFL",
    "DXCM",
    "TTD",
    "ON",
    "BIIB",
    "LULU",
    "CDW",
    "GFS",
]

all_sse_50_symbols = [
    "600519.SH",
    "601318.SH",
    "600036.SH",
    "601899.SH",
    "600900.SH",
    "601166.SH",
    "600276.SH",
    "600030.SH",
    "603259.SH",
    "688981.SH",
    "688256.SH",
    "601398.SH",
    "688041.SH",
    "601211.SH",
    "601288.SH",
    "601328.SH",
    "688008.SH",
    "600887.SH",
    "600150.SH",
    "601816.SH",
    "601127.SH",
    "600031.SH",
    "688012.SH",
    "603501.SH",
    "601088.SH",
    "600309.SH",
    "601601.SH",
    "601668.SH",
    "603993.SH",
    "601012.SH",
    "601728.SH",
    "600690.SH",
    "600809.SH",
    "600941.SH",
    "600406.SH",
    "601857.SH",
    "601766.SH",
    "601919.SH",
    "600050.SH",
    "600760.SH",
    "601225.SH",
    "600028.SH",
    "601988.SH",
    "688111.SH",
    "601985.SH",
    "601888.SH",
    "601628.SH",
    "601600.SH",
    "601658.SH",
    "600048.SH",
]


def get_merged_file_path(market: str = "us") -> Path:
    """Get merged.jsonl path based on market type.

    Args:
        market: Market type, "us" for US stocks, "cn" for A-shares, "crypto" for cryptocurrencies

    Returns:
        Path object pointing to the merged.jsonl file
    """
    base_dir = Path(__file__).resolve().parents[1]
    if market == "cn":
        return base_dir / "data" / "A_stock" / "merged.jsonl"
    elif market == "crypto":
        return base_dir / "data" / "crypto" / "crypto_merged.jsonl"
    else:
        return base_dir / "data" / "merged.jsonl"

def _resolve_merged_file_path_for_date(
    today_date: Optional[str], market: str, merged_path: Optional[str] = None
) -> Path:
    """
    Resolve the correct merged data file path taking into account market and granularity.
    For A-shares:
      - Daily: data/A_stock/merged.jsonl
      - Hourly (timestamp contains space): data/A_stock/merged_hourly.jsonl
    A custom merged_path, if provided, takes precedence.
    """
    if merged_path is not None:
        return Path(merged_path)
    base_dir = Path(__file__).resolve().parents[1]
    if market == "cn" and today_date and " " in today_date:
        # Hourly trading session for A-shares
        return base_dir / "data" / "A_stock" / "merged_hourly.jsonl"
    return get_merged_file_path(market)


def is_trading_day(date: str, market: str = "us") -> bool:
    """Check if a given date is a trading day by looking up merged.jsonl.

    Args:
        date: Date string in "YYYY-MM-DD" format
        market: Market type ("us", "cn", or "crypto")

    Returns:
        True if the date exists in merged.jsonl (is a trading day), False otherwise
    """
    # MVP assumption: crypto trades every day, but the date should not be neither in the future nor no any data yet.
    # if market == "crypto":
    #     # Parse input date/time and compare real-world time (to the minute).
    #     # If input has no time part, default to 00:00. Supported formats:
    #     #   "YYYY-MM-DD", "YYYY-MM-DD HH:MM", "YYYY-MM-DD HH:MM:SS"
    #     fmt_candidates = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
    #     input_dt = None
    #     for fmt in fmt_candidates:
    #         try:
    #             input_dt = datetime.strptime(date, fmt)
    #             break
    #         except Exception:
    #             continue
    #     if input_dt is None:
    #         # Unable to parse input date -> treat as not a trading day
    #         return False

    #     # Normalize to minute precision (ignore seconds/microseconds)
    #     input_dt = input_dt.replace(second=0, microsecond=0)
    #     now_minute = datetime.now().replace(second=0, microsecond=0)

    #     # If current real-world time is earlier than the requested time, it's future -> return False
    #     if now_minute < input_dt:
    #         return False
    #     return True

    merged_file_path = get_merged_file_path(market)

    if not merged_file_path.exists():
        print(f"⚠️  Warning: {merged_file_path} not found, cannot validate trading day")
        return False

    try:
        with open(merged_file_path, "r", encoding="utf-8", errors="replace") as f:
            # Read first line to check if date exists
            for line in f:
                try:
                    data = json.loads(line.strip())
                    # Check for daily time series first
                    time_series = data.get("Time Series (Daily)", {})
                    if date in time_series:
                        return True

                    # If no daily data, check for hourly data (e.g., "Time Series (60min)")
                    for key, value in data.items():
                        if key.startswith("Time Series") and isinstance(value, dict):
                            # Check if any hourly timestamp starts with the date
                            for timestamp in value.keys():
                                if timestamp.startswith(date):
                                    return True
                except json.JSONDecodeError:
                    continue
            # If we get here, checked all stocks and date was not found in any
            return False
    except Exception as e:
        print(f"⚠️  Error checking trading day: {e}")
        return False


def get_all_trading_days(market: str = "us") -> List[str]:
    """Get all available trading days from merged.jsonl.

    Args:
        market: Market type ("us" or "cn")

    Returns:
        Sorted list of trading dates in "YYYY-MM-DD" format
    """
    merged_file_path = get_merged_file_path(market)

    if not merged_file_path.exists():
        print(f"⚠️  Warning: {merged_file_path} not found")
        return []

    trading_days = set()
    try:
        with open(merged_file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    time_series = data.get("Time Series (Daily)", {})
                    # Add all dates from this stock's time series
                    trading_days.update(time_series.keys())
                except json.JSONDecodeError:
                    continue
        return sorted(list(trading_days))
    except Exception as e:
        print(f"⚠️  Error reading trading days: {e}")
        return []


def get_stock_name_mapping(market: str = "us") -> Dict[str, str]:
    """Get mapping from stock symbols to names.

    Args:
        market: Market type ("us" or "cn")

    Returns:
        Dictionary mapping symbols to names, e.g. {"600519.SH": "Kweichow Moutai"}
    """
    merged_file_path = get_merged_file_path(market)

    if not merged_file_path.exists():
        return {}

    name_map = {}
    try:
        with open(merged_file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    meta = data.get("Meta Data", {})
                    symbol = meta.get("2. Symbol")
                    name = meta.get("2.1. Name", "")
                    if symbol and name:
                        name_map[symbol] = name
                except json.JSONDecodeError:
                    continue
        return name_map
    except Exception as e:
        print(f"⚠️  Error reading stock names: {e}")
        return {}


def format_price_dict_with_names(
    price_dict: Dict[str, Optional[float]], market: str = "us"
) -> Dict[str, Optional[float]]:
    """Format price dictionary to include stock names for display.

    Args:
        price_dict: Original price dictionary with keys like "600519.SH_price"
        market: Market type ("us" or "cn")

    Returns:
        New dictionary with keys like "600519.SH (Kweichow Moutai)_price" for CN market,
        unchanged for US market
    """
    if market != "cn":
        return price_dict

    name_map = get_stock_name_mapping(market)
    if not name_map:
        return price_dict

    formatted_dict = {}
    for key, value in price_dict.items():
        if key.endswith("_price"):
            symbol = key[:-6]  # Remove "_price" suffix
            stock_name = name_map.get(symbol, "")
            if stock_name:
                new_key = f"{symbol} ({stock_name})_price"
            else:
                new_key = key
            formatted_dict[new_key] = value
        else:
            formatted_dict[key] = value

    return formatted_dict


def get_yesterday_date(today_date: str, merged_path: Optional[str] = None, market: str = "us") -> str:
    """
    Get the previous trading day or time point for the input date.
    Read all available trading times from merged.jsonl, then find the time before today_date.
    
    Args:
        today_date: Date string in format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS.
        merged_path: Optional custom merged.jsonl path; defaults to reading the corresponding market's merged.jsonl based on market parameter.
        market: Market type, "us" for US stocks, "cn" for A-shares

    Returns:
        yesterday_date: Previous trading day or time point string, same format as input.
    """
    # Parse input date/time
    if ' ' in today_date:
        input_dt = datetime.strptime(today_date, "%Y-%m-%d %H:%M:%S")
        date_only = False
    else:
        input_dt = datetime.strptime(today_date, "%Y-%m-%d")
        date_only = True
    
    # Get merged.jsonl file path
    merged_file = _resolve_merged_file_path_for_date(today_date, market, merged_path)
    
    if not merged_file.exists():
        # If file doesn't exist, fallback based on input type
        print(f"merged.jsonl file does not exist at {merged_file}")
        if date_only:
            yesterday_dt = input_dt - timedelta(days=1)
            while yesterday_dt.weekday() >= 5:
                yesterday_dt -= timedelta(days=1)
            return yesterday_dt.strftime("%Y-%m-%d")
        else:
            yesterday_dt = input_dt - timedelta(hours=1)
            return yesterday_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # Read all available trading times from merged.jsonl
    all_timestamps = set()
    
    with merged_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
                # Find all keys starting with "Time Series"
                for key, value in doc.items():
                    if key.startswith("Time Series"):
                        if isinstance(value, dict):
                            all_timestamps.update(value.keys())
                        break
            except Exception:
                continue
    
    if not all_timestamps:
        # If no timestamps found, fallback based on input type
        if date_only:
            yesterday_dt = input_dt - timedelta(days=1)
            while yesterday_dt.weekday() >= 5:
                yesterday_dt -= timedelta(days=1)
            return yesterday_dt.strftime("%Y-%m-%d")
        else:
            yesterday_dt = input_dt - timedelta(hours=1)
            return yesterday_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # Convert all timestamps to datetime objects and find the maximum timestamp less than today_date
    previous_timestamp = None
    
    for ts_str in all_timestamps:
        try:
            ts_dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            if ts_dt < input_dt:
                if previous_timestamp is None or ts_dt > previous_timestamp:
                    previous_timestamp = ts_dt
        except Exception:
            continue
    
    # If no earlier timestamp found, fallback based on input type
    if previous_timestamp is None:
        if date_only:
            yesterday_dt = input_dt - timedelta(days=1)
            while yesterday_dt.weekday() >= 5:
                yesterday_dt -= timedelta(days=1)
            return yesterday_dt.strftime("%Y-%m-%d")
        else:
            yesterday_dt = input_dt - timedelta(hours=1)
            return yesterday_dt.strftime("%Y-%m-%d %H:%M:%S")

    # Return result
    if date_only:
        return previous_timestamp.strftime("%Y-%m-%d")
    else:
        return previous_timestamp.strftime("%Y-%m-%d %H:%M:%S")



def get_open_prices(
    today_date: str, symbols: List[str], merged_path: Optional[str] = None, market: str = "us"
) -> Dict[str, Optional[float]]:
    """Read opening prices for specified date and symbols from data/merged.jsonl.

    Args:
        today_date: Date string in format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS.
        symbols: List of stock codes to query.
        merged_path: Optional custom merged.jsonl path; defaults to reading from project root data/merged.jsonl.
        market: Market type, "us" for US stocks, "cn" for A-shares

    Returns:
        {symbol_price: open_price or None} dictionary; value is None if corresponding date or symbol not found.
    """
    wanted = set(symbols)
    results: Dict[str, Optional[float]] = {}

    merged_file = _resolve_merged_file_path_for_date(today_date, market, merged_path)

    if not merged_file.exists():
        return results

    with merged_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
            except Exception:
                continue
            meta = doc.get("Meta Data", {}) if isinstance(doc, dict) else {}
            sym = meta.get("2. Symbol")
            if sym not in wanted:
                continue
            # Find all keys starting with "Time Series"
            series = None
            for key, value in doc.items():
                if key.startswith("Time Series"):
                    series = value
                    break
            if not isinstance(series, dict):
                continue
            bar = series.get(today_date)
            
            if isinstance(bar, dict):
                open_val = bar.get("1. buy price")
                
                try:
                    results[f"{sym}_price"] = float(open_val) if open_val is not None else None
                except Exception:
                    results[f"{sym}_price"] = None

    return results


def get_yesterday_open_and_close_price(
    today_date: str, symbols: List[str], merged_path: Optional[str] = None, market: str = "us"
) -> Tuple[Dict[str, Optional[float]], Dict[str, Optional[float]]]:
    """Read yesterday's buy and sell prices for specified date and stocks from data/merged.jsonl.

    Args:
        today_date: Date string in format YYYY-MM-DD, representing today's date.
        symbols: List of stock codes to query.
        merged_path: Optional custom merged.jsonl path; defaults to reading from project root data/merged.jsonl.
        market: Market type, "us" for US stocks, "cn" for A-shares

    Returns:
        Tuple of (buy_price_dict, sell_price_dict); value is None if corresponding date or symbol not found.
    """
    wanted = set(symbols)
    buy_results: Dict[str, Optional[float]] = {}
    sell_results: Dict[str, Optional[float]] = {}

    merged_file = _resolve_merged_file_path_for_date(today_date, market, merged_path)

    if not merged_file.exists():
        return buy_results, sell_results

    yesterday_date = get_yesterday_date(today_date, merged_path=merged_path, market=market)

    with merged_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
            except Exception:
                continue
            meta = doc.get("Meta Data", {}) if isinstance(doc, dict) else {}
            sym = meta.get("2. Symbol")
            if sym not in wanted:
                continue
            # Find all keys starting with "Time Series"
            series = None
            for key, value in doc.items():
                if key.startswith("Time Series"):
                    series = value
                    break
            if not isinstance(series, dict):
                continue

            # Try to get yesterday's buy and sell prices
            bar = series.get(yesterday_date)
            if isinstance(bar, dict):
                buy_val = bar.get("1. buy price")  # Buy price field
                sell_val = bar.get("4. sell price")  # Sell price field

                try:
                    buy_price = float(buy_val) if buy_val is not None else None
                    sell_price = float(sell_val) if sell_val is not None else None
                    buy_results[f"{sym}_price"] = buy_price
                    sell_results[f"{sym}_price"] = sell_price
                except Exception:
                    buy_results[f"{sym}_price"] = None
                    sell_results[f"{sym}_price"] = None
            else:
                # If no data for yesterday, try to look forward for the most recent trading day
                # raise ValueError(f"No data found for {sym} on {yesterday_date}")
                # print(f"No data found for {sym} on {yesterday_date}")
                buy_results[f'{sym}_price'] = None
                sell_results[f'{sym}_price'] = None
                # today_dt = datetime.strptime(today_date, "%Y-%m-%d")
                # yesterday_dt = today_dt - timedelta(days=1)
                # current_date = yesterday_dt
                # found_data = False
                # # Search forward at most 5 trading days
                # for _ in range(5):
                #     current_date -= timedelta(days=1)
                #     # Skip weekends
                #     while current_date.weekday() >= 5:
                #         current_date -= timedelta(days=1)
                #     check_date = current_date.strftime("%Y-%m-%d")
                #     bar = series.get(check_date)
                #     if isinstance(bar, dict):
                #         buy_val = bar.get("1. buy price")
                #         sell_val = bar.get("4. sell price")
                #         try:
                #             buy_price = float(buy_val) if buy_val is not None else None
                #             sell_price = float(sell_val) if sell_val is not None else None
                #             buy_results[f'{sym}_price'] = buy_price
                #             sell_results[f'{sym}_price'] = sell_price
                #             found_data = True
                #             break
                #         except Exception:
                #             continue
                # if not found_data:
                #     buy_results[f'{sym}_price'] = None
                #     sell_results[f'{sym}_price'] = None

    return buy_results, sell_results


def get_yesterday_profit(
    today_date: str,
    yesterday_buy_prices: Dict[str, Optional[float]],
    yesterday_sell_prices: Dict[str, Optional[float]],
    yesterday_init_position: Dict[str, float],
    stock_symbols: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Get position profit (for daily and hourly trading)
    
    Profit calculation: (previous time point closing price - previous time point opening price) * current position quantity
    
    For daily trading: calculate yesterday's profit
    For hourly trading: calculate previous hour's profit
    
    Args:
        today_date: Date/time string in format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS
        yesterday_buy_prices: Previous time point opening price dict, format {symbol_price: price}
        yesterday_sell_prices: Previous time point closing price dict, format {symbol_price: price}
        yesterday_init_position: Previous time point initial position dict, format {symbol: quantity}
        stock_symbols: Stock code list, defaults to all_nasdaq_100_symbols

    Returns:
        {symbol: profit} dict; value is 0.0 if corresponding date or symbol not found.
    """
    profit_dict = {}

    # Use provided stock list or default NASDAQ 100 list
    if stock_symbols is None:
        stock_symbols = all_nasdaq_100_symbols

    # Iterate through all stock codes
    for symbol in stock_symbols:
        symbol_price_key = f"{symbol}_price"

        # Get yesterday's opening and closing prices
        buy_price = yesterday_buy_prices.get(symbol_price_key)
        sell_price = yesterday_sell_prices.get(symbol_price_key)

        # Get yesterday's position weight
        position_weight = yesterday_init_position.get(symbol, 0.0)

        # Calculate profit: (closing price - opening price) * position weight
        if buy_price is not None and sell_price is not None and position_weight > 0:
            profit = (sell_price - buy_price) * position_weight
            profit_dict[symbol] = round(profit, 4)  # Keep 4 decimal places
        else:
            profit_dict[symbol] = 0.0

    return profit_dict

def get_today_init_position(today_date: str, signature: str) -> Dict[str, float]:
    """
    Get today's opening position (i.e., position from the previous trading day in the file). Read from ../data/agent_data/{signature}/position/position.jsonl.
    If multiple records exist for the same date, select the one with the largest id as initial position.

    Args:
        today_date: Date string in format YYYY-MM-DD, representing today's date.
        signature: Model name, used to build file path.

    Returns:
        {symbol: weight} dict; returns empty dict if corresponding date not found.
    """
    from tools.general_tools import get_config_value
    import os

    base_dir = Path(__file__).resolve().parents[1]

    # Get log_path from config, default to "agent_data" for backward compatibility
    log_path = get_config_value("LOG_PATH", "./data/agent_data")

    # Handle different path formats:
    # - If it's an absolute path (like temp directory), use it directly
    # - If it's a relative path starting with "./data/", remove the prefix and prepend base_dir/data
    # - Otherwise, treat as relative to base_dir/data
    if os.path.isabs(log_path):
        # Absolute path (like temp directory) - use directly
        position_file = Path(log_path) / signature / "position" / "position.jsonl"
    else:
        if log_path.startswith("./data/"):
            log_path = log_path[7:]  # Remove "./data/" prefix
        position_file = base_dir / "data" / log_path / signature / "position" / "position.jsonl"
#     position_file = base_dir / "data" / "agent_data" / signature / "position" / "position.jsonl"

    if not position_file.exists():
        print(f"Position file {position_file} does not exist")
        return {}
    # Get market type, smart detection
    market = get_market_type()
    yesterday_date = get_yesterday_date(today_date, market=market)
    max_id = -1
    latest_positions = {}
    with position_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
                record_date = doc.get("date")
                if record_date == yesterday_date:
                    current_id = doc.get("id", -1)
                    if current_id > max_id:
                        max_id = current_id
                        latest_positions = doc.get("positions", {})
            except Exception:
                continue
    return latest_positions


def get_latest_position(today_date: str, signature: str) -> Tuple[Dict[str, float], int]:
    """
    Get latest position. Read from ../data/agent_data/{signature}/position/position.jsonl.
    Prioritize selecting the record with the largest id on today_date;
    If no records for today, fallback to the previous trading day, selecting the record with the largest id.

    Args:
        today_date: Date string in format YYYY-MM-DD, representing today's date.
        signature: Model name, used to build file path.

    Returns:
        (positions, max_id):
          - positions: {symbol: weight} dict; empty dict if no records found.
          - max_id: Maximum id of selected record; -1 if no records found.
    """
    from tools.general_tools import get_config_value
    import os

    base_dir = Path(__file__).resolve().parents[1]

    # Get log_path from config, default to "agent_data" for backward compatibility
    log_path = get_config_value("LOG_PATH", "./data/agent_data")

    # Handle different path formats:
    # - If it's an absolute path (like temp directory), use it directly
    # - If it's a relative path starting with "./data/", remove the prefix and prepend base_dir/data
    # - Otherwise, treat as relative to base_dir/data
    if os.path.isabs(log_path):
        # Absolute path (like temp directory) - use directly
        position_file = Path(log_path) / signature / "position" / "position.jsonl"
    else:
        if log_path.startswith("./data/"):
            log_path = log_path[7:]  # Remove "./data/" prefix
        position_file = base_dir / "data" / log_path / signature / "position" / "position.jsonl"

    if not position_file.exists():
        return {}, -1

    # Get market type, smart detection
    market = get_market_type()

    # Step 1: First look for today's records
    max_id_today = -1
    latest_positions_today: Dict[str, float] = {}

    with position_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
                if doc.get("date") == today_date:
                    current_id = doc.get("id", -1)
                    if current_id > max_id_today:
                        max_id_today = current_id
                        latest_positions_today = doc.get("positions", {})
            except Exception:
                continue

    # If today's records exist, return directly
    if max_id_today >= 0 and latest_positions_today:
        return latest_positions_today, max_id_today

    # Step 2: If no records for today, fallback to previous trading day
    prev_date = get_yesterday_date(today_date, market=market)

    max_id_prev = -1
    latest_positions_prev: Dict[str, float] = {}
    with position_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
                if doc.get("date") == prev_date:
                    current_id = doc.get("id", -1)
                    if current_id > max_id_prev:
                        max_id_prev = current_id
                        latest_positions_prev = doc.get("positions", {})
            except Exception:
                continue

    # If no records from previous day either, try to find the latest non-empty record in the file (sorted by actual time and id)
    if max_id_prev < 0 or not latest_positions_prev:
        all_records: List[Dict[str, Any]] = []
        norm_today = _normalize_timestamp_str(today_date)
        today_dt = _parse_timestamp_to_dt(norm_today)
        with position_file.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    doc = json.loads(line)
                    doc_date = doc.get("date")
                    if not doc_date:
                        continue
                    norm_doc_date = _normalize_timestamp_str(doc_date)
                    doc_dt = _parse_timestamp_to_dt(norm_doc_date)
                    # Only consider records earlier than today_date
                    if doc_dt < today_dt:
                        positions = doc.get("positions", {})
                        # Skip empty position records
                        if positions:
                            all_records.append(doc)
                except Exception:
                    continue
        if all_records:
            # Sort by actual time first, then by id, take the latest one
            all_records.sort(
                key=lambda x: (
                    _parse_timestamp_to_dt(_normalize_timestamp_str(x.get("date", "1900-01-01"))),
                    x.get("id", 0),
                ),
                reverse=True,
            )
            latest_positions_prev = all_records[0].get("positions", {})
            max_id_prev = all_records[0].get("id", -1)
    return latest_positions_prev, max_id_prev

def add_no_trade_record(today_date: str, signature: str):
    """
    Add no-trade record. Take the last position from the previous day in ../data/agent_data/{signature}/position/position.jsonl and update today's position.jsonl file.
    Args:
        today_date: Date string in format YYYY-MM-DD, representing today's date.
        signature: Model name, used to build file path.

    Returns:
        None
    """
    save_item = {}
    current_position, current_action_id = get_latest_position(today_date, signature)
    save_item["date"] = today_date
    save_item["id"] = current_action_id + 1
    save_item["this_action"] = {"action": "no_trade", "symbol": "", "amount": 0}
    save_item["positions"] = current_position

    from tools.general_tools import get_config_value
    import os

    base_dir = Path(__file__).resolve().parents[1]

    # Get log_path from config, default to "agent_data" for backward compatibility
    log_path = get_config_value("LOG_PATH", "./data/agent_data")

    # Handle different path formats:
    # - If it's an absolute path (like temp directory), use it directly
    # - If it's a relative path starting with "./data/", remove the prefix and prepend base_dir/data
    # - Otherwise, treat as relative to base_dir/data
    if os.path.isabs(log_path):
        # Absolute path (like temp directory) - use directly
        position_file = Path(log_path) / signature / "position" / "position.jsonl"
    else:
        if log_path.startswith("./data/"):
            log_path = log_path[7:]  # Remove "./data/" prefix
        position_file = base_dir / "data" / log_path / signature / "position" / "position.jsonl"

    with position_file.open("a", encoding="utf-8", errors="replace") as f:
        f.write(json.dumps(save_item, ensure_ascii=False) + "\n")
    return


if __name__ == "__main__":
    today_date = get_config_value("TODAY_DATE")
    signature = get_config_value("SIGNATURE")
    if signature is None:
        raise ValueError("SIGNATURE environment variable is not set")
    if today_date is None:
        raise ValueError("TODAY_DATE environment variable is not set")
    print(today_date, signature)
    yesterday_date = get_yesterday_date(today_date)
    print(yesterday_date)
    # today_buy_price = get_open_prices(today_date, all_nasdaq_100_symbols)
    # print(today_buy_price)
    # yesterday_buy_prices, yesterday_sell_prices = get_yesterday_open_and_close_price(today_date, all_nasdaq_100_symbols)
    # print(yesterday_sell_prices)
    # today_init_position = get_today_init_position(today_date, signature='qwen3-max')
    # print(today_init_position)
    # latest_position, latest_action_id = get_latest_position('2025-10-24', 'qwen3-max')
    # print(latest_position, latest_action_id)
    latest_position, latest_action_id = get_latest_position('2025-10-16 16:00:00', 'test')
    print(latest_position, latest_action_id)
    # yesterday_profit = get_yesterday_profit(today_date, yesterday_buy_prices, yesterday_sell_prices, today_init_position)
    # # print(yesterday_profit)
    # add_no_trade_record(today_date, signature)
