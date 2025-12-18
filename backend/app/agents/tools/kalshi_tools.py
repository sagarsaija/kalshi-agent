"""
Kalshi API Tools for LangGraph agents
"""
import re
import httpx
from typing import Optional, List, Dict, Any, Tuple

from langchain_core.tools import tool

from app.kalshi_client import get_kalshi_client


def build_kalshi_url(series_ticker: str, event_ticker: str) -> Optional[str]:
    """
    Build a Kalshi website URL from series and event tickers.
    
    Pattern: https://kalshi.com/markets/{series}/{slug}/{event}
    Where slug is derived from series (e.g., kxnhlgame -> nhl-game)
    
    Returns None for multivariate/parlay markets that don't have clean URLs.
    """
    if not series_ticker or not event_ticker:
        return None
    
    # Skip multivariate/combo markets - they don't have clean URLs
    if 'MULTIGAME' in series_ticker.upper() or 'MVE' in series_ticker.upper():
        return None
    
    series_lower = series_ticker.lower()
    event_lower = event_ticker.lower()
    
    # Known series -> slug mappings
    slug_map = {
        'kxnhlgame': 'nhl-game',
        'kxnbagame': 'nba-game',
        'kxnflgame': 'nfl-game',
        'kxmlbgame': 'mlb-game',
        'kxnba': 'nba-championship',
        'kxnhl': 'nhl-championship',
        'kxnfl': 'nfl-championship',
        'kxmlb': 'mlb-championship',
        'kxfeddecision': 'fed-decision',
        'kxbtcd': 'btc-price',
        'kxethd': 'eth-price',
        'kxnflpassyds': 'nfl-passing-yards',
        'kxnflrshyds': 'nfl-rushing-yards',
        'kxnflrec': 'nfl-receptions',
    }
    
    slug = slug_map.get(series_lower)
    
    # If not in map, try to derive it
    if not slug:
        slug = series_lower
        if slug.startswith('kx'):
            slug = slug[2:]
        # Insert hyphen before common suffixes
        for suffix in ['game', 'decision', 'price', 'range']:
            if slug.endswith(suffix) and not slug.endswith(f'-{suffix}'):
                slug = slug[:-len(suffix)] + '-' + suffix
                break
    
    return f"https://kalshi.com/markets/{series_lower}/{slug}/{event_lower}"


