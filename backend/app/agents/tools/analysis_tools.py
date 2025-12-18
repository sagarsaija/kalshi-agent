"""
Analysis Tools for market calculations and comparisons
"""
from typing import Dict, Any, List, Optional

from langchain_core.tools import tool


def calculate_implied_probability(price_cents: float) -> str:
    """
    Calculate implied probability from a price in cents.
    
    Args:
        price_cents: Price in cents (0-100)
        
    Returns:
        Formatted probability string
    """
    if price_cents is None:
        return "N/A"
    
    probability = price_cents / 100.0
    return f"{probability:.1%}"


def calculate_expected_value(
    probability: float,
    yes_price: float,
    payout: float = 100.0,
) -> Dict[str, float]:
    """
    Calculate expected value for a trade.
    
    Args:
        probability: Your estimated probability (0-1)
        yes_price: Current Yes price in cents
        payout: Payout on win (default 100 cents)
        
    Returns:
        Dict with EV calculations
    """
    cost = yes_price
    win_amount = payout - cost
    
    # EV = (probability * win) - ((1 - probability) * cost)
    ev = (probability * win_amount) - ((1 - probability) * cost)
    ev_percent = (ev / cost) * 100 if cost > 0 else 0
    
    return {
        "cost": cost,
        "potential_win": win_amount,
        "expected_value": round(ev, 2),
        "ev_percent": round(ev_percent, 2),
        "edge": round((probability * 100) - yes_price, 2),
    }


def calculate_kelly_criterion(
    probability: float,
    odds: float,
) -> float:
    """
    Calculate Kelly Criterion bet size.
    
    Args:
        probability: Your estimated probability of winning
        odds: Decimal odds (e.g., 2.0 for even money)
        
    Returns:
        Optimal bet fraction (0-1)
    """
    if odds <= 1 or probability <= 0 or probability >= 1:
        return 0.0
    
    q = 1 - probability
    kelly = (probability * odds - q) / odds
    
    return max(0, min(1, kelly))


def format_market_summary(market: Dict[str, Any]) -> str:
    """
    Format market data into a readable summary.
    
    Args:
        market: Market data dict
        
    Returns:
        Formatted string summary
    """
    lines = []
    
    title = market.get("title", "Unknown Market")
    lines.append(f"**{title}**")
    
    if market.get("subtitle"):
        lines.append(f"_{market['subtitle']}_")
    
    yes_bid = market.get("yes_bid")
    yes_ask = market.get("yes_ask")
    
    if yes_bid and yes_ask:
        mid = (yes_bid + yes_ask) / 2
        spread = yes_ask - yes_bid
        lines.append(f"Yes: {yes_bid}¢ - {yes_ask}¢ (mid: {mid:.1f}¢, spread: {spread}¢)")
        lines.append(f"Implied Prob: {calculate_implied_probability(mid)}")
    
    if market.get("volume_24h"):
        lines.append(f"24h Volume: {market['volume_24h']:,}")
    
    if market.get("open_interest"):
        lines.append(f"Open Interest: {market['open_interest']:,}")
    
    if market.get("status"):
        lines.append(f"Status: {market['status']}")
    
    return "\n".join(lines)


def compare_markets(markets: List[Dict[str, Any]]) -> str:
    """
    Compare multiple markets side by side.
    
    Args:
        markets: List of market data dicts
        
    Returns:
        Formatted comparison string
    """
    if not markets:
        return "No markets to compare"
    
    lines = ["## Market Comparison", ""]
    
    # Header
    lines.append("| Market | Yes Price | Volume | Status |")
    lines.append("|--------|-----------|--------|--------|")
    
    for market in markets:
        title = (market.get("title") or "Unknown")[:30]
        yes_bid = market.get("yes_bid", "N/A")
        yes_ask = market.get("yes_ask", "N/A")
        
        if yes_bid != "N/A" and yes_ask != "N/A":
            price = f"{yes_bid}¢-{yes_ask}¢"
        else:
            price = "N/A"
        
        volume = market.get("volume_24h", "N/A")
        if volume != "N/A":
            volume = f"{volume:,}"
        
        status = market.get("status", "N/A")
        
        lines.append(f"| {title} | {price} | {volume} | {status} |")
    
    return "\n".join(lines)


# LangChain tool wrappers
@tool
def ev_calculator_tool(probability: float, yes_price: float) -> str:
    """
    Calculate expected value for a trade given your probability estimate and current Yes price.
    probability should be 0-1, yes_price in cents (0-100).
    """
    ev = calculate_expected_value(probability, yes_price)
    return f"EV: {ev['expected_value']}¢ ({ev['ev_percent']}%), Edge: {ev['edge']}¢"


@tool
def kelly_tool(probability: float, yes_price: float) -> str:
    """
    Calculate Kelly Criterion bet size for a trade.
    probability should be 0-1, yes_price in cents (0-100).
    """
    odds = 100 / yes_price if yes_price > 0 else 0
    kelly = calculate_kelly_criterion(probability, odds)
    return f"Kelly suggests betting {kelly:.1%} of bankroll"
