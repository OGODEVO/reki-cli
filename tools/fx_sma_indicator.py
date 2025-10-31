import os
import requests
from typing import Optional

class FXSMAIndicatorTool:
    def __init__(self):
        self.api_key = os.environ.get("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set.")

    def get_sma(self, ticker: str, timespan: str, window: int, series_type: str, adjusted: Optional[bool] = True, order: Optional[str] = "desc"):
        """
        Calculate the Simple Moving Average (SMA) for a forex ticker.
        """
        # Polygon.io uses a specific format for forex tickers
        if not ticker.startswith("C:"):
            ticker = f"C:{ticker}"
            
        url = f"{self.base_url}/v1/indicators/sma/{ticker}"
        params = {
            "apiKey": self.api_key,
            "timespan": timespan,
            "adjusted": "true" if adjusted else "false",
            "window": window,
            "series_type": series_type,
            "order": order
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
                    "name": "get_sma_indicator",
                    "description": "Calculate the Simple Moving Average (SMA) for a forex ticker over a given window.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "The forex ticker pair (e.g., 'EURUSD')."
                            },
                            "timespan": {
                                "type": "string",
                                "description": "The size of the time window (e.g., 'day', 'week', 'month')."
                            },
                            "window": {
                                "type": "integer",
                                "description": "The window size for the SMA (e.g., 50 for a 50-day SMA)."
                            },
                            "series_type": {
                                "type": "string",
                                "description": "The price point to use (e.g., 'open', 'high', 'low', 'close')."
                            },
                            "adjusted": {
                                "type": "boolean",
                                "description": "Whether the results are adjusted for splits. Defaults to true."
                            },
                            "order": {
                                "type": "string",
                                "description": "The order of the results ('asc' or 'desc'). Defaults to 'desc'."
                            }
                        },
                        "required": ["ticker", "timespan", "window", "series_type"]
                    }
                }
            }
        ]
