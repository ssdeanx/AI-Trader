"""
Market Sentiment Analysis MCP Tool
Analyzes sentiment of financial news, social media, and market commentary
Uses FinBERT and other financial domain-specific models
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

# Lazy imports for transformers (only loaded when needed)
_sentiment_pipeline = None
_tokenizer = None
_model = None


def get_sentiment_pipeline():
    """Lazy load sentiment analysis pipeline"""
    global _sentiment_pipeline, _tokenizer, _model
    
    if _sentiment_pipeline is None:
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
            
            # Use FinBERT for financial sentiment (best for financial texts)
            model_name = os.getenv("SENTIMENT_MODEL", "ProsusAI/finbert")
            
            print(f"📥 Loading sentiment model: {model_name}")
            _tokenizer = AutoTokenizer.from_pretrained(model_name)
            _model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=_model,
                tokenizer=_tokenizer,
                device=-1  # CPU (change to 0 for GPU)
            )
            
            print(f"✅ Loaded sentiment analysis model")
        except ImportError:
            print("⚠️ transformers not installed. Install with: pip install transformers torch")
            raise
        except Exception as e:
            print(f"❌ Failed to load sentiment model: {e}")
            # Fallback to basic sentiment analysis
            _sentiment_pipeline = None
    
    return _sentiment_pipeline


def analyze_text_sentiment(text: str) -> Dict[str, any]:
    """
    Analyze sentiment of a single text
    
    Returns:
        {
            "label": "positive" | "negative" | "neutral",
            "score": confidence score (0-1),
            "raw_output": model's raw output
        }
    """
    pipeline = get_sentiment_pipeline()
    
    if pipeline is None:
        # Fallback: simple keyword-based sentiment
        return _fallback_sentiment(text)
    
    try:
        # Truncate text if too long (max 512 tokens for BERT models)
        max_length = 510
        if len(text.split()) > max_length:
            text = " ".join(text.split()[:max_length])
        
        result = pipeline(text)[0]
        
        # Normalize label (FinBERT uses: positive, negative, neutral)
        label = result["label"].lower()
        score = float(result["score"])
        
        return {
            "label": label,
            "score": score,
            "confidence": score,
            "raw_output": result
        }
    except Exception as e:
        print(f"⚠️ Sentiment analysis error: {e}")
        return _fallback_sentiment(text)


def _fallback_sentiment(text: str) -> Dict[str, any]:
    """Fallback keyword-based sentiment analysis"""
    text_lower = text.lower()
    
    positive_keywords = [
        "bullish", "surge", "rally", "gains", "profit", "growth", "positive",
        "outperform", "beat", "strong", "upgrade", "buy", "soar", "jump"
    ]
    
    negative_keywords = [
        "bearish", "crash", "decline", "loss", "negative", "drop", "fall",
        "downgrade", "sell", "plunge", "weak", "miss", "disappointing"
    ]
    
    pos_count = sum(1 for word in positive_keywords if word in text_lower)
    neg_count = sum(1 for word in negative_keywords if word in text_lower)
    
    if pos_count > neg_count:
        return {"label": "positive", "score": 0.6, "confidence": 0.6, "method": "keyword"}
    elif neg_count > pos_count:
        return {"label": "negative", "score": 0.6, "confidence": 0.6, "method": "keyword"}
    else:
        return {"label": "neutral", "score": 0.5, "confidence": 0.5, "method": "keyword"}


def aggregate_sentiment(sentiments: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Aggregate multiple sentiment analyses
    
    Returns:
        {
            "overall_sentiment": "positive" | "negative" | "neutral",
            "sentiment_score": -1 to 1 (negative to positive),
            "distribution": {"positive": %, "negative": %, "neutral": %},
            "confidence": average confidence
        }
    """
    if not sentiments:
        return {
            "overall_sentiment": "neutral",
            "sentiment_score": 0.0,
            "distribution": {"positive": 0, "negative": 0, "neutral": 100},
            "confidence": 0.0
        }
    
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    total_confidence = 0.0
    
    for s in sentiments:
        label = s.get("label", "neutral")
        counts[label] = counts.get(label, 0) + 1
        total_confidence += s.get("confidence", 0.5)
    
    total = len(sentiments)
    distribution = {k: (v / total * 100) for k, v in counts.items()}
    avg_confidence = total_confidence / total
    
    # Calculate sentiment score (-1 to 1)
    sentiment_score = (
        (counts["positive"] - counts["negative"]) / total
    )
    
    # Determine overall sentiment
    if sentiment_score > 0.2:
        overall = "positive"
    elif sentiment_score < -0.2:
        overall = "negative"
    else:
        overall = "neutral"
    
    return {
        "overall_sentiment": overall,
        "sentiment_score": round(sentiment_score, 3),
        "distribution": {k: round(v, 1) for k, v in distribution.items()},
        "confidence": round(avg_confidence, 3),
        "sample_size": total
    }


# Create MCP server
mcp = FastMCP("Sentiment Analysis for Financial Trading")


@mcp.tool()
def analyze_sentiment(text: str) -> Dict[str, any]:
    """
    Analyze sentiment of financial text (news, social media, reports)
    
    Args:
        text: Text to analyze (news headline, article, tweet, etc.)
    
    Returns:
        Sentiment analysis result with label and confidence score
    
    Examples:
        analyze_sentiment("Tech stocks surge on strong earnings reports")
        analyze_sentiment("Market crashes amid inflation concerns")
    """
    try:
        result = analyze_text_sentiment(text)
        result["timestamp"] = datetime.now().isoformat()
        result["text_length"] = len(text)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "label": "neutral",
            "score": 0.0
        }


