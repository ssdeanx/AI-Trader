"""
Technical Indicators MCP Tool
Calculates common technical analysis indicators for trading decisions
No TA-Lib dependency - pure Python/NumPy implementation
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()


def calculate_sma(prices: List[float], period: int) -> List[float]:
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return [None] * len(prices)
    
    sma = []
    for i in range(len(prices)):
        if i < period - 1:
            sma.append(None)
        else:
            sma.append(np.mean(prices[i - period + 1:i + 1]))
    
    return sma


def calculate_ema(prices: List[float], period: int) -> List[float]:
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return [None] * len(prices)
    
    ema = []
    multiplier = 2 / (period + 1)
    
    # Start with SMA for first EMA value
    initial_sma = np.mean(prices[:period])
    ema.extend([None] * (period - 1))
    ema.append(initial_sma)
    
    for i in range(period, len(prices)):
        ema_value = (prices[i] - ema[-1]) * multiplier + ema[-1]
        ema.append(ema_value)
    
    return ema


def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """
    Calculate Relative Strength Index (RSI)
    
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    """
    if len(prices) < period + 1:
        return [None] * len(prices)
    
    # Calculate price changes
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    # Calculate initial averages
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    rsi = [None] * period
    
    # Calculate first RSI
    if avg_loss == 0:
        rsi.append(100)
    else:
        rs = avg_gain / avg_loss
        rsi.append(100 - (100 / (1 + rs)))
    
    # Calculate subsequent RSI values using smoothed averages
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))
    
    return rsi


def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Dict[str, List[float]]:
    """
    Calculate MACD (Moving Average Convergence Divergence)
    
    Returns:
        {
            "macd": MACD line,
            "signal": Signal line,
            "histogram": MACD histogram
        }
    """
    # Calculate fast and slow EMAs
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)
    
    # Calculate MACD line
    macd_line = []
    for i in range(len(prices)):
        if fast_ema[i] is None or slow_ema[i] is None:
            macd_line.append(None)
        else:
            macd_line.append(fast_ema[i] - slow_ema[i])
    
    # Calculate signal line (EMA of MACD)
    macd_values = [x for x in macd_line if x is not None]
    if len(macd_values) < signal_period:
        signal_line = [None] * len(prices)
        histogram = [None] * len(prices)
    else:
        signal_line = calculate_ema(
            [x if x is not None else 0 for x in macd_line],
            signal_period
        )
        
        # Calculate histogram
        histogram = []
        for i in range(len(prices)):
            if macd_line[i] is None or signal_line[i] is None:
                histogram.append(None)
            else:
                histogram.append(macd_line[i] - signal_line[i])
    
    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    }


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0
) -> Dict[str, List[float]]:
    """
    Calculate Bollinger Bands
    
    Returns:
        {
            "middle": Middle band (SMA),
            "upper": Upper band,
            "lower": Lower band,
            "bandwidth": Band width
        }
    """
    middle_band = calculate_sma(prices, period)
    
    upper_band = []
    lower_band = []
    bandwidth = []
    
    for i in range(len(prices)):
        if middle_band[i] is None:
            upper_band.append(None)
            lower_band.append(None)
            bandwidth.append(None)
        else:
            # Calculate standard deviation
            window = prices[max(0, i - period + 1):i + 1]
            std = np.std(window)
            
            upper = middle_band[i] + (std_dev * std)
            lower = middle_band[i] - (std_dev * std)
            
            upper_band.append(upper)
            lower_band.append(lower)
            bandwidth.append((upper - lower) / middle_band[i] * 100 if middle_band[i] != 0 else 0)
    
    return {
        "middle": middle_band,
        "upper": upper_band,
        "lower": lower_band,
        "bandwidth": bandwidth
    }


def calculate_stochastic_oscillator(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    k_period: int = 14,
    d_period: int = 3
) -> Dict[str, List[float]]:
    """
    Calculate Stochastic Oscillator
    
    %K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100
    %D = 3-period SMA of %K
    """
    k_values = []
    
    for i in range(len(closes)):
        if i < k_period - 1:
            k_values.append(None)
        else:
            window_high = max(highs[i - k_period + 1:i + 1])
            window_low = min(lows[i - k_period + 1:i + 1])
            
            if window_high == window_low:
                k_values.append(50)
            else:
                k = (closes[i] - window_low) / (window_high - window_low) * 100
                k_values.append(k)
    
    # Calculate %D (SMA of %K)
    d_values = calculate_sma([x if x is not None else 0 for x in k_values], d_period)
    
    return {
        "k": k_values,
        "d": d_values
    }


def calculate_atr(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14
) -> List[float]:
    """
    Calculate Average True Range (ATR)
    Measures market volatility
    """
    true_ranges = []
    
    for i in range(len(closes)):
        if i == 0:
            true_ranges.append(highs[i] - lows[i])
        else:
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            true_ranges.append(tr)
    
    # Calculate ATR using EMA
    atr = calculate_ema(true_ranges, period)
    
    return atr


def identify_support_resistance(prices: List[float], window: int = 20) -> Dict[str, List[float]]:
    """
    Identify support and resistance levels using local extrema
    """
    support_levels = []
    resistance_levels = []
    
    for i in range(window, len(prices) - window):
        window_prices = prices[i - window:i + window + 1]
        
        # Check if current price is a local minimum (support)
        if prices[i] == min(window_prices):
            support_levels.append(prices[i])
        
        # Check if current price is a local maximum (resistance)
        if prices[i] == max(window_prices):
            resistance_levels.append(prices[i])
    
    # Remove duplicates and sort
    support_levels = sorted(list(set([round(x, 2) for x in support_levels])))
    resistance_levels = sorted(list(set([round(x, 2) for x in resistance_levels])), reverse=True)
    
    return {
        "support_levels": support_levels[:5],  # Top 5 support levels
        "resistance_levels": resistance_levels[:5]  # Top 5 resistance levels
    }


# Create MCP server
mcp = FastMCP("Technical Indicators for Trading Analysis")


@mcp.tool()
def calculate_indicators(
    prices: List[float],
    highs: Optional[List[float]] = None,
    lows: Optional[List[float]] = None,
    indicators: Optional[List[str]] = None
) -> Dict[str, any]:
    """
    Calculate multiple technical indicators at once
    
    Args:
        prices: List of closing prices (most recent last)
        highs: List of high prices (optional, for some indicators)
        lows: List of low prices (optional, for some indicators)
        indicators: List of indicators to calculate (default: all)
                   Options: "sma", "ema", "rsi", "macd", "bollinger", "stochastic", "atr"
    
    Returns:
        Dictionary containing all calculated indicators
    
    Examples:
        calculate_indicators([100, 102, 105, 103, 107, 110, 108], indicators=["sma", "rsi"])
    """
    try:
        if not prices or len(prices) < 2:
            return {"error": "Need at least 2 price points"}
        
        if indicators is None:
            indicators = ["sma", "ema", "rsi", "macd", "bollinger"]
        
        results = {
            "data_points": len(prices),
            "current_price": prices[-1],
            "indicators": {}
        }
        
        # Calculate requested indicators
        if "sma" in indicators:
            results["indicators"]["sma_20"] = calculate_sma(prices, 20)[-1]
            results["indicators"]["sma_50"] = calculate_sma(prices, 50)[-1] if len(prices) >= 50 else None
        
        if "ema" in indicators:
            results["indicators"]["ema_12"] = calculate_ema(prices, 12)[-1]
            results["indicators"]["ema_26"] = calculate_ema(prices, 26)[-1]
        
        if "rsi" in indicators:
            rsi = calculate_rsi(prices)
            results["indicators"]["rsi"] = rsi[-1]
            if rsi[-1] is not None:
                if rsi[-1] > 70:
                    results["indicators"]["rsi_signal"] = "OVERBOUGHT"
                elif rsi[-1] < 30:
                    results["indicators"]["rsi_signal"] = "OVERSOLD"
                else:
                    results["indicators"]["rsi_signal"] = "NEUTRAL"
        
        if "macd" in indicators:
            macd = calculate_macd(prices)
            results["indicators"]["macd"] = {
                "macd": macd["macd"][-1],
                "signal": macd["signal"][-1],
                "histogram": macd["histogram"][-1]
            }
            if macd["histogram"][-1] is not None and macd["histogram"][-2] is not None:
                if macd["histogram"][-1] > 0 and macd["histogram"][-2] <= 0:
                    results["indicators"]["macd_signal"] = "BULLISH_CROSSOVER"
                elif macd["histogram"][-1] < 0 and macd["histogram"][-2] >= 0:
                    results["indicators"]["macd_signal"] = "BEARISH_CROSSOVER"
                else:
                    results["indicators"]["macd_signal"] = "NO_CROSSOVER"
        
        if "bollinger" in indicators:
            bb = calculate_bollinger_bands(prices)
            current_price = prices[-1]
            results["indicators"]["bollinger_bands"] = {
                "upper": bb["upper"][-1],
                "middle": bb["middle"][-1],
                "lower": bb["lower"][-1],
                "bandwidth": bb["bandwidth"][-1]
            }
            
            if bb["upper"][-1] is not None and bb["lower"][-1] is not None:
                if current_price >= bb["upper"][-1]:
                    results["indicators"]["bollinger_signal"] = "OVERBOUGHT"
                elif current_price <= bb["lower"][-1]:
                    results["indicators"]["bollinger_signal"] = "OVERSOLD"
                else:
                    results["indicators"]["bollinger_signal"] = "NEUTRAL"
        
        if "stochastic" in indicators and highs and lows:
            if len(highs) == len(prices) and len(lows) == len(prices):
                stoch = calculate_stochastic_oscillator(highs, lows, prices)
                results["indicators"]["stochastic"] = {
                    "k": stoch["k"][-1],
                    "d": stoch["d"][-1]
                }
        
        if "atr" in indicators and highs and lows:
            if len(highs) == len(prices) and len(lows) == len(prices):
                atr = calculate_atr(highs, lows, prices)
                results["indicators"]["atr"] = atr[-1]
        
        results["timestamp"] = datetime.now().isoformat()
        return results
        
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def generate_trading_signals(
    prices: List[float],
    highs: Optional[List[float]] = None,
    lows: Optional[List[float]] = None
) -> Dict[str, any]:
    """
    Generate comprehensive trading signals based on multiple indicators
    
    Args:
        prices: List of closing prices
        highs: List of high prices (optional)
        lows: List of low prices (optional)
    
    Returns:
        Trading signals with buy/sell/hold recommendations
    
    Examples:
        generate_trading_signals([100, 102, 105, 103, 107, 110, 108, 112, 115])
    """
    try:
        if len(prices) < 30:
            return {"error": "Need at least 30 price points for reliable signals"}
        
        signals = []
        signal_scores = {"bullish": 0, "bearish": 0, "neutral": 0}
        
        # RSI Signal
        rsi = calculate_rsi(prices)
        if rsi[-1] is not None:
            if rsi[-1] < 30:
                signals.append({"indicator": "RSI", "signal": "BULLISH", "reason": f"Oversold (RSI: {rsi[-1]:.1f})"})
                signal_scores["bullish"] += 2
            elif rsi[-1] > 70:
                signals.append({"indicator": "RSI", "signal": "BEARISH", "reason": f"Overbought (RSI: {rsi[-1]:.1f})"})
                signal_scores["bearish"] += 2
            else:
                signal_scores["neutral"] += 1
        
        # MACD Signal
        macd = calculate_macd(prices)
        if macd["histogram"][-1] is not None and len(macd["histogram"]) > 1:
            if macd["histogram"][-1] > 0 and macd["histogram"][-2] <= 0:
                signals.append({"indicator": "MACD", "signal": "BULLISH", "reason": "Bullish crossover"})
                signal_scores["bullish"] += 2
            elif macd["histogram"][-1] < 0 and macd["histogram"][-2] >= 0:
                signals.append({"indicator": "MACD", "signal": "BEARISH", "reason": "Bearish crossover"})
                signal_scores["bearish"] += 2
        
        # Moving Average Signal
        sma_20 = calculate_sma(prices, 20)
        sma_50 = calculate_sma(prices, 50)
        
        if sma_20[-1] is not None and sma_50[-1] is not None:
            if sma_20[-1] > sma_50[-1] and (len(sma_20) < 2 or sma_20[-2] <= sma_50[-2]):
                signals.append({"indicator": "MA", "signal": "BULLISH", "reason": "Golden cross (SMA20 > SMA50)"})
                signal_scores["bullish"] += 2
            elif sma_20[-1] < sma_50[-1] and (len(sma_20) < 2 or sma_20[-2] >= sma_50[-2]):
                signals.append({"indicator": "MA", "signal": "BEARISH", "reason": "Death cross (SMA20 < SMA50)"})
                signal_scores["bearish"] += 2
        
        # Bollinger Bands Signal
        bb = calculate_bollinger_bands(prices)
        current_price = prices[-1]
        
        if bb["lower"][-1] is not None and bb["upper"][-1] is not None:
            if current_price <= bb["lower"][-1]:
                signals.append({"indicator": "BB", "signal": "BULLISH", "reason": "Price at lower band"})
                signal_scores["bullish"] += 1
            elif current_price >= bb["upper"][-1]:
                signals.append({"indicator": "BB", "signal": "BEARISH", "reason": "Price at upper band"})
                signal_scores["bearish"] += 1
        
        # Determine overall signal
        total_signals = sum(signal_scores.values())
        if total_signals == 0:
            overall_signal = "HOLD"
            confidence = 0
        else:
            bullish_pct = signal_scores["bullish"] / total_signals * 100
            bearish_pct = signal_scores["bearish"] / total_signals * 100
            
            if bullish_pct > 60:
                overall_signal = "BUY"
                confidence = bullish_pct
            elif bearish_pct > 60:
                overall_signal = "SELL"
                confidence = bearish_pct
            else:
                overall_signal = "HOLD"
                confidence = max(bullish_pct, bearish_pct)
        
        return {
            "overall_signal": overall_signal,
            "confidence": round(confidence, 1),
            "individual_signals": signals,
            "signal_distribution": signal_scores,
            "current_price": current_price,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def find_support_resistance(prices: List[float], window: int = 20) -> Dict[str, any]:
    """
    Identify key support and resistance price levels
    
    Args:
        prices: List of prices
        window: Window size for finding local extrema
    
    Returns:
        Support and resistance levels
    
    Examples:
        find_support_resistance([100, 105, 103, 108, 107, 112, 110, 115])
    """
    try:
        if len(prices) < window * 2:
            return {"error": f"Need at least {window * 2} price points"}
        
        levels = identify_support_resistance(prices, window)
        current_price = prices[-1]
        
        # Find nearest support and resistance
        nearest_support = None
        nearest_resistance = None
        
        for level in levels["support_levels"]:
            if level < current_price:
                nearest_support = level
                break
        
        for level in levels["resistance_levels"]:
            if level > current_price:
                nearest_resistance = level
                break
        
        return {
            "current_price": current_price,
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
            "all_support_levels": levels["support_levels"],
            "all_resistance_levels": levels["resistance_levels"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Test the technical indicators
    print("🧪 Testing Technical Indicators Tool\n")
    
    # Generate sample price data
    np.random.seed(42)
    base_price = 100
    prices = [base_price]
    for _ in range(60):
        change = np.random.randn() * 2
        prices.append(max(prices[-1] + change, 50))
    
    print(f"Sample data: {len(prices)} prices from {prices[0]:.2f} to {prices[-1]:.2f}")
    
    # Test indicators
    result = calculate_indicators(prices, indicators=["sma", "rsi", "macd", "bollinger"])
    print(f"\nIndicators:")
    print(f"  RSI: {result['indicators'].get('rsi', 'N/A')}")
    print(f"  SMA(20): {result['indicators'].get('sma_20', 'N/A')}")
    
    # Test signals
    signals = generate_trading_signals(prices)
    print(f"\nTrading Signals:")
    print(f"  Overall: {signals.get('overall_signal', 'N/A')}")
    print(f"  Confidence: {signals.get('confidence', 0):.1f}%")
    
    print("\n🚀 Starting MCP server on port 8007...")
    mcp.run(transport="streamable_http", port=int(os.getenv("TECHNICAL_HTTP_PORT", "8007")))
