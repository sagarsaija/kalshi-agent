from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional
from fastapi import APIRouter, Query

from app.kalshi_client import get_kalshi_client

router = APIRouter(prefix="/analytics", tags=["analytics"])


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


@router.get("/daily-pnl")
async def get_daily_pnl(
    period: str = Query("30d", description="Time period: 1h, 1d, 7d, 30d, all"),
):
    """Get daily P/L breakdown for charting."""
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
    
    # Get all settlements for realized P/L
    all_settlements = []
    cursor = None
    while True:
        data = await client.get_settlements(limit=100, cursor=cursor)
        settlements = data.get("settlements", [])
        all_settlements.extend(settlements)
        cursor = data.get("cursor")
        if not cursor or not settlements:
            break
    
    # Group settlements by day
    daily_data = defaultdict(lambda: {
        "realized_pnl": 0,
        "settlement_count": 0,
        "wins": 0,
        "losses": 0,
    })
    
    for s in all_settlements:
        settled_time = s.get("settled_time")
        if not settled_time:
            continue
        
        # Convert to ms timestamp for comparison
        settled_time_ms = parse_timestamp_to_ms(settled_time)
        
        # Filter by period
        if min_ts and settled_time_ms and settled_time_ms < min_ts:
            continue
        
        # Convert to date
        if isinstance(settled_time, int):
            date_str = datetime.fromtimestamp(settled_time / 1000).strftime("%Y-%m-%d")
        else:
            date_str = datetime.fromisoformat(settled_time.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        
        revenue = s.get("revenue", 0)
        daily_data[date_str]["realized_pnl"] += revenue
        daily_data[date_str]["settlement_count"] += 1
        
        if revenue > 0:
            daily_data[date_str]["wins"] += 1
        elif revenue < 0:
            daily_data[date_str]["losses"] += 1
    
    # Get all fills for trading volume
    all_fills = []
    cursor = None
    while True:
        data = await client.get_fills(limit=100, cursor=cursor, min_ts=min_ts)
        fills = data.get("fills", [])
        all_fills.extend(fills)
        cursor = data.get("cursor")
        if not cursor or not fills:
            break
    
    # Add fill data to daily breakdown
    for fill in all_fills:
        created_time = fill.get("created_time")
        if not created_time:
            continue
        
        if isinstance(created_time, int):
            date_str = datetime.fromtimestamp(created_time / 1000).strftime("%Y-%m-%d")
        else:
            date_str = datetime.fromisoformat(created_time.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        
        count = fill.get("count", 0)
        side = fill.get("side")
        price = fill.get("yes_price", 0) if side == "yes" else fill.get("no_price", 0)
        
        if "trade_count" not in daily_data[date_str]:
            daily_data[date_str]["trade_count"] = 0
            daily_data[date_str]["volume"] = 0
        
        daily_data[date_str]["trade_count"] += 1
        daily_data[date_str]["volume"] += count * price
    
    # Convert to sorted list
    result = []
    for date_str in sorted(daily_data.keys()):
        data = daily_data[date_str]
        result.append({
            "date": date_str,
            "realized_pnl": data["realized_pnl"],
            "settlement_count": data["settlement_count"],
            "wins": data["wins"],
            "losses": data["losses"],
            "trade_count": data.get("trade_count", 0),
            "volume": data.get("volume", 0),
        })
    
    return {"daily_pnl": result, "period": period}


@router.get("/cumulative-pnl")
async def get_cumulative_pnl(
    period: str = Query("30d", description="Time period: 1h, 1d, 7d, 30d, all"),
):
    """Get cumulative P/L over time for charting."""
    # Get daily P/L first
    daily_data = await get_daily_pnl(period)
    daily_pnl = daily_data["daily_pnl"]
    
    # Calculate cumulative
    cumulative = []
    running_total = 0
    
    for day in daily_pnl:
        running_total += day["realized_pnl"]
        cumulative.append({
            "date": day["date"],
            "daily_pnl": day["realized_pnl"],
            "cumulative_pnl": running_total,
            "trade_count": day["trade_count"],
        })
    
    return {"cumulative_pnl": cumulative, "period": period}


@router.get("/win-rate")
async def get_win_rate(
    period: str = Query("all", description="Time period: 1h, 1d, 7d, 30d, all"),
):
    """Get win/loss statistics."""
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
    
    # Get all settlements
    all_settlements = []
    cursor = None
    while True:
        data = await client.get_settlements(limit=100, cursor=cursor)
        settlements = data.get("settlements", [])
        all_settlements.extend(settlements)
        cursor = data.get("cursor")
        if not cursor or not settlements:
            break
    
    # Calculate stats
    wins = 0
    losses = 0
    total_win_amount = 0
    total_loss_amount = 0
    
    for s in all_settlements:
        settled_time = s.get("settled_time")
        settled_time_ms = parse_timestamp_to_ms(settled_time)
        if min_ts and settled_time_ms and settled_time_ms < min_ts:
            continue
        
        revenue = s.get("revenue", 0)
        if revenue > 0:
            wins += 1
            total_win_amount += revenue
        elif revenue < 0:
            losses += 1
            total_loss_amount += abs(revenue)
    
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0
    avg_win = (total_win_amount / wins) if wins > 0 else 0
    avg_loss = (total_loss_amount / losses) if losses > 0 else 0
    
    return {
        "wins": wins,
        "losses": losses,
        "total": total,
        "win_rate": round(win_rate, 2),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "net_pnl": total_win_amount - total_loss_amount,
        "period": period,
    }


@router.get("/market-breakdown")
async def get_market_breakdown(
    period: str = Query("all", description="Time period: 1h, 1d, 7d, 30d, all"),
):
    """Get P/L breakdown by market/ticker."""
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
    
    # Get all settlements
    all_settlements = []
    cursor = None
    while True:
        data = await client.get_settlements(limit=100, cursor=cursor)
        settlements = data.get("settlements", [])
        all_settlements.extend(settlements)
        cursor = data.get("cursor")
        if not cursor or not settlements:
            break
    
    # Group by ticker
    by_ticker = defaultdict(lambda: {
        "pnl": 0,
        "wins": 0,
        "losses": 0,
        "count": 0,
    })
    
    for s in all_settlements:
        settled_time = s.get("settled_time")
        settled_time_ms = parse_timestamp_to_ms(settled_time)
        if min_ts and settled_time_ms and settled_time_ms < min_ts:
            continue
        
        ticker = s.get("ticker", "unknown")
        revenue = s.get("revenue", 0)
        
        by_ticker[ticker]["pnl"] += revenue
        by_ticker[ticker]["count"] += 1
        
        if revenue > 0:
            by_ticker[ticker]["wins"] += 1
        elif revenue < 0:
            by_ticker[ticker]["losses"] += 1
    
    # Convert to sorted list (by P/L)
    result = []
    for ticker, data in by_ticker.items():
        total = data["wins"] + data["losses"]
        result.append({
            "ticker": ticker,
            "pnl": data["pnl"],
            "wins": data["wins"],
            "losses": data["losses"],
            "count": data["count"],
            "win_rate": round((data["wins"] / total * 100) if total > 0 else 0, 2),
        })
    
    # Sort by absolute P/L
    result.sort(key=lambda x: abs(x["pnl"]), reverse=True)
    
    return {"breakdown": result, "period": period}
