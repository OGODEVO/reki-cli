import os
import requests
import json

class DailyMarketTool:
    def __init__(self):
        self.api_key = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY")
        if not self.api_key:
            # Fallback or raise error, but for now we will assume it is set or use the one from prompt if we hardcode it (not recommended for prod)
            # Ideally, we raise an error if it's missing.
            # raise ValueError("MASSIVE_API_KEY environment variable not set.")
            pass
        self.base_url = "https://api.massive.com/v2/aggs/grouped/locale/global/market/fx"

    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_daily_market_summary",
                    "description": "Retrieve daily OHLC (open, high, low, close), volume, and VWAP data for all forex tickers on a specified trading date.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "The date to retrieve data for, in YYYY-MM-DD format."
                            },
                            "pair": {
                                "type": "string",
                                "description": "Optional. The currency pair to filter by (e.g., 'EUR/USD', 'USDJPY')."
                            }
                        },
                        "required": ["date"]
                    }
                }
            }
        ]

    def get_functions(self):
        return {
            "get_daily_market_summary": self.get_daily_market_summary
        }

    def get_daily_market_summary(self, date: str, pair: str = None):
        """
        Fetches the daily market summary for the given date, optionally filtered by a currency pair.
        """
        if not self.api_key:
             return {"error": "MASSIVE_API_KEY environment variable not set."}

        url = f"{self.base_url}/{date}"
        params = {
            'adjusted': 'true',
            'apiKey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if pair and "results" in data:
                # Normalize pair format: remove slash, uppercase, prepend 'C:' if not present
                # The API returns tickers like "C:EURUSD"
                normalized_pair = pair.upper().replace("/", "").replace("-", "")
                if not normalized_pair.startswith("C:"):
                    normalized_pair = f"C:{normalized_pair}"
                
                filtered_results = [
                    item for item in data["results"] 
                    if item.get("T") == normalized_pair
                ]
                
                if not filtered_results:
                     return {"message": f"No data found for pair {pair} on {date}. Available tickers example: {data['results'][0].get('T') if data['results'] else 'None'}"}
                
                data["results"] = filtered_results
                data["resultsCount"] = len(filtered_results) # Update count to reflect filtering

            return data

        except requests.exceptions.RequestException as e:
            return {"error": f"An API error occurred: {e}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}

if __name__ == '__main__':
    # Example usage
    tool = DailyMarketTool()
    # You would need to set MASSIVE_API_KEY env var to run this
    print(json.dumps(tool.get_daily_market_summary("2023-01-09"), indent=2))
