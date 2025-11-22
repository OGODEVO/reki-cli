import os
import requests
import json

class CurrencyConversionTool:
    def __init__(self):
        self.api_key = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY")
        if not self.api_key:
            # Fallback or raise error, but for now we will assume it is set or use the one from prompt if we hardcode it (not recommended for prod)
            # Ideally, we raise an error if it's missing.
            # raise ValueError("MASSIVE_API_KEY environment variable not set.")
            pass
        self.base_url = "https://api.massive.com/v1/conversion"

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
                                "description": "The 'from' symbol of the pair (e.g., 'USD')."
                            },
                            "to_currency": {
                                "type": "string",
                                "description": "The 'to' symbol of the pair (e.g., 'CAD')."
                            },
                            "amount": {
                                "type": "number",
                                "description": "The amount to convert. Defaults to 1.0 if not specified."
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

    def get_functions(self):
        return {
            "get_currency_conversion": self.get_currency_conversion
        }

    def get_currency_conversion(self, from_currency: str, to_currency: str, amount: float = 1.0, precision: int = 2):
        """
        Fetches the real-time currency conversion.
        """
        if not self.api_key:
             return {"error": "MASSIVE_API_KEY or POLYGON_API_KEY environment variable not set."}

        url = f"{self.base_url}/{from_currency.upper()}/{to_currency.upper()}"
        params = {
            'amount': amount,
            'precision': precision,
            'apiKey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            return {"error": f"An API error occurred: {e}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}

if __name__ == '__main__':
    # Example usage
    tool = CurrencyConversionTool()
    # You would need to set MASSIVE_API_KEY env var to run this
    print(json.dumps(tool.get_currency_conversion("AUD", "USD", 100), indent=2))
