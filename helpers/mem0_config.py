# Configuration for Mem0 project setup

# Custom instructions to filter what gets stored in memory for the FX Trading Analyst.
CUSTOM_INSTRUCTIONS = """
Extract from conversations with the user:
- Specific currency pairs the user is interested in (e.g., EUR/USD, GBP/JPY).
- The user's trading strategies, risk tolerance, or portfolio goals.
- Key levels of support or resistance the user has identified.
- User's preferences for specific technical indicators or timeframes.
- Summaries of analysis performed on currency pairs.

Exclude:
- Greetings, farewells, and conversational filler (e.g., "hello", "thanks").
- Casual, non-substantive chatter.
- Any discussion not related to Forex, financial markets, or trading.
- Standalone price points without context.
"""

# Custom categories to organize memories for FX trading.
CUSTOM_CATEGORIES = [
    {
        "name": "currency_pairs",
        "description": "Specific currency pairs that the user is actively trading or monitoring."
    },
    {
        "name": "trading_strategy",
        "description": "The user's defined trading plans, rules, risk management, and overall strategy."
    },
    {
        "name": "market_analysis",
        "description": "Key insights, conclusions, or summaries from technical analysis performed on currency pairs."
    },
    {
        "name": "user_preferences",
        "description": "The user's preferences for indicators, timeframes, or reporting styles."
    }
]