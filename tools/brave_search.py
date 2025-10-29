"""
This module provides a browsing tool that allows an agent to search the web using the Brave Search API.
"""

import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class BrowserTool:
    """
    A tool that allows an agent to search the web using the Brave Search API.
    """

    def __init__(self):
        """
        Initializes the BrowserTool.
        The Brave API key is read from the BRAVE_API_KEY environment variable.
        """
        self.api_key = os.getenv("BRAVE_API_KEY")
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Performs a web search using the Brave Search API.

        Args:
            query: The search query.

        Returns:
            A list of dictionaries, where each dictionary represents a search result.
        """
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        params = {"q": query}
        response = requests.get(self.base_url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json().get("web", {}).get("results", [])

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Returns a list of tools that can be used by an agent.
        Each tool is represented by a dictionary that describes the tool's schema.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "browser_search",
                    "description": "Performs a web search using the Brave Search API to find up-to-date information on sports games, player stats, or any other relevant topic. Returns a list of search results.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query.",
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
        ]
