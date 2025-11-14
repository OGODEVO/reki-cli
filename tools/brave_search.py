"""
This module provides a browsing tool that allows an agent to search the web using the Brave Search API.
"""

import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from bs4 import BeautifulSoup

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

    def search(self, query: str) -> List[str]:
        """
        Performs a web search using the Brave Search API and returns a concise summary.

        Args:
            query: The search query.

        Returns:
            A list of strings, each summarizing a search result.
        """
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        params = {"q": query}
        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            results = response.json().get("web", {}).get("results", [])
            
            # Process and truncate the results
            summaries = []
            for result in results[:5]:  # Limit to top 5 results
                title = result.get("title", "No Title")
                url = result.get("url", "#")
                description = result.get("description", "")
                # Create a concise snippet
                snippet = f"Title: {title}, URL: {url}, Snippet: {description[:300]}..."
                summaries.append(snippet)
            
            return summaries
            
        except requests.exceptions.Timeout:
            return ["Error: The web search timed out after 10 seconds."]
        except requests.exceptions.RequestException as e:
            return [f"Error: An error occurred during the web search: {e}"]

    def open_url(self, url: str) -> str:
        """
        Opens a URL and returns the main content of the webpage.

        Args:
            url: The URL to open.

        Returns:
            The main content of the webpage.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Remove script and style elements
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except requests.exceptions.Timeout:
            return "Error: The request timed out after 10 seconds."
        except requests.exceptions.RequestException as e:
            return f"Error: An error occurred while opening the URL: {e}"

    def get_functions(self):
        return {
            "browser_search": self.search,
            "open_url": self.open_url,
        }

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
            {
                "type": "function",
                "function": {
                    "name": "open_url",
                    "description": "Opens a URL and returns the main content of the webpage.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to open.",
                            },
                        },
                        "required": ["url"],
                    },
                },
            },
        ]
