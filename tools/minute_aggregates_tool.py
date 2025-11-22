import os
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

class MinuteAggregatesTool:
    def __init__(self):
        self.api_key = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"

    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_minute_aggregates",
                    "description": "Fetch historical OHLC aggregates for a Forex pair. Supports custom timeframes (e.g., 1-minute, 5-minute, 1-hour). Returns the last N bars.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pair": {
                                "type": "string",
                                "description": "The currency pair (e.g., 'EUR/USD', 'USD/JPY')."
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of bars to retrieve. Defaults to 60."
                            },
                            "multiplier": {
                                "type": "integer",
                                "description": "The size of the timespan multiplier (e.g., 1, 5, 15). Defaults to 1."
                            },
                            "timespan": {
                                "type": "string",
                                "enum": ["minute", "hour", "day", "week", "month", "quarter", "year"],
                                "description": "The size of the time window. Defaults to 'minute'."
                            }
                        },
                        "required": ["pair"]
                    }
                }
            }
        ]

    def get_functions(self):
        return {
            "get_minute_aggregates": self.get_minute_aggregates
        }

    def get_minute_aggregates(self, pair: str, limit: int = 60, multiplier: int = 1, timespan: str = "minute") -> Dict[str, Any]:
        """
        Fetches historical aggregates for the specified pair using the REST API.
        Supports custom timeframes (e.g. 5 minute, 1 hour).
        """
        if not self.api_key:
            return {"error": "MASSIVE_API_KEY or POLYGON_API_KEY environment variable not set."}

        # Normalize pair format
        clean_pair = pair.upper().replace("/", "").replace("-", "")
        ticker = f"C:{clean_pair}"

        # Calculate time range based on timespan to ensure we cover enough time
        # This is an approximation to ensure we get 'limit' number of bars
        # We'll request a bit more time than strictly necessary
        
        timespan_map = {
            "minute": timedelta(minutes=1),
            "hour": timedelta(hours=1),
            "day": timedelta(days=1),
            "week": timedelta(weeks=1),
            "month": timedelta(days=30),
            "quarter": timedelta(days=90),
            "year": timedelta(days=365)
        }
        
        delta = timespan_map.get(timespan, timedelta(minutes=1))
        total_duration = delta * limit * 2 # Double the duration to be safe (holidays, weekends)
        
        end_time = datetime.now()
        start_time = end_time - total_duration

        from_ts = int(start_time.timestamp() * 1000)
        to_ts = int(end_time.timestamp() * 1000)

        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_ts}/{to_ts}"
        
        params = {
            "adjusted": "true",
            "sort": "desc",
            "limit": limit,
            "apiKey": self.api_key
        }

        try:
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "details": response.text
                }

            data = response.json()

            if "results" not in data or not data["results"]:
                return {
                    "message": f"No data found for {pair} (Ticker: {ticker}). The market might be closed or the pair name is incorrect.",
                    "pair": pair,
                    "params": {"multiplier": multiplier, "timespan": timespan}
                }

            formatted_results = []
            for bar in data["results"]:
                formatted_results.append({
                    "timestamp": datetime.fromtimestamp(bar["t"] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                    "open": bar["o"],
                    "high": bar["h"],
                    "low": bar["l"],
                    "close": bar["c"],
                    "volume": bar.get("v", 0)
                })

            return {
                "pair": pair,
                "timeframe": f"{multiplier} {timespan}",
                "count": len(formatted_results),
                "data": formatted_results
            }

        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}

if __name__ == '__main__':
    # Example usage
    import json
    tool = MinuteAggregatesTool()
    print("Testing get_minute_aggregates for EUR/USD (last 5 minutes)...")
    # Note: You need a valid API key in env vars for this to work
    result = tool.get_minute_aggregates("EUR/USD", limit=5)
    print(json.dumps(result, indent=2))
