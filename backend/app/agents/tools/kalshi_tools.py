"""
Kalshi API Tools for LangGraph agents
"""
import re
from typing import Optional, List, Dict, Any

from langchain_core.tools import tool

from app.kalshi_client import get_kalshi_client


def parse_kalshi_url(url: str) -> Optional[str]:
    """
    Parse a Kalshi market URL and extract the ticker.
    
    URL formats:
    - https://kalshi.com/markets/kxbtcd/bitcoin-price-abovebelow/kxbtcd-25dec1722
    - https://kalshi.com/markets/kxbtcd/bitcoin-price-abovebelow
    
    Returns the ticker (e.g., 'kxbtcd-25dec1722') or event ticker (e.g., 'kxbtcd')
    """
    if not url:
        return None
    
    # Pattern 1: Full market URL with specific ticker
    # /markets/{event_ticker}/{event_name}/{ticker}
    match = re.search(r'/markets/[^/]+/[^/]+/([^/?]+)', url)
    if match:
        return match.group(1)
    
    # Pattern 2: Event URL without specific ticker
    # /markets/{event_ticker}/{event_name}
    match = re.search(r'/markets/([^/]+)/[^/]+/?$', url)
    if match:
        return match.group(1)
    
    # Pattern 3: Just event ticker
    # /markets/{event_ticker}
    match = re.search(r'/markets/([^/]+)/?$', url)
    if match:
        return match.group(1)
    
    return None


async def get_market_details(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed market information from Kalshi API.
    
    Args:
        ticker: Market ticker (e.g., 'kxbtcd-25dec1722')
        
    Returns:
        Market data dict or None if not found
    """
    try:
        client = get_kalshi_client()
        response = await client.get_market(ticker)
        
        market = response.get("market", {})
        
        return {
            "ticker": market.get("ticker"),
            "title": market.get("title"),
            "subtitle": market.get("subtitle"),
            "yes_bid": market.get("yes_bid"),
            "yes_ask": market.get("yes_ask"),
            "no_bid": market.get("no_bid"),
            "no_ask": market.get("no_ask"),
            "volume": market.get("volume"),
            "volume_24h": market.get("volume_24h"),
            "open_interest": market.get("open_interest"),
            "status": market.get("status"),
            "expiration_time": market.get("expiration_time"),
            "result": market.get("result"),
            "category": market.get("category"),
            "event_ticker": market.get("event_ticker"),
        }
        
    except Exception as e:
        print(f"Error fetching market {ticker}: {e}")
        return None


async def get_trending_markets(limit: int = 10, category: str = None) -> List[Dict[str, Any]]:
    """
    Fetch trending/popular markets from Kalshi.
    
    Args:
        limit: Maximum number of markets to return
        category: Optional category filter
        
    Returns:
        List of market data dicts
    """
    try:
        client = get_kalshi_client()
        response = await client.get_markets(limit=limit)
        
        markets = response.get("markets", [])
        
        result = []
        for market in markets:
            result.append({
                "ticker": market.get("ticker"),
                "title": market.get("title"),
                "subtitle": market.get("subtitle"),
                "yes_bid": market.get("yes_bid"),
                "yes_ask": market.get("yes_ask"),
                "volume_24h": market.get("volume_24h"),
                "open_interest": market.get("open_interest"),
                "status": market.get("status"),
                "category": market.get("category"),
            })
        
        # Sort by volume for "trending"
        result.sort(key=lambda x: x.get("volume_24h") or 0, reverse=True)
        
        return result[:limit]
        
    except Exception as e:
        print(f"Error fetching trending markets: {e}")
        return []


async def search_markets(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search for markets matching a query.
    
    Args:
        query: Search query
        limit: Maximum results
        
    Returns:
        List of matching markets
    """
    try:
        client = get_kalshi_client()
        # Note: Kalshi API may not have direct search - we fetch and filter
        response = await client.get_markets(limit=100)
        
        markets = response.get("markets", [])
        query_lower = query.lower()
        
        # Filter by query
        matching = []
        for market in markets:
            title = (market.get("title") or "").lower()
            subtitle = (market.get("subtitle") or "").lower()
            
            if query_lower in title or query_lower in subtitle:
                matching.append({
                    "ticker": market.get("ticker"),
                    "title": market.get("title"),
                    "subtitle": market.get("subtitle"),
                    "yes_bid": market.get("yes_bid"),
                    "yes_ask": market.get("yes_ask"),
                    "volume_24h": market.get("volume_24h"),
                    "status": market.get("status"),
                })
        
        return matching[:limit]
        
    except Exception as e:
        print(f"Error searching markets: {e}")
        return []


# LangChain tool wrappers for agent use
@tool
def parse_url_tool(url: str) -> str:
    """Parse a Kalshi URL and extract the market ticker."""
    ticker = parse_kalshi_url(url)
    return ticker if ticker else "Could not parse ticker from URL"


@tool
async def get_market_tool(ticker: str) -> str:
    """Get detailed information about a Kalshi market by ticker."""
    market = await get_market_details(ticker)
    if market:
        return str(market)
    return f"Market {ticker} not found"


@tool
async def search_markets_tool(query: str) -> str:
    """Search for Kalshi markets matching a query."""
    markets = await search_markets(query)
    if markets:
        return str(markets)
    return f"No markets found for query: {query}"