def parse_kalshi_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse a Kalshi market URL and extract the ticker and event info."""
    if not url:
        return None, None
    
    # Pattern 1: Full market URL with specific ticker
    match = re.search(r'/markets/([^/]+)/([^/]+)/([^/?]+)', url)
    if match:
        return match.group(3), match.group(1)
    
    # Pattern 2: Event URL without specific ticker
    match = re.search(r'/markets/([^/]+)/[^/]+/?$', url)
    if match:
        return match.group(1), match.group(1)
    
    # Pattern 3: Just event ticker
    match = re.search(r'/markets/([^/]+)/?$', url)
    if match:
        return match.group(1), match.group(1)
    
    return None, None


def extract_search_terms_from_ticker(ticker: str) -> List[str]:
    """
    Extract search terms from a URL ticker slug.
    Returns list of terms to search for (any match).
    """
    if not ticker:
        return []
    
    ticker_lower = ticker.lower()
    terms = []
    
    # NBA team abbreviations -> full names
    nba_teams = {
        'mem': 'memphis',
        'min': 'minnesota',
        'lal': 'lakers',
        'lac': 'clippers',
        'gsw': 'warriors',
        'bos': 'celtics',
        'mia': 'heat',
        'nyk': 'knicks',
        'chi': 'bulls',
        'dal': 'mavericks',
        'hou': 'rockets',
        'phi': '76ers',
        'atl': 'hawks',
        'bkn': 'nets',
        'den': 'nuggets',
        'phx': 'suns',
        'por': 'blazers',
        'sac': 'kings',
        'tor': 'raptors',
        'uta': 'jazz',
        'was': 'wizards',
        'det': 'pistons',
        'ind': 'pacers',
        'mil': 'bucks',
        'nop': 'pelicans',
        'okc': 'thunder',
        'orl': 'magic',
        'sas': 'spurs',
        'cle': 'cavaliers',
        'cha': 'hornets',
    }
    
    # Crypto
    crypto = {'btc': 'bitcoin', 'eth': 'ethereum', 'sol': 'solana'}
    
    # Economic/Political keywords (exact matches to avoid false positives)
    economic = {
        'feddecision': 'fed',
        'fed': 'fed',
        'fomc': 'fed',
        'inflation': 'inflation',
        'cpi': 'cpi',
        'gdp': 'gdp',
        'jobs': 'jobs',
        'unemployment': 'unemployment',
        'trump': 'trump',
        'biden': 'biden',
        'election': 'election',
        'congress': 'congress',
        'senate': 'senate',
        'house': 'house',
    }
    
    # Check for team codes
    for code, name in nba_teams.items():
        if code in ticker_lower:
            terms.append(name)
    
    # Check for crypto
    for code, name in crypto.items():
        if code in ticker_lower:
            terms.append(name)
    
    # Check for economic/political terms
    for code, name in economic.items():
        if code in ticker_lower:
            terms.append(name)
            break  # Only add one economic term to avoid duplicates
    
    return terms


async def get_market_details(ticker: str) -> Optional[Dict[str, Any]]:
    """Fetch market info. First tries direct lookup, then event lookup, then search."""
    client = get_kalshi_client()
    
    # Try direct market lookup first
    try:
        response = await client.get_market(ticker)
        market = response.get("market", {})
        if market:
            series_ticker = None
            event_ticker = market.get("event_ticker")
            if event_ticker:
                try:
                    event_response = await client.get_event(event_ticker)
                    series_ticker = event_response.get("event", {}).get("series_ticker")
                except Exception:
                    pass
            return _format_market(market, series_ticker)
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 404:
            print(f"HTTP error: {e.response.status_code}")
            return None
    except Exception as e:
        print(f"Market lookup error: {type(e).__name__}: {e}")
    
    # Try as event ticker (e.g., KXNBA-26 is an event, not a market)
    print(f"Market {ticker} not found, trying as event...")
    try:
        event_response = await client.get_event(ticker.upper())
        event = event_response.get("event", {})
        if event:
            series_ticker = event.get("series_ticker")
            # Get the top market from this event
            markets_response = await client._request('GET', '/markets', params={
                'event_ticker': ticker.upper(),
                'limit': 10
            })
            markets = markets_response.get("markets", [])
            
            if markets:
                # Sort by volume to get the most popular option
                markets.sort(key=lambda m: m.get("volume_24h") or 0, reverse=True)
                top_market = markets[0]
                
                # Return event-level info with top market's pricing
                return {
                    "ticker": top_market.get("ticker"),
                    "title": event.get("title"),
                    "subtitle": f"{len(markets)} options available",
                    "yes_bid": top_market.get("yes_bid"),
                    "yes_ask": top_market.get("yes_ask"),
                    "no_bid": top_market.get("no_bid"),
                    "no_ask": top_market.get("no_ask"),
                    "volume": sum(m.get("volume") or 0 for m in markets),
                    "volume_24h": sum(m.get("volume_24h") or 0 for m in markets),
                    "open_interest": sum(m.get("open_interest") or 0 for m in markets),
                    "status": top_market.get("status"),
                    "expiration_time": top_market.get("expiration_time"),
                    "result": top_market.get("result"),
                    "category": event.get("category"),
                    "event_ticker": ticker.upper(),
                    "series_ticker": series_ticker,
                    "url": build_kalshi_url(series_ticker, ticker.upper()) if series_ticker else None,
                    "is_event": True,
                    "top_options": [
                        {"title": m.get("title"), "yes_bid": m.get("yes_bid"), "ticker": m.get("ticker")}
                        for m in markets[:5]
                    ],
                }
            
            print(f"Event {ticker} found but has no markets")
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 404:
            print(f"Event lookup HTTP error: {e.response.status_code}")
    except Exception as e:
        print(f"Event lookup error: {type(e).__name__}: {e}")
    
    # Fall back to search by ticker terms
    print(f"Event {ticker} not found, trying search...")
    return await _search_market_by_ticker_terms(ticker)


async def get_event_details(event_ticker: str) -> Optional[Dict[str, Any]]:
    """Fetch event info with all its markets."""
    try:
        client = get_kalshi_client()
        
        event_response = await client.get_event(event_ticker.upper())
        event = event_response.get("event", {})
        if not event:
            return None
        
        series_ticker = event.get("series_ticker")
        
        # Get all markets for this event
        markets_response = await client._request('GET', '/markets', params={
            'event_ticker': event_ticker.upper(),
            'limit': 50
        })
        markets = markets_response.get("markets", [])
        markets.sort(key=lambda m: m.get("yes_bid") or 0, reverse=True)
        
        return {
            "event_ticker": event_ticker.upper(),
            "title": event.get("title"),
            "category": event.get("category"),
            "series_ticker": series_ticker,
            "url": build_kalshi_url(series_ticker, event_ticker.upper()) if series_ticker else None,
            "markets": [
                {
                    "ticker": m.get("ticker"),
                    "title": m.get("title"),
                    "yes_bid": m.get("yes_bid"),
                    "yes_ask": m.get("yes_ask"),
                    "volume_24h": m.get("volume_24h"),
                }
                for m in markets
            ],
            "total_volume_24h": sum(m.get("volume_24h") or 0 for m in markets),
        }
        
    except Exception as e:
        print(f"Event details error: {type(e).__name__}: {e}")
        return None


def _format_market(market: dict, series_ticker: str = None) -> dict:
    """Format market data into standard response."""
    event_ticker = market.get("event_ticker", "")
    
    # Build URL if we have series_ticker
    url = None
    if series_ticker and event_ticker:
        url = build_kalshi_url(series_ticker, event_ticker)
    
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
        "event_ticker": event_ticker,
        "series_ticker": series_ticker,
        "url": url,
    }


async def _search_market_by_ticker_terms(ticker: str) -> Optional[Dict[str, Any]]:
    """Fallback: search for market by extracted terms."""
    terms = extract_search_terms_from_ticker(ticker)
    
    if not terms:
        print(f"No search terms from ticker: {ticker}")
        return None
    
    print(f"Searching for: {terms}")
    
    try:
        client = get_kalshi_client()
        response = await client.get_markets(limit=500)
        markets = response.get("markets", [])
        
        # Find markets matching any term, prefer simpler titles
        scored = []
        for market in markets:
            title = (market.get("title") or "").lower()
            
            # Check if any search term is in title
            matches = sum(1 for term in terms if term in title)
            if matches == 0:
                continue
            
            # Score: matches + bonus for simpler markets (fewer commas = simpler)
            complexity_penalty = title.count(',')
            score = matches * 10 - complexity_penalty
            
            # Bonus for being NBA single game (not parlay)
            if 'NBASINGLEGAME' in market.get('ticker', ''):
                score += 5
            
            scored.append((score, market))
        
        if not scored:
            print(f"No markets found for terms: {terms}")
            return None
        
        # Best match
        scored.sort(key=lambda x: (-x[0], len(x[1].get('title', ''))))
        best = scored[0][1]
        
        print(f"Found: {best.get('ticker')} - {best.get('title')[:60]}...")
        
        # Get series_ticker for URL
        series_ticker = None
        event_ticker = best.get("event_ticker")
        if event_ticker:
            try:
                event_response = await client.get_event(event_ticker)
                series_ticker = event_response.get("event", {}).get("series_ticker")
            except Exception:
                pass
        
        return _format_market(best, series_ticker)
        
    except Exception as e:
        print(f"Search error: {type(e).__name__}: {e}")
        return None


def derive_series_ticker(event_ticker: str) -> Optional[str]:
    """Derive series ticker from event ticker by removing the date suffix."""
    if not event_ticker:
        return None
    
    # Pattern: SERIESNAME-DATEINFO (e.g., KXNHLGAME-25DEC17NJVGK -> KXNHLGAME)
    match = re.match(r'^([A-Z]+)-', event_ticker)
    if match:
        return match.group(1)
    
    # For complex tickers, try to extract the base
    parts = event_ticker.split('-')
    if parts:
        return parts[0]
    
    return None


async def get_trending_markets(limit: int = 10, category: str = None) -> List[Dict[str, Any]]:
    """Fetch trending markets sorted by volume from popular series."""
    try:
        client = get_kalshi_client()
        
        # Popular series to fetch from (single-game markets with clean URLs)
        popular_series = [
            'KXNHLGAME', 'KXNBAGAME', 'KXNFLGAME', 
            'KXBTCD', 'KXETHD',  # Crypto
            'KXFEDDECISION',  # Fed
        ]
        
        all_markets = []
        
        # Fetch from each series
        for series in popular_series:
            try:
                response = await client._request('GET', '/markets', params={
                    'series_ticker': series, 
                    'limit': 20
                })
                markets = response.get("markets", [])
                all_markets.extend(markets)
            except Exception:
                continue  # Series might not exist or have no markets
        
        # Also get some general markets as fallback
        try:
            response = await client.get_markets(limit=100)
            # Filter to only non-MVE markets
            for m in response.get("markets", []):
                ticker = m.get("ticker", "")
                if "MULTIGAME" not in ticker and "MVE" not in ticker:
                    all_markets.append(m)
        except Exception:
            pass
        
        # Dedupe by event_ticker (so we don't show both sides of same game)
        seen = set()
        result = []
        
        for m in all_markets:
            event_ticker = m.get("event_ticker", "")
            # Use event_ticker for deduping games, ticker for other markets
            dedup_key = event_ticker if event_ticker else m.get("ticker", "")
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            
            event_ticker = m.get("event_ticker", "")
            series_ticker = derive_series_ticker(event_ticker)
            url = build_kalshi_url(series_ticker, event_ticker)
            
            result.append({
                "ticker": ticker,
                "title": m.get("title"),
                "subtitle": m.get("subtitle"),
                "yes_bid": m.get("yes_bid"),
                "yes_ask": m.get("yes_ask"),
                "volume_24h": m.get("volume_24h"),
                "open_interest": m.get("open_interest"),
                "status": m.get("status"),
                "category": m.get("category"),
                "event_ticker": event_ticker,
                "url": url,
            })
        
        # Sort by volume
        result.sort(key=lambda x: x.get("volume_24h") or 0, reverse=True)
        return result[:limit]
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return []


async def search_markets(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search for markets matching a query."""
    try:
        client = get_kalshi_client()
        response = await client.get_markets(limit=200)
        
        query_lower = query.lower()
        matching = []
        
        for m in response.get("markets", []):
            title = (m.get("title") or "").lower()
            subtitle = (m.get("subtitle") or "").lower()
            
            if query_lower in title or query_lower in subtitle:
                matching.append({
                    "ticker": m.get("ticker"),
                    "title": m.get("title"),
                    "subtitle": m.get("subtitle"),
                    "yes_bid": m.get("yes_bid"),
                    "yes_ask": m.get("yes_ask"),
                    "volume_24h": m.get("volume_24h"),
                    "status": m.get("status"),
                })
        
        return matching[:limit]
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return []


# LangChain tool wrappers
@tool
def parse_url_tool(url: str) -> str:
    """Parse a Kalshi URL and extract the market ticker."""
    ticker, _ = parse_kalshi_url(url)
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
