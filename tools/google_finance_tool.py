import os
import json
import serpapi

class GoogleFinanceTool:
    def __init__(self):
        self.api_key = os.environ.get("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY environment variable not set.")
        self.client = serpapi.Client()

    def get_functions(self):
        return {
            "get_finance_data": self.get_finance_data,
        }

    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_finance_data",
                    "description": "Fetches real-time financial data, including price and recent news, for a given financial instrument (like a Forex pair or stock ticker).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The financial instrument to look up (e.g., 'USD/JPY', 'EUR/USD', 'AAPL')."
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    def get_finance_data(self, query: str):
        """
        Performs a search on Google Finance using SerpApi and returns a structured result.
        """
        try:
            params = {
                "api_key": self.api_key,
                "engine": "google_finance",
                "q": query
            }
            results = self.client.search(params)
            
            # Extract the most relevant information
            summary = results.get("summary", {})
            news = results.get("news", [])

            # Clean up the news to be more digestible for the LLM
            cleaned_news = [
                {"title": item.get("title"), "source": item.get("source")}
                for item in news[:5] # Limit to the top 5 news items
            ]

            # Structure the final output
            structured_result = {
                "query": query,
                "price": summary.get("price"),
                "change": summary.get("change"),
                "percent_change": summary.get("percent_change"),
                "news": cleaned_news
            }
            
            return structured_result
        except Exception as e:
            return {"error": f"An error occurred while fetching financial data: {e}"}

if __name__ == '__main__':
    # Example usage for testing
    tool = GoogleFinanceTool()
    # Make sure to set your SERPAPI_API_KEY in your environment to test
    data = tool.get_finance_data("USD/JPY")
    print(json.dumps(data, indent=2))
