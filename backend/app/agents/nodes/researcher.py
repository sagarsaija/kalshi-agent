"""
Researcher Node - Generates comprehensive research reports
"""
from langchain_core.messages import AIMessage

from app.llm import get_llm
from app.agents.state import ResearchState


RESEARCHER_SYSTEM_PROMPT = """You are an expert research analyst specializing in prediction markets, 
particularly Kalshi. You provide comprehensive, well-reasoned analysis based on market data, 
probability theory, and current events.

Your research should be:
1. Data-driven when data is available
2. Clearly structured with key takeaways
3. Honest about uncertainties and limitations
4. Actionable with specific insights

When analyzing prediction markets, consider:
- Historical accuracy of similar markets
- Key events or catalysts that could affect outcomes
- Market liquidity and efficiency
- Potential biases in market pricing
"""


async def researcher_node(state: ResearchState) -> ResearchState:
    """
    Researcher node that generates comprehensive research reports.
    """
    query = state.get("query", "")
    market_data = state.get("market_data")
    analysis = state.get("analysis")
    probability_assessment = state.get("probability_assessment")
    crypto_data = state.get("crypto_data")
    related_markets = state.get("related_markets")
    error = state.get("error")
    
    # Build context for the LLM
    context_parts = []
    
    if market_data:
        context_parts.append(f"**Target Market:**")
        context_parts.append(f"- Title: {market_data.get('title', 'Unknown')}")
        context_parts.append(f"- Ticker: {market_data.get('ticker', 'Unknown')}")
        context_parts.append(f"- Status: {market_data.get('status', 'Unknown')}")
        if market_data.get('yes_bid'):
            context_parts.append(f"- Yes Price: {market_data.get('yes_bid')}¢ - {market_data.get('yes_ask')}¢")
        context_parts.append(f"- Volume 24h: {market_data.get('volume_24h', 'N/A')}")
        context_parts.append("")
    
    if analysis:
        context_parts.append("**Previous Analysis:**")
        context_parts.append(analysis)
        context_parts.append("")
    
    if crypto_data:
        context_parts.append(f"**Crypto Data:**")
        context_parts.append(f"- BTC Price: ${crypto_data.get('price', 'N/A'):,.2f}")
        context_parts.append("")
    
    if related_markets:
        context_parts.append(f"**Related Markets ({len(related_markets)}):**")
        for mkt in related_markets[:3]:
            context_parts.append(f"- {mkt.get('title', 'Unknown')[:60]}")
        context_parts.append("")
    
    if error:
        context_parts.append(f"**Note:** {error}")
        context_parts.append("")
    
    context = "\n".join(context_parts) if context_parts else "No additional context available."
    
    # Generate research report
    try:
        llm = get_llm(temperature=0.5)
        
        prompt = f"""Research Query: {query}

Available Data and Context:
{context}

Please provide a comprehensive research response that addresses the user's query. 
Include:
1. Direct answer to the query
2. Supporting analysis and reasoning
3. Key factors and considerations
4. Potential risks or uncertainties
5. Actionable insights or recommendations

If analyzing a specific market, include probability assessments and market dynamics."""
        
        response = await llm.ainvoke([
            {"role": "system", "content": RESEARCHER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        
        research_report = response.content
        
    except Exception as e:
        research_report = f"Research generation error: {str(e)}\n\nBased on available data:\n{context}"
    
    return {
        **state,
        "research_report": research_report,
        "messages": state.get("messages", []) + [
            AIMessage(content=research_report),
        ],
    }
