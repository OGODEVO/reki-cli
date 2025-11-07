import os
import requests
import json

class ForexTool:
    def __init__(self):
        self.api_key = os.environ.get("FOREXRATE_API_KEY")
        if not self.api_key:
            raise ValueError("FOREXRATE_API_KEY environment variable not set.")
        self.base_url = "https://api.forexrateapi.com/v1/latest"

    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_forex_rate",
                    "description": "Fetches the latest foreign exchange rate for a given pair of currencies.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "base_currency": {
                                "type": "string",
                                "description": "The base currency (e.g., 'USD')."
                            },
                            "target_currency": {
                                "type": "string",
                                "description": "The target currency to get the rate for (e.g., 'EUR')."
                            }
                        },
                        "required": ["base_currency", "target_currency"]
                    }
                }
            }
        ]

    def get_functions(self):
        return {
            "get_forex_rate": self.get_forex_rate
        }

    def get_forex_rate(self, base_currency: str, target_currency: str):
        """
        Fetches the latest exchange rate from forexrateapi.com.
        """
        try:
            params = {
                'api_key': self.api_key,
                'base': base_currency.upper(),
                'currencies': target_currency.upper()
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                return {"error": f"API returned an error: {data.get('message', 'Unknown error')}"}

            rate = data.get("rates", {}).get(target_currency.upper())
            if rate is None:
                return {"error": f"Rate for {target_currency.upper()} not found in response."}

            structured_result = {
                "base": base_currency.upper(),
                "target": target_currency.upper(),
                "rate": rate,
                "timestamp": data.get("timestamp")
            }
            
            return structured_result
        except requests.exceptions.RequestException as e:
            return {"error": f"An API error occurred: {e}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}

if __name__ == '__main__':
    # Example usage for testing
    tool = ForexTool()
    print(json.dumps(tool.get_forex_rate("USD", "EUR"), indent=2))
