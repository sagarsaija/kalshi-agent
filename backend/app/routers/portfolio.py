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


def calculate_cost_basis_by_ticker(fills: list) -> dict:
    """
    Calculate cost basis per ticker from fills.
    Cost basis = money spent on buys - money received from sells
    """
    from collections import defaultdict
    cost_by_ticker = defaultdict(int)
    
    for fill in fills:
        ticker = fill.get("ticker")
        if not ticker:
            continue
        
        count = fill.get("count", 0)
        side = fill.get("side")
        action = fill.get("action")
        
        price = fill.get("yes_price", 0) if side == "yes" else fill.get("no_price", 0)
        cost = count * price
        
        if action == "buy":
            cost_by_ticker[ticker] += cost
        else:
            cost_by_ticker[ticker] -= cost
    
    return dict(cost_by_ticker)


async def get_all_fills(client) -> list:
    """Fetch all fills."""
    all_fills = []
    cursor = None
    while True:
        data = await client.get_fills(limit=100, cursor=cursor)
        fills = data.get("fills", [])
        all_fills.extend(fills)
        cursor = data.get("cursor")
        if not cursor or not fills:
            break
    return all_fills


async def get_all_settlements(client) -> list:
    """Fetch all settlements."""
    all_settlements = []
    cursor = None
    while True:
        data = await client.get_settlements(limit=100, cursor=cursor)
        settlements = data.get("settlements", [])
        all_settlements.extend(settlements)
        cursor = data.get("cursor")
        if not cursor or not settlements:
            break
    return all_settlements


@router.get("/summary")
async def get_summary(
    period: str = Query("all", description="Time period: 1h, 1d, 7d, 30d, all"),
):
    """Get portfolio summary with key stats and proper P/L calculation."""
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
    
    # Get ALL fills for cost basis calculation
    all_fills = await get_all_fills(client)
    
    # Filter fills by period for volume/trade count
    period_fills = [
        f for f in all_fills
        if min_ts is None or (parse_timestamp_to_ms(f.get("created_time")) or 0) >= min_ts
    ]
    
    # Calculate trading stats
    total_volume = sum(
        abs(f.get("count", 0) * (f.get("yes_price", 0) if f.get("side") == "yes" else f.get("no_price", 0)))
        for f in period_fills
    )
    trade_count = len(period_fills)
    
    # Get all settlements and calculate proper P/L
    all_settlements = await get_all_settlements(client)
    cost_by_ticker = calculate_cost_basis_by_ticker(all_fills)
    
    # Calculate realized P/L with proper cost basis
    realized_pnl = 0
    for s in all_settlements:
        settled_ts = s.get("settled_time")
        settled_ts_ms = parse_timestamp_to_ms(settled_ts)
        if settled_ts_ms:
            if min_ts is None or settled_ts_ms >= min_ts:
                ticker = s.get("ticker")
                revenue = s.get("revenue", 0)
                cost_basis = cost_by_ticker.get(ticker, 0)
                realized_pnl += revenue - cost_basis
    
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
