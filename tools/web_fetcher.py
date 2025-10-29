"""
This module provides a tool for fetching and summarizing the content of a URL.
"""
from typing import List, Dict, Any

class WebFetcherTool:
    """
    A tool that allows an agent to fetch the content of a URL.
    This is a wrapper around the primitive web_fetch tool.
    """

    def __init__(self):
        """
        Initializes the WebFetcherTool.
        """
        pass

    def fetch(self, url: str) -> str:
        """
        Fetches the content of a URL and returns a summary.
        This method is a placeholder for the actual implementation that
        will call the primitive web_fetch tool. The main loop will
        intercept this and call the actual tool.
        """
        # The actual implementation will be handled by the main loop
        # calling the primitive `web_fetch` tool.
        # This is just a stub to satisfy the tool definition.
        return f"Fetching content from {url}"

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Returns the schema for the url_fetch tool.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "url_fetch",
                    "description": "Fetches the main content of a web page from a given URL. Use this when a user provides a URL to get information from.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to fetch the content from.",
                            },
                        },
                        "required": ["url"],
                    },
                },
            },
        ]
