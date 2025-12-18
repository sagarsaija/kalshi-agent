"""
Data Fetcher Node - Fetches data from Kalshi API and external sources
"""
from typing import Optional
from langchain_core.messages import AIMessage

from app.agents.state import ResearchState
from app.agents.tools.kalshi_tools import (
    parse_kalshi_url,
    get_market_details,
    get_trending_markets,
)
from app.agents.tools.financial_data_tools import (
    get_crypto_snapshot,
)


async def data_fetcher_node(state: ResearchState) -> ResearchState:
    """
    Data fetcher node that retrieves market data from various sources.
    """
    query = state.get("query", "")
    kalshi_url = state.get("kalshi_url")
    ticker = state.get("ticker")
    
    market_data = None
    related_markets = None
    crypto_data = None
    error = None
    
    try:
        # If we have a URL but no ticker, parse it
        if kalshi_url and not ticker:
            ticker, _ = parse_kalshi_url(kalshi_url)
        
        # Fetch market data if we have a ticker
        if ticker:
            market_data = await get_market_details(ticker)
        
        # Check if query is about trending/popular markets
        query_lower = query.lower()
        if any(word in query_lower for word in ["trending", "popular", "hot", "top"]):
            related_markets = await get_trending_markets(limit=10)
        
        # Check if query involves crypto (for Bitcoin price markets, etc.)
        if any(word in query_lower for word in ["bitcoin", "btc", "crypto", "ethereum", "eth"]):
            crypto_data = await get_crypto_snapshot("BTC-USD")
            
    except Exception as e:
        error = f"Data fetch error: {str(e)}"
    
    # Build status message
    status_parts = []
    if market_data:
        status_parts.append(f"Fetched market data for {ticker}")
    if related_markets:
        status_parts.append(f"Found {len(related_markets)} trending markets")
    if crypto_data:
        status_parts.append("Fetched crypto price data")
    if error:
        status_parts.append(error)
    
    status_msg = "; ".join(status_parts) if status_parts else "No data fetched"
    
    return {
        **state,
        "ticker": ticker,
        "market_data": market_data,
        "related_markets": related_markets,
        "crypto_data": crypto_data,
        "error": error,
        "messages": state.get("messages", []) + [
            AIMessage(content=f"[Data Fetcher] {status_msg}"),
        ],
    }