@mcp.tool()
def analyze_batch_sentiment(texts: List[str]) -> Dict[str, any]:
    """
    Analyze sentiment of multiple texts and provide aggregate analysis
    
    Args:
        texts: List of texts to analyze
    
    Returns:
        Individual sentiments + aggregate sentiment analysis
    
    Examples:
        analyze_batch_sentiment([
            "NVDA beats earnings expectations",
            "Market shows strong bullish momentum",
            "Tech sector leads market gains"
        ])
    """
    try:
        individual_results = []
        
        for text in texts:
            result = analyze_text_sentiment(text)
            result["text"] = text[:100]  # Include truncated text
            individual_results.append(result)
        
        aggregate = aggregate_sentiment(individual_results)
        
        return {
            "individual_sentiments": individual_results,
            "aggregate": aggregate,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "individual_sentiments": [],
            "aggregate": {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0
            }
        }


@mcp.tool()
def analyze_symbol_sentiment(symbol: str, texts: List[str]) -> Dict[str, any]:
    """
    Analyze sentiment for a specific stock symbol from multiple sources
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "NVDA")
        texts: List of news/social media texts about the symbol
    
    Returns:
        Symbol-specific sentiment analysis with recommendation
    
    Examples:
        analyze_symbol_sentiment("NVDA", [
            "NVIDIA announces new AI chip breakthrough",
            "NVDA stock reaches new all-time high",
            "Analysts upgrade NVDA price target"
        ])
    """
    try:
        # Analyze each text
        sentiments = []
        for text in texts:
            result = analyze_text_sentiment(text)
            sentiments.append(result)
        
        # Aggregate
        aggregate = aggregate_sentiment(sentiments)
        
        # Generate trading signal based on sentiment
        score = aggregate["sentiment_score"]
        confidence = aggregate["confidence"]
        
        if score > 0.3 and confidence > 0.6:
            signal = "BULLISH"
            recommendation = "Consider buying opportunities"
        elif score < -0.3 and confidence > 0.6:
            signal = "BEARISH"
            recommendation = "Consider selling or avoiding"
        else:
            signal = "NEUTRAL"
            recommendation = "Monitor closely, no strong signal"
        
        return {
            "symbol": symbol,
            "sentiment_analysis": aggregate,
            "trading_signal": signal,
            "recommendation": recommendation,
            "sources_analyzed": len(texts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "symbol": symbol,
            "error": str(e),
            "trading_signal": "NEUTRAL",
            "recommendation": "Unable to analyze sentiment"
        }


@mcp.tool()
def get_market_sentiment_summary(news_items: List[Dict[str, str]]) -> Dict[str, any]:
    """
    Analyze overall market sentiment from multiple news items
    
    Args:
        news_items: List of dicts with {"title": str, "description": str, "symbol": str}
    
    Returns:
        Overall market sentiment with symbol breakdown
    
    Examples:
        get_market_sentiment_summary([
            {"title": "Tech stocks rally", "description": "...", "symbol": "TECH"},
            {"title": "Banks face pressure", "description": "...", "symbol": "FINANCIALS"}
        ])
    """
    try:
        all_texts = []
        symbol_sentiments = {}
        
        for item in news_items:
            text = f"{item.get('title', '')} {item.get('description', '')}".strip()
            if text:
                all_texts.append(text)
                
                symbol = item.get("symbol", "UNKNOWN")
                sentiment = analyze_text_sentiment(text)
                
                if symbol not in symbol_sentiments:
                    symbol_sentiments[symbol] = []
                symbol_sentiments[symbol].append(sentiment)
        
        # Overall market sentiment
        overall_sentiments = [analyze_text_sentiment(t) for t in all_texts]
        market_aggregate = aggregate_sentiment(overall_sentiments)
        
        # Per-symbol aggregates
        symbol_analysis = {}
        for symbol, sentiments in symbol_sentiments.items():
            symbol_analysis[symbol] = aggregate_sentiment(sentiments)
        
        return {
            "market_sentiment": market_aggregate,
            "symbol_breakdown": symbol_analysis,
            "total_news_analyzed": len(news_items),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "market_sentiment": {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0
            }
        }


if __name__ == "__main__":
    # Test the sentiment analysis
    print("🧪 Testing Sentiment Analysis Tool\n")
    
    test_texts = [
        "NVIDIA announces breakthrough in AI chip technology, stock soars 15%",
        "Market crashes amid fears of economic recession",
        "Tech stocks show mixed performance in volatile trading session",
        "Apple beats earnings expectations, announces new product lineup",
        "Banking sector faces pressure from regulatory concerns"
    ]
    
    print("Individual sentiment analysis:")
    for text in test_texts:
        result = analyze_sentiment(text)
        print(f"  [{result['label'].upper()}] ({result['score']:.2f}) {text[:60]}...")
    
    print("\nBatch analysis:")
    batch_result = analyze_batch_sentiment(test_texts)
    agg = batch_result["aggregate"]
    print(f"  Overall: {agg['overall_sentiment'].upper()}")
    print(f"  Score: {agg['sentiment_score']}")
    print(f"  Distribution: {agg['distribution']}")
    
    print("\n🚀 Starting MCP server on port 8006...")
    mcp.run(transport="streamable_http", port=int(os.getenv("SENTIMENT_HTTP_PORT", "8006")))
