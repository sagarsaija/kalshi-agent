from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.kalshi_client import get_kalshi_client, KalshiClient
from app.models import Position, PortfolioSnapshot

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def parse_timestamp_to_ms(ts) -> Optional[int]:
    """Convert a timestamp (string or int) to milliseconds since epoch."""
    if ts is None:
        return None
    if isinstance(ts, int):
        return ts
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except ValueError:
            return None
    return None


@router.get("/balance")
async def get_balance():
    """Get current portfolio balance from Kalshi API."""
    client = get_kalshi_client()
    data = await client.get_balance()
    
    # Kalshi returns balance in cents, convert to dollars for display
    return {
        "balance": data.get("balance", 0),  # cash balance in cents
        "portfolio_value": data.get("portfolio_value", 0),  # total value in cents
        "available_balance": data.get("available_balance", 0),
        "bonus_balance": data.get("bonus_balance", 0),
    }


@router.get("/positions")
async def get_positions(db: AsyncSession = Depends(get_db)):
    """Get current open positions."""
    client = get_kalshi_client()
    
    all_positions = []
    cursor = None
    
    while True:
        data = await client.get_positions(limit=100, cursor=cursor)
        positions = data.get("market_positions", [])
        all_positions.extend(positions)
        
        cursor = data.get("cursor")
        if not cursor or not positions:
            break
    
    # Enrich with market info if needed
    enriched_positions = []
    for pos in all_positions:
        enriched_positions.append({
            "ticker": pos.get("ticker"),
            "market_title": pos.get("market_title", ""),
            "position": pos.get("position", 0),  # positive = yes, negative = no
            "market_exposure": pos.get("market_exposure", 0),
            "resting_orders_count": pos.get("resting_orders_count", 0),
            "total_traded": pos.get("total_traded", 0),
            "realized_pnl": pos.get("realized_pnl", 0),
            "fees_paid": pos.get("fees_paid", 0),
        })
    
    return {"positions": enriched_positions, "count": len(enriched_positions)}


@router.get("/history")
async def get_portfolio_history(
    period: str = Query("7d", description="Time period: 1h, 1d, 7d, 30d, all"),
    db: AsyncSession = Depends(get_db),
):
    """Get historical portfolio values."""
    client = get_kalshi_client()
    
    # Calculate time range
    now = datetime.utcnow()
    min_ts = None
    
    if period == "1h":
        min_ts = int((now - timedelta(hours=1)).timestamp() * 1000)
    elif period == "1d":
        min_ts = int((now - timedelta(days=1)).timestamp() * 1000)
    elif period == "7d":
        min_ts = int((now - timedelta(days=7)).timestamp() * 1000)
    elif period == "30d":
        min_ts = int((now - timedelta(days=30)).timestamp() * 1000)
    # "all" means no min_ts
    
    try:
        data = await client.get_portfolio_history(min_ts=min_ts)
        history = data.get("history", [])
    except Exception:
        # Portfolio history endpoint may not be available
        history = []
    
    # Format for charting
    formatted_history = []
    for point in history:
        ts = point.get("ts")
        if ts:
            formatted_history.append({
                "timestamp": datetime.fromtimestamp(ts / 1000).isoformat(),
                "ts": ts,
                "balance": point.get("balance", 0),
                "portfolio_value": point.get("portfolio_value", 0),
                "total_value": point.get("balance", 0) + point.get("portfolio_value", 0),
                "pnl": point.get("pnl", 0),
            })
    
    return {"history": formatted_history, "period": period}


@router.get("/summary")
async def get_summary(
    period: str = Query("all", description="Time period: 1h, 1d, 7d, 30d, all"),
):
    """Get portfolio summary with key stats."""
    client = get_kalshi_client()
    
    # Get current balance
    balance_data = await client.get_balance()
    
    # Get positions
    positions_data = await client.get_positions(limit=100)
    positions = positions_data.get("market_positions", [])
    
    # Calculate unrealized P/L from positions
    total_unrealized_pnl = sum(p.get("realized_pnl", 0) for p in positions)
    total_exposure = sum(abs(p.get("market_exposure", 0)) for p in positions)
    
    # Get fills for the period to calculate trading stats
    now = datetime.utcnow()
    min_ts = None
    
    if period == "1h":
        min_ts = int((now - timedelta(hours=1)).timestamp() * 1000)
    elif period == "1d":
        min_ts = int((now - timedelta(days=1)).timestamp() * 1000)
    elif period == "7d":
        min_ts = int((now - timedelta(days=7)).timestamp() * 1000)
    elif period == "30d":
        min_ts = int((now - timedelta(days=30)).timestamp() * 1000)
    
    fills_data = await client.get_fills(limit=100, min_ts=min_ts)
    fills = fills_data.get("fills", [])
    
    # Calculate trading stats
    total_volume = sum(abs(f.get("count", 0) * f.get("yes_price", f.get("no_price", 0))) for f in fills)
    trade_count = len(fills)
    
    # Get settlements for realized P/L
    settlements_data = await client.get_settlements(limit=100)
    settlements = settlements_data.get("settlements", [])
    
    # Filter settlements by period
    realized_pnl = 0
    for s in settlements:
        settled_ts = s.get("settled_time")
        settled_ts_ms = parse_timestamp_to_ms(settled_ts)
        if settled_ts_ms:
            if min_ts is None or settled_ts_ms >= min_ts:
                realized_pnl += s.get("revenue", 0)
    
    return {
        "balance": balance_data.get("balance", 0),
        "portfolio_value": balance_data.get("portfolio_value", 0),
        "total_value": balance_data.get("balance", 0) + balance_data.get("portfolio_value", 0),
        "available_balance": balance_data.get("available_balance", 0),
        "open_positions_count": len(positions),
        "total_exposure": total_exposure,
        "unrealized_pnl": total_unrealized_pnl,
        "realized_pnl": realized_pnl,
        "trade_count": trade_count,
        "volume": total_volume,
        "period": period,
    }
