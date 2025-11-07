import requests
import json

class BinanceTool:
    def __init__(self):
        self.api_url = "https://api.binance.us/api/v3"

    def get_latest_price(self, symbol):
        """
        Get the latest price for a specific symbol (e.g., BTCUSDT).
        """
        try:
            response = requests.get(f"{self.api_url}/ticker/price", params={"symbol": symbol})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_latest_binance_price",
                    "description": "Get the latest price for a specific symbol from Binance.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The trading symbol (e.g., BTCUSDT)",
                            }
                        },
                        "required": ["symbol"],
                    },
                },
            }
        ]

    def get_functions(self):
        return {
            "get_latest_binance_price": self.get_latest_price
        }
