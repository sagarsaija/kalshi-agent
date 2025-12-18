"""
Coordinator Node - Routes queries to appropriate specialist agents
"""
from langchain_core.messages import HumanMessage, AIMessage

from app.llm import get_llm
from app.agents.state import ResearchState
from app.agents.tools.kalshi_tools import parse_kalshi_url


COORDINATOR_SYSTEM_PROMPT = """You are a research coordinator for Kalshi prediction markets. 
Your job is to analyze user queries and determine the best approach to answer them.

Given a user query, determine:
1. If they provided a Kalshi URL, extract the market ticker
2. What type of analysis they need:
   - data_fetcher: Need to fetch market data, prices, or external financial data
   - market_analyst: Need probability analysis, odds comparison, or market metrics
   - researcher: Need deep research, explanations, or comprehensive reports
   - end: Query is simple and can be answered directly

Respond with a brief routing decision in this format:
ROUTE: [data_fetcher|market_analyst|researcher|end]
REASON: [one sentence explanation]
"""


async def coordinator_node(state: ResearchState) -> ResearchState:
    """
    Coordinator node that analyzes the query and routes to appropriate agents.
    """
    query = state.get("query", "")
    kalshi_url = state.get("kalshi_url")
    
    # Parse URL if provided
    ticker = None
    if kalshi_url:
        ticker = parse_kalshi_url(kalshi_url)
    
    # Determine routing based on query content
    next_node = "researcher"  # Default
    
    # Simple heuristics for routing
    query_lower = query.lower()
    
    if kalshi_url or ticker:
        # URL provided - need to fetch data first
        next_node = "data_fetcher"
    elif any(word in query_lower for word in ["price", "odds", "probability", "chance"]):
        next_node = "data_fetcher"
    elif any(word in query_lower for word in ["compare", "analysis", "evaluate", "assess"]):
        next_node = "market_analyst"
    elif any(word in query_lower for word in ["trending", "popular", "hot", "markets"]):
        next_node = "data_fetcher"
    elif any(word in query_lower for word in ["explain", "what is", "how does", "research"]):
        next_node = "researcher"
    
    # Update state
    return {
        **state,
        "ticker": ticker,
        "next_node": next_node,
        "messages": state.get("messages", []) + [
            HumanMessage(content=f"Research query: {query}"),
        ],
    }
