from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.database import get_db
from app.kalshi_client import get_kalshi_client
from app.models import Fill, Settlement

router = APIRouter(prefix="/trades", tags=["trades"])


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


@router.get("/fills")
async def get_fills(
    period: str = Query("all", description="Time period: 1h, 1d, 7d, 30d, all"),
    limit: int = Query(100, ge=1, le=1000),
    cursor: Optional[str] = None,
):
    """Get trade fills (executed orders)."""
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
    
    data = await client.get_fills(limit=limit, cursor=cursor, min_ts=min_ts)
    fills = data.get("fills", [])
    
    # Format fills for frontend
    formatted_fills = []
    for fill in fills:
        created_time = fill.get("created_time")
        if created_time:
            # Handle both string and int timestamps
            if isinstance(created_time, str):
                timestamp = created_time
            else:
                timestamp = datetime.fromtimestamp(created_time / 1000).isoformat()
        else:
            timestamp = None
        
        formatted_fills.append({
            "id": fill.get("trade_id"),
            "ticker": fill.get("ticker"),
            "side": fill.get("side"),  # 'yes' or 'no'
            "action": fill.get("action"),  # 'buy' or 'sell'
            "count": fill.get("count"),
            "yes_price": fill.get("yes_price"),
            "no_price": fill.get("no_price"),
            "created_at": timestamp,
            "is_taker": fill.get("is_taker"),
            "order_id": fill.get("order_id"),
        })
    
    return {
        "fills": formatted_fills,
        "cursor": data.get("cursor"),
        "period": period,
    }


@router.get("/settlements")
async def get_settlements(
    period: str = Query("all", description="Time period: 1h, 1d, 7d, 30d, all"),
    limit: int = Query(100, ge=1, le=1000),
    cursor: Optional[str] = None,
):
    """Get settled positions."""
    client = get_kalshi_client()
    
    data = await client.get_settlements(limit=limit, cursor=cursor)
    settlements = data.get("settlements", [])
    
    # Calculate time range for filtering
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
    
    # Format and filter settlements
    formatted_settlements = []
    for s in settlements:
        settled_time = s.get("settled_time")
        settled_time_ms = parse_timestamp_to_ms(settled_time)
        
        # Filter by period
        if min_ts and settled_time_ms and settled_time_ms < min_ts:
            continue
        
        if settled_time:
            if isinstance(settled_time, str):
                timestamp = settled_time
            else:
                timestamp = datetime.fromtimestamp(settled_time / 1000).isoformat()
        else:
            timestamp = None
        
        # Calculate if won or lost
        market_result = s.get("market_result")  # 'yes' or 'no'
        position_side = "yes" if s.get("yes_count", 0) > 0 else "no"
        is_win = market_result == position_side
        
        revenue = s.get("revenue", 0)
        
        formatted_settlements.append({
            "id": s.get("settlement_id"),
            "ticker": s.get("ticker"),
            "market_result": market_result,
            "yes_count": s.get("yes_count", 0),
            "no_count": s.get("no_count", 0),
            "revenue": revenue,
            "settled_at": timestamp,
            "is_win": is_win,
        })
    
    return {
        "settlements": formatted_settlements,
        "cursor": data.get("cursor"),
        "period": period,
    }


@router.get("/recent")
async def get_recent_trades(limit: int = Query(20, ge=1, le=100)):
    """Get most recent trades for the dashboard."""
    client = get_kalshi_client()
    
    data = await client.get_fills(limit=limit)
    fills = data.get("fills", [])
    
    formatted = []
    for fill in fills:
        created_time = fill.get("created_time")
        if created_time:
            if isinstance(created_time, str):
                timestamp = created_time
            else:
                timestamp = datetime.fromtimestamp(created_time / 1000).isoformat()
        else:
            timestamp = None
        
        # Determine effective price based on side
        side = fill.get("side")
        if side == "yes":
            price = fill.get("yes_price", 0)
        else:
            price = fill.get("no_price", 0)
        
        action = fill.get("action")
        count = fill.get("count", 0)
        cost = price * count
        
        # If selling, cost is positive (received), if buying, cost is negative (spent)
        if action == "sell":
            cost = cost  # received
        else:
            cost = -cost  # spent
        
        formatted.append({
            "id": fill.get("trade_id"),
            "ticker": fill.get("ticker"),
            "side": side,
            "action": action,
            "count": count,
            "price": price,
            "cost": cost,
            "created_at": timestamp,
        })
    
    return {"trades": formatted}
