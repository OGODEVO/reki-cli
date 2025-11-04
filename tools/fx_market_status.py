import os
import requests

class FXMarketStatusTool:
    def __init__(self):
        self.api_key = os.environ.get("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set.")

    def get_status(self):
        """
        Retrieve the current trading status for the forex market.
        """
        url = f"{self.base_url}/v1/marketstatus/now"
        params = {"apiKey": self.api_key}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            # Return the full, validated JSON response
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            return {"error": f"HTTP error occurred: {http_err.response.status_code} {http_err.response.reason}"}
        except requests.exceptions.RequestException as req_err:
            return {"error": f"API request failed: {req_err}"}

    def get_functions(self):
        return {
            "get_market_status": self.get_status,
        }

    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_market_status",
                    "description": "Retrieve the current trading status for the forex market (e.g., open, closed).",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
