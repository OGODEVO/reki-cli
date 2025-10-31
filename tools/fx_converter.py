import os
import requests
from typing import Optional

class FXConverterTool:
    def __init__(self):
        self.api_key = os.environ.get("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set.")

    def get_conversion(self, from_currency: str, to_currency: str, amount: Optional[float] = None, precision: Optional[int] = None):
        """
        Retrieve real-time currency conversion rates.
        """
        url = f"{self.base_url}/v1/conversion/{from_currency}/{to_currency}"
        params = {
            "apiKey": self.api_key
        }
        if amount is not None:
            params["amount"] = amount
        if precision is not None:
            params["precision"] = precision

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {e}"}

    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_currency_conversion",
                    "description": "Retrieve real-time currency conversion rates between any two supported currencies.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "from_currency": {
                                "type": "string",
                                "description": "The 'from' symbol of the pair (e.g., USD)."
                            },
                            "to_currency": {
                                "type": "string",
                                "description": "The 'to' symbol of the pair (e.g., EUR)."
                            },
                            "amount": {
                                "type": "number",
                                "description": "The amount to convert."
                            },
                            "precision": {
                                "type": "integer",
                                "description": "The decimal precision of the conversion. Defaults to 2."
                            }
                        },
                        "required": ["from_currency", "to_currency"]
                    }
                }
            }
        ]
