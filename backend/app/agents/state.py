"""
LangGraph State Schema for Research Agent System
"""
from typing import TypedDict, Annotated, List, Optional, Any
from langgraph.graph.message import add_messages


class MarketData(TypedDict, total=False):
    """Market data structure from Kalshi API."""
    ticker: str
    title: str
    subtitle: Optional[str]
    yes_bid: Optional[float]
    yes_ask: Optional[float]
    no_bid: Optional[float]
    no_ask: Optional[float]
    volume: Optional[int]
    volume_24h: Optional[int]
    open_interest: Optional[int]
    status: Optional[str]
    expiration_time: Optional[str]
    result: Optional[str]
    category: Optional[str]
    event_ticker: Optional[str]


class ResearchState(TypedDict, total=False):
    """State schema for the research agent graph."""
    
    # Conversation messages (auto-accumulates with add_messages)
    messages: Annotated[List[Any], add_messages]
    
    # User query
    query: str
    
    # Extracted from URL if provided
    kalshi_url: Optional[str]
    ticker: Optional[str]
    
    # Fetched market data
    market_data: Optional[MarketData]
    related_markets: Optional[List[MarketData]]
    
    # External data
    crypto_data: Optional[dict]
    financial_data: Optional[dict]
    
    # Analysis results
    analysis: Optional[str]
    probability_assessment: Optional[str]
    research_report: Optional[str]
    
    # Routing
    next_node: Optional[str]
    
    # Error handling
    error: Optional[str]
