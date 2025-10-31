import os
import requests
from typing import Optional

class FXMarketSummaryTool:
    def __init__(self):
        self.api_key = os.environ.get("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set.")

    def get_daily_summary(self, date: str, adjusted: Optional[bool] = True):
        """
        Retrieve daily OHLC, volume, and VWAP data for all forex tickers.
        """
        url = f"{self.base_url}/v2/aggs/grouped/locale/global/market/fx/{date}"
        params = {
            "apiKey": self.api_key,
            "adjusted": "true" if adjusted else "false"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {e}"}

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
                                "description": "The date for the aggregate window (e.g., '2023-10-27')."
                            },
                            "adjusted": {
                                "type": "boolean",
                                "description": "Whether the results are adjusted for splits. Defaults to true."
                            }
                        },
                        "required": ["date"]
                    }
                }
            }
        ]
