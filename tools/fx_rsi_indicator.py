import os
import requests
from typing import Optional

class FXRSIIndicatorTool:
    def __init__(self):
        self.api_key = os.environ.get("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set.")

    def get_rsi(self, ticker: str, timespan: str, window: int = 14, series_type: str = "close", adjusted: Optional[bool] = True, order: Optional[str] = "desc"):
        """
        Calculate the Relative Strength Index (RSI) for a forex ticker.
        """
        if not ticker.startswith("C:"):
            ticker = f"C:{ticker}"
            
        url = f"{self.base_url}/v1/indicators/rsi/{ticker}"
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
                    "name": "get_rsi_indicator",
                    "description": "Calculate the Relative Strength Index (RSI) for a forex ticker to identify overbought or oversold conditions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "The forex ticker pair (e.g., 'EURUSD')."
                            },
                            "timespan": {
                                "type": "string",
                                "description": "The size of the time window (e.g., 'day', 'week')."
                            },
                            "window": {
                                "type": "integer",
                                "description": "The window size for the RSI. Defaults to 14."
                            },
                            "series_type": {
                                "type": "string",
                                "description": "The price point to use (e.g., 'close'). Defaults to 'close'."
                            },
                            "adjusted": {
                                "type": "boolean",
                                "description": "Whether the results are adjusted. Defaults to true."
                            },
                            "order": {
                                "type": "string",
                                "description": "The order of the results ('asc' or 'desc'). Defaults to 'desc'."
                            }
                        },
                        "required": ["ticker", "timespan"]
                    }
                }
            }
        ]
