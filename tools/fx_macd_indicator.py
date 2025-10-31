import os
import requests
from typing import Optional

class FXMACDIndicatorTool:
    def __init__(self):
        self.api_key = os.environ.get("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set.")

    def get_macd(self, ticker: str, timespan: str, short_window: int = 12, long_window: int = 26, signal_window: int = 9, series_type: str = "close", adjusted: Optional[bool] = True):
        """
        Calculate the Moving Average Convergence Divergence (MACD) for a forex ticker.
        """
        # Polygon.io uses a specific format for forex tickers (e.g., C:USDCAD)
        formatted_ticker = ticker.replace("/", "")
        if not formatted_ticker.startswith("C:"):
            formatted_ticker = f"C:{formatted_ticker}"
            
        url = f"{self.base_url}/v1/indicators/macd/{formatted_ticker}"
        params = {
            "apiKey": self.api_key,
            "timespan": timespan,
            "adjusted": "true" if adjusted else "false",
            "short_window": short_window,
            "long_window": long_window,
            "signal_window": signal_window,
            "series_type": series_type,
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            raw_text = response.text

            # Attempt to parse the JSON response
            try:
                data = response.json()
            except ValueError: # Catches JSONDecodeError
                return {"error": "Failed to decode JSON from API response.", "raw_response": raw_text}

            # Correctly parse the nested response
            if "results" in data and "values" in data["results"]:
                return data["results"]["values"]
            else:
                return {"error": "Invalid API response format", "data": data}
        except requests.exceptions.HTTPError as http_err:
            error_message = f"HTTP error occurred: {http_err}"
            try:
                error_details = response.json()
                error_message += f" - {error_details.get('error', 'No details')}"
            except ValueError:
                error_message += f" - Response content: {response.text}"
            return {"error": error_message}
        except requests.exceptions.RequestException as req_err:
            return {"error": f"API request failed: {req_err}"}

    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_macd_indicator",
                    "description": "Calculate the Moving Average Convergence Divergence (MACD) for a forex ticker.",
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
                            "short_window": {
                                "type": "integer",
                                "description": "The short window size. Defaults to 12."
                            },
                            "long_window": {
                                "type": "integer",
                                "description": "The long window size. Defaults to 26."
                            },
                            "signal_window": {
                                "type": "integer",
                                "description": "The signal window size. Defaults to 9."
                            },
                            "series_type": {
                                "type": "string",
                                "description": "The price point to use (e.g., 'close'). Defaults to 'close'."
                            },
                            "adjusted": {
                                "type": "boolean",
                                "description": "Whether the results are adjusted. Defaults to true."
                            }
                        },
                        "required": ["ticker", "timespan"]
                    }
                }
            }
        ]
