"""
Market Analyst Node - Analyzes market data and calculates probabilities
"""
from langchain_core.messages import AIMessage

from app.llm import get_llm
from app.agents.state import ResearchState
from app.agents.tools.analysis_tools import (
    calculate_implied_probability,
    calculate_expected_value,
    format_market_summary,
)


ANALYST_SYSTEM_PROMPT = """You are an expert prediction market analyst specializing in Kalshi markets.
Analyze the provided market data and give insights on:
1. Implied probabilities from current prices
2. Volume and liquidity assessment  
3. Market sentiment indicators
4. Key factors that could affect the outcome

Be concise but thorough. Focus on actionable insights."""


async def market_analyst_node(state: ResearchState) -> ResearchState:
    """
    Market analyst node that analyzes market data and generates insights.
    """
    market_data = state.get("market_data")
    related_markets = state.get("related_markets")
    crypto_data = state.get("crypto_data")
    query = state.get("query", "")
    
    analysis_parts = []
    probability_assessment = None
    
    # Analyze main market if available
    if market_data:
        # Calculate implied probabilities
        yes_bid = market_data.get("yes_bid")
        yes_ask = market_data.get("yes_ask")
        
        if yes_bid and yes_ask:
            mid_price = (yes_bid + yes_ask) / 2
            probability_assessment = calculate_implied_probability(mid_price)
            
            analysis_parts.append(f"**Market: {market_data.get('title', 'Unknown')}**")
            analysis_parts.append(f"- Current Yes price: {yes_bid}¢ bid / {yes_ask}¢ ask")
            analysis_parts.append(f"- Implied probability: {probability_assessment}")
            analysis_parts.append(f"- 24h Volume: {market_data.get('volume_24h', 'N/A')}")
            analysis_parts.append(f"- Open Interest: {market_data.get('open_interest', 'N/A')}")
    
    # Add crypto context if relevant
    if crypto_data:
        btc_price = crypto_data.get("price")
        if btc_price:
            analysis_parts.append(f"\n**Crypto Context:**")
            analysis_parts.append(f"- Current BTC price: ${btc_price:,.2f}")
    
    # Summarize related markets
    if related_markets:
        analysis_parts.append(f"\n**Related/Trending Markets ({len(related_markets)}):**")
        for i, mkt in enumerate(related_markets[:5], 1):
            title = mkt.get("title", "Unknown")[:50]
            volume = mkt.get("volume_24h", 0)
            analysis_parts.append(f"{i}. {title}... (Vol: {volume})")
    
    # Generate LLM analysis if we have data
    llm_analysis = None
    if market_data or related_markets:
        try:
            llm = get_llm(temperature=0.3)
            
            context = "\n".join(analysis_parts) if analysis_parts else "No market data available"
            prompt = f"""Analyze this Kalshi market data for the query: "{query}"

{context}

Provide a brief but insightful analysis covering:
1. Current market sentiment
2. Key price levels and probabilities
3. Factors to watch
"""
            
            response = await llm.ainvoke([
                {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ])
            llm_analysis = response.content
            
        except Exception as e:
            llm_analysis = f"Analysis generation error: {str(e)}"
    
    # Combine all analysis
    full_analysis = "\n".join(analysis_parts)
    if llm_analysis:
        full_analysis += f"\n\n**AI Analysis:**\n{llm_analysis}"
    
    return {
        **state,
        "analysis": full_analysis,
        "probability_assessment": probability_assessment,
        "messages": state.get("messages", []) + [
            AIMessage(content=f"[Market Analyst] Completed analysis"),
        ],
    }
