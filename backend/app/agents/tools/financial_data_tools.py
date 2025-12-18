"""
FinancialDatasets.ai Tools for external market data
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import httpx
from langchain_core.tools import tool

from app.config import get_settings


FIN_DATASETS_BASE_URL = "https://api.financialdatasets.ai"


async def _make_fin_request(endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
    """Make an authenticated request to FinancialDatasets.ai API."""
    settings = get_settings()
    
    if not settings.fin_dataset_key:
        return None
    
    headers = {
        "X-API-KEY": settings.fin_dataset_key,
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{FIN_DATASETS_BASE_URL}{endpoint}",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()


async def get_crypto_snapshot(ticker: str = "BTC-USD") -> Optional[Dict[str, Any]]:
    """
    Get current crypto price snapshot.
    
    Args:
        ticker: Crypto ticker (e.g., 'BTC-USD', 'ETH-USD')
        
    Returns:
        Price snapshot dict
    """
    try:
        data = await _make_fin_request("/crypto/prices/snapshot/", {"ticker": ticker})
        
        if data and "snapshot" in data:
            snapshot = data["snapshot"]
            return {
                "ticker": ticker,
                "price": snapshot.get("close"),
                "open": snapshot.get("open"),
                "high": snapshot.get("high"),
                "low": snapshot.get("low"),
                "volume": snapshot.get("volume"),
                "time": snapshot.get("time"),
            }
        return None
        
    except Exception as e:
        print(f"Error fetching crypto snapshot for {ticker}: {e}")
        return None


async def get_crypto_prices(
    ticker: str = "BTC-USD",
    interval: str = "day",
    interval_multiplier: int = 1,
    days_back: int = 30,
) -> Optional[List[Dict[str, Any]]]:
    """
    Get historical crypto prices.
    
    Args:
        ticker: Crypto ticker
        interval: Time interval ('minute', 'day', 'week', 'month')
        interval_multiplier: Multiplier for interval
        days_back: Number of days of history
        
    Returns:
        List of price data points
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            "ticker": ticker,
            "interval": interval,
            "interval_multiplier": interval_multiplier,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
        
        data = await _make_fin_request("/crypto/prices/", params)
        
        if data and "prices" in data:
            return [
                {
                    "time": p.get("time"),
                    "open": p.get("open"),
                    "high": p.get("high"),
                    "low": p.get("low"),
                    "close": p.get("close"),
                    "volume": p.get("volume"),
                }
                for p in data["prices"]
            ]
        return None
        
    except Exception as e:
        print(f"Error fetching crypto prices for {ticker}: {e}")
        return None


async def get_stock_snapshot(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get current stock price snapshot.
    
    Args:
        ticker: Stock ticker (e.g., 'AAPL', 'GOOGL')
        
    Returns:
        Price snapshot dict
    """
    try:
        data = await _make_fin_request("/prices/snapshot/", {"ticker": ticker})
        
        if data and "snapshot" in data:
            snapshot = data["snapshot"]
            return {
                "ticker": ticker,
                "price": snapshot.get("close"),
                "open": snapshot.get("open"),
                "high": snapshot.get("high"),
                "low": snapshot.get("low"),
                "volume": snapshot.get("volume"),
                "time": snapshot.get("time"),
            }
        return None
        
    except Exception as e:
        print(f"Error fetching stock snapshot for {ticker}: {e}")
        return None


async def get_stock_prices(
    ticker: str,
    interval: str = "day",
    days_back: int = 30,
) -> Optional[List[Dict[str, Any]]]:
    """
    Get historical stock prices.
    
    Args:
        ticker: Stock ticker
        interval: Time interval
        days_back: Number of days of history
        
    Returns:
        List of price data points
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            "ticker": ticker,
            "interval": interval,
            "interval_multiplier": 1,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
        
        data = await _make_fin_request("/prices/", params)
        
        if data and "prices" in data:
            return [
                {
                    "time": p.get("time"),
                    "open": p.get("open"),
                    "high": p.get("high"),
                    "low": p.get("low"),
                    "close": p.get("close"),
                    "volume": p.get("volume"),
                }
                for p in data["prices"]
            ]
        return None
        
    except Exception as e:
        print(f"Error fetching stock prices for {ticker}: {e}")
        return None


# LangChain tool wrappers
@tool
async def crypto_price_tool(ticker: str = "BTC-USD") -> str:
    """Get current crypto price for a ticker like BTC-USD or ETH-USD."""
    data = await get_crypto_snapshot(ticker)
    if data:
        return f"{ticker}: ${data['price']:,.2f}"
    return f"Could not fetch price for {ticker}"


@tool
async def stock_price_tool(ticker: str) -> str:
    """Get current stock price for a ticker like AAPL or GOOGL."""
    data = await get_stock_snapshot(ticker)
    if data:
        return f"{ticker}: ${data['price']:,.2f}"
    return f"Could not fetch price for {ticker}"
