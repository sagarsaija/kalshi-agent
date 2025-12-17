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


def timestamp_to_date_str(ts) -> Optional[str]:
    """Convert a timestamp to YYYY-MM-DD string."""
    if ts is None:
        return None
    if isinstance(ts, int):
        return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None
    return None


async def get_all_fills(client, min_ts: Optional[int] = None) -> list:
    """Fetch all fills, optionally filtered by min timestamp."""
    all_fills = []
    cursor = None
    while True:
        data = await client.get_fills(limit=100, cursor=cursor, min_ts=min_ts)
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


def calculate_cost_basis_by_ticker(fills: list) -> dict:
    """
    Calculate cost basis per ticker from fills.
    Cost basis = money spent on buys - money received from sells (before settlement)
    
    Returns dict: ticker -> cost in cents
    """
    cost_by_ticker = defaultdict(int)
    
    for fill in fills:
        ticker = fill.get("ticker")
        if not ticker:
            continue
        
        count = fill.get("count", 0)
        side = fill.get("side")  # "yes" or "no"
        action = fill.get("action")  # "buy" or "sell"
        
        # Get the price for the side we're trading
        if side == "yes":
            price = fill.get("yes_price", 0)
        else:
            price = fill.get("no_price", 0)
        
        cost = count * price  # in cents
        
        if action == "buy":
            # Buying costs money (negative cash flow)
            cost_by_ticker[ticker] += cost
        else:
            # Selling returns money (positive cash flow, reduces cost basis)
            cost_by_ticker[ticker] -= cost
    
    return dict(cost_by_ticker)


@router.get("/daily-pnl")
async def get_daily_pnl(
    period: str = Query("30d", description="Time period: 1h, 1d, 7d, 30d, all"),
):
    """
    Get daily P/L breakdown for charting.
    
    P/L is calculated as: settlement_revenue - cost_basis
    Where cost_basis comes from fills (buys - sells before settlement)
    """
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
    
    # Get all data (we need all fills to calculate cost basis, not just recent ones)
    all_settlements = await get_all_settlements(client)
    all_fills = await get_all_fills(client)  # Get ALL fills for cost basis calculation
    
    # Calculate cost basis per ticker
    cost_by_ticker = calculate_cost_basis_by_ticker(all_fills)
    
    # Track which tickers have been settled (to avoid double-counting cost basis)
    settled_tickers = set()
    
    # Group settlements by day with proper P/L calculation
    daily_data = defaultdict(lambda: {
        "realized_pnl": 0,
        "settlement_count": 0,
        "wins": 0,
        "losses": 0,
        "trade_count": 0,
        "volume": 0,
    })
    
    for s in all_settlements:
        settled_time = s.get("settled_time")
        if not settled_time:
            continue
        
        settled_time_ms = parse_timestamp_to_ms(settled_time)
        
        # Filter by period
        if min_ts and settled_time_ms and settled_time_ms < min_ts:
            continue
        
        date_str = timestamp_to_date_str(settled_time)
        if not date_str:
            continue
        
        ticker = s.get("ticker")
        revenue = s.get("revenue", 0)  # This is just the payout, not profit
        
        # Calculate true P/L: payout - cost basis
        cost_basis = cost_by_ticker.get(ticker, 0)
        true_pnl = revenue - cost_basis
        
        # Track this ticker as settled
        settled_tickers.add(ticker)
        
        daily_data[date_str]["realized_pnl"] += true_pnl
        daily_data[date_str]["settlement_count"] += 1
        
        if true_pnl > 0:
            daily_data[date_str]["wins"] += 1
        elif true_pnl < 0:
            daily_data[date_str]["losses"] += 1
    
    # Add fill data (volume, trade count) filtered by period
    for fill in all_fills:
        created_time = fill.get("created_time")
        if not created_time:
            continue
        
        created_time_ms = parse_timestamp_to_ms(created_time)
        if min_ts and created_time_ms and created_time_ms < min_ts:
            continue
        
        date_str = timestamp_to_date_str(created_time)
        if not date_str:
            continue
        
        count = fill.get("count", 0)
        side = fill.get("side")
        price = fill.get("yes_price", 0) if side == "yes" else fill.get("no_price", 0)
        
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
            "trade_count": data["trade_count"],
            "volume": data["volume"],
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
    """Get win/loss statistics with proper P/L calculation."""
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
    
    # Get all data
    all_settlements = await get_all_settlements(client)
    all_fills = await get_all_fills(client)
    
    # Calculate cost basis per ticker
    cost_by_ticker = calculate_cost_basis_by_ticker(all_fills)
    
    # Calculate stats with proper P/L
    wins = 0
    losses = 0
    total_win_amount = 0
    total_loss_amount = 0
    
    for s in all_settlements:
        settled_time = s.get("settled_time")
        settled_time_ms = parse_timestamp_to_ms(settled_time)
        if min_ts and settled_time_ms and settled_time_ms < min_ts:
            continue
        
        ticker = s.get("ticker")
        revenue = s.get("revenue", 0)
        cost_basis = cost_by_ticker.get(ticker, 0)
        true_pnl = revenue - cost_basis
        
        if true_pnl > 0:
            wins += 1
            total_win_amount += true_pnl
        elif true_pnl < 0:
            losses += 1
            total_loss_amount += abs(true_pnl)
    
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
    """Get P/L breakdown by market/ticker with proper P/L calculation."""
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
    
    # Get all data
    all_settlements = await get_all_settlements(client)
    all_fills = await get_all_fills(client)
    
    # Calculate cost basis per ticker
    cost_by_ticker = calculate_cost_basis_by_ticker(all_fills)
    
    # Group by ticker with proper P/L
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
        cost_basis = cost_by_ticker.get(ticker, 0)
        true_pnl = revenue - cost_basis
        
        by_ticker[ticker]["pnl"] += true_pnl
        by_ticker[ticker]["count"] += 1
        
        if true_pnl > 0:
            by_ticker[ticker]["wins"] += 1
        elif true_pnl < 0:
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
