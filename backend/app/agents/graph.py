"""
LangGraph Research Agent Graph Definition
"""
from typing import Literal
from langgraph.graph import StateGraph, END

from .state import ResearchState
from .nodes import coordinator, data_fetcher, market_analyst, researcher


def route_after_coordinator(state: ResearchState) -> Literal["data_fetcher", "researcher", "__end__"]:
    """Route based on coordinator's decision."""
    next_node = state.get("next_node")
    
    if next_node == "data_fetcher":
        return "data_fetcher"
    elif next_node == "researcher":
        return "researcher"
    elif next_node == "end":
        return END
    
    # Default: if we have a URL/ticker, fetch data first
    if state.get("ticker") or state.get("kalshi_url"):
        return "data_fetcher"
    
    # Otherwise go straight to researcher for general queries
    return "researcher"


def route_after_data_fetcher(state: ResearchState) -> Literal["market_analyst", "researcher"]:
    """After fetching data, analyze or research."""
    # If we have market data, analyze it
    if state.get("market_data"):
        return "market_analyst"
    return "researcher"


def create_research_graph() -> StateGraph:
    """Create the research agent graph."""
    
    # Create the graph with our state schema
    graph = StateGraph(ResearchState)
    
    # Add nodes
    graph.add_node("coordinator", coordinator.coordinator_node)
    graph.add_node("data_fetcher", data_fetcher.data_fetcher_node)
    graph.add_node("market_analyst", market_analyst.market_analyst_node)
    graph.add_node("researcher", researcher.researcher_node)
    
    # Set entry point
    graph.set_entry_point("coordinator")
    
    # Add conditional edges from coordinator
    graph.add_conditional_edges(
        "coordinator",
        route_after_coordinator,
        {
            "data_fetcher": "data_fetcher",
            "researcher": "researcher",
            END: END,
        }
    )
    
    # Add conditional edges from data_fetcher
    graph.add_conditional_edges(
        "data_fetcher",
        route_after_data_fetcher,
        {
            "market_analyst": "market_analyst",
            "researcher": "researcher",
        }
    )
    
    # Market analyst always goes to researcher for final synthesis
    graph.add_edge("market_analyst", "researcher")
    
    # Researcher is the final node
    graph.add_edge("researcher", END)
    
    return graph


# Compiled graph instance
_compiled_graph = None


def get_compiled_graph():
    """Get or create the compiled graph."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = create_research_graph()
        _compiled_graph = graph.compile()
    return _compiled_graph


async def run_research_query(query: str, kalshi_url: str = None) -> dict:
    """
    Run a research query through the agent graph.
    
    Args:
        query: The user's research question
        kalshi_url: Optional Kalshi market URL to analyze
        
    Returns:
        Final state with analysis results
    """
    graph = get_compiled_graph()
    
    initial_state: ResearchState = {
        "messages": [],
        "query": query,
        "kalshi_url": kalshi_url,
    }
    
    # Run the graph
    final_state = await graph.ainvoke(initial_state)
    
    return final_state
