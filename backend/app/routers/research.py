"""
Research API Router - Endpoints for AI-powered market research
"""
from typing import Optional, List
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.agents import run_research_query
from app.agents.tools.kalshi_tools import (
    parse_kalshi_url,
    get_market_details,
    get_trending_markets,
    search_markets,
)
from app.agents.tools.analysis_tools import (
    calculate_implied_probability,
    calculate_expected_value,
    format_market_summary,
)


router = APIRouter(prefix="/research", tags=["research"])


# Request/Response models
class AnalyzeURLRequest(BaseModel):
    url: str


class ChatRequest(BaseModel):
    query: str
    kalshi_url: Optional[str] = None


class CompareRequest(BaseModel):
    tickers: List[str]


class MarketResponse(BaseModel):
    ticker: str
    title: Optional[str]
    subtitle: Optional[str]
    yes_bid: Optional[float]
    yes_ask: Optional[float]
    no_bid: Optional[float]
    no_ask: Optional[float]
    volume_24h: Optional[int]
    open_interest: Optional[int]
    status: Optional[str]
    implied_probability: Optional[str]


class AnalysisResponse(BaseModel):
    ticker: str
    market: Optional[MarketResponse]
    analysis: str
    research_report: Optional[str]


class ChatResponse(BaseModel):
    query: str
    response: str
    market_data: Optional[dict]
    analysis: Optional[str]


# Endpoints
@router.post("/analyze-url", response_model=AnalysisResponse)
async def analyze_url(request: AnalyzeURLRequest):
    """
    Analyze a Kalshi market URL and provide AI-powered insights.
    """
    # Parse the URL
    ticker = parse_kalshi_url(request.url)
    if not ticker:
        raise HTTPException(status_code=400, detail="Could not parse Kalshi URL")
    
    # Fetch market data
    market_data = await get_market_details(ticker)
    if not market_data:
        raise HTTPException(status_code=404, detail=f"Market {ticker} not found")
    
    # Run research agent
    result = await run_research_query(
        query=f"Analyze the market: {market_data.get('title', ticker)}",
        kalshi_url=request.url,
    )
    
    # Build response
    market_response = None
    if market_data:
        yes_bid = market_data.get("yes_bid")
        yes_ask = market_data.get("yes_ask")
        mid_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else None
        
        market_response = MarketResponse(
            ticker=market_data.get("ticker", ticker),
            title=market_data.get("title"),
            subtitle=market_data.get("subtitle"),
            yes_bid=yes_bid,
            yes_ask=yes_ask,
            no_bid=market_data.get("no_bid"),
            no_ask=market_data.get("no_ask"),
            volume_24h=market_data.get("volume_24h"),
            open_interest=market_data.get("open_interest"),
            status=market_data.get("status"),
            implied_probability=calculate_implied_probability(mid_price) if mid_price else None,
        )
    
    return AnalysisResponse(
        ticker=ticker,
        market=market_response,
        analysis=result.get("analysis", ""),
        research_report=result.get("research_report"),
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the research agent for market analysis and insights.
    """
    result = await run_research_query(
        query=request.query,
        kalshi_url=request.kalshi_url,
    )
    
    return ChatResponse(
        query=request.query,
        response=result.get("research_report", "No response generated"),
        market_data=result.get("market_data"),
        analysis=result.get("analysis"),
    )


@router.get("/trending")
async def get_trending(limit: int = 10):
    """
    Get trending/popular markets sorted by volume.
    """
    markets = await get_trending_markets(limit=limit)
    
    # Enrich with implied probabilities
    result = []
    for market in markets:
        yes_bid = market.get("yes_bid")
        yes_ask = market.get("yes_ask")
        mid_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else None
        
        result.append({
            **market,
            "implied_probability": calculate_implied_probability(mid_price) if mid_price else None,
        })
    
    return {"markets": result, "count": len(result)}


@router.get("/market/{ticker}")
async def get_market(ticker: str):
    """
    Get detailed market information with analysis.
    """
    market_data = await get_market_details(ticker)
    if not market_data:
        raise HTTPException(status_code=404, detail=f"Market {ticker} not found")
    
    # Calculate derived metrics
    yes_bid = market_data.get("yes_bid")
    yes_ask = market_data.get("yes_ask")
    
    metrics = {}
    if yes_bid and yes_ask:
        mid_price = (yes_bid + yes_ask) / 2
        spread = yes_ask - yes_bid
        
        metrics = {
            "mid_price": mid_price,
            "spread": spread,
            "spread_percent": (spread / mid_price * 100) if mid_price > 0 else 0,
            "implied_probability": calculate_implied_probability(mid_price),
        }
    
    return {
        "market": market_data,
        "metrics": metrics,
        "summary": format_market_summary(market_data),
    }


@router.get("/search")
async def search(q: str, limit: int = 20):
    """
    Search for markets matching a query.
    """
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    
    markets = await search_markets(q, limit=limit)
    
    return {"markets": markets, "count": len(markets), "query": q}


@router.post("/compare")
async def compare(request: CompareRequest):
    """
    Compare multiple markets side by side.
    """
    if not request.tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")
    
    if len(request.tickers) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 markets can be compared")
    
    markets = []
    for ticker in request.tickers:
        market_data = await get_market_details(ticker)
        if market_data:
            yes_bid = market_data.get("yes_bid")
            yes_ask = market_data.get("yes_ask")
            mid_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else None
            
            markets.append({
                **market_data,
                "implied_probability": calculate_implied_probability(mid_price) if mid_price else None,
            })
    
    return {
        "markets": markets,
        "count": len(markets),
        "requested": len(request.tickers),
    }


@router.post("/ev-calculator")
async def calculate_ev(probability: float, yes_price: float):
    """
    Calculate expected value for a potential trade.
    """
    if probability < 0 or probability > 1:
        raise HTTPException(status_code=400, detail="Probability must be between 0 and 1")
    
    if yes_price < 0 or yes_price > 100:
        raise HTTPException(status_code=400, detail="Yes price must be between 0 and 100")
    
    ev = calculate_expected_value(probability, yes_price)
    
    return {
        "input": {"probability": probability, "yes_price": yes_price},
        "result": ev,
    }
