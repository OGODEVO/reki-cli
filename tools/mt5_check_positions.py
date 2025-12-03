"""
MT5 Check Positions Tool - For Reki agent to monitor open positions
"""
import os
import requests
from typing import Dict, Any, List
from reki.config import config


class MT5CheckPositionsTool:
    """Tool for checking open positions through MT5 API"""
    
    def __init__(self):
        self.mt5_api_url = config.get("trading.mt5.api_url", "http://localhost:8000")
    
    def get_tools(self):
        """Return tool definitions for the agent"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_mt5_positions",
                    "description": "Check all currently open trading positions on MT5. Use this before placing new trades to avoid over-exposure, or to monitor existing positions' profit/loss.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Optional: Filter positions by symbol (e.g., 'EURUSD'). If not provided, returns all positions."
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "close_mt5_position",
                    "description": "Close a specific MT5 position by ticket number. Use this when you've decided to exit a position based on your analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticket": {
                                "type": "integer",
                                "description": "Position ticket number to close (get this from check_mt5_positions)"
                            }
                        },
                        "required": ["ticket"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "close_all_mt5_positions",
                    "description": "Close ALL open positions on MT5. Use with extreme caution - typically only when market conditions require immediate exit from all trades (e.g., major news event, end of trading week).",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_account_balance",
                    "description": "Get current account balance, equity, and margin. Use this to check available funds before opening new trades and to monitor account growth.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]
    
    def get_functions(self):
        """Return function mappings for the agent"""
        return {
            "check_mt5_positions": self.check_positions,
            "close_mt5_position": self.close_position,
            "close_all_mt5_positions": self.close_all_positions,
            "get_account_balance": self.get_account_balance
        }
    
    def check_positions(self, symbol: str = None) -> Dict[str, Any]:
        """
        Check open positions
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            Dict with positions list
        """
        try:
            url = f"{self.mt5_api_url}/positions"
            params = {"symbol": symbol} if symbol else {}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                positions = response.json()
                
                if not positions:
                    return {
                        "success": True,
                        "message": "No open positions",
                        "positions": [],
                        "count": 0,
                        "total_profit": 0
                    }
                
                total_profit = sum(pos.get("profit", 0) for pos in positions)
                
                return {
                    "success": True,
                    "message": f"Found {len(positions)} open position(s)",
                    "positions": positions,
                    "count": len(positions),
                    "total_profit": round(total_profit, 2)
                }
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.text else "No response"
                return {
                    "success": False,
                    "error": f"Failed to fetch positions: {error_detail}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to MT5 API at {self.mt5_api_url}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def close_position(self, ticket: int) -> Dict[str, Any]:
        """
        Close a specific position
        
        Args:
            ticket: Position ticket number
            
        Returns:
            Dict with close result
        """
        try:
            url = f"{self.mt5_api_url}/positions/close/{ticket}"
            
            response = requests.post(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": f"Position {ticket} closed successfully",
                    "ticket": result.get("ticket"),
                    "closed_at": result.get("closed_at"),
                    "profit": result.get("profit")
                }
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.text else "No response"
                return {
                    "success": False,
                    "error": f"Failed to close position: {error_detail}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to MT5 API at {self.mt5_api_url}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def close_all_positions(self) -> Dict[str, Any]:
        """
        Close all open positions
        
        Returns:
            Dict with close all result
        """
        try:
            url = f"{self.mt5_api_url}/positions/close_all"
            
            response = requests.post(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": f"Closed {result.get('closed', 0)} of {result.get('total', 0)} positions",
                    "closed": result.get("closed"),
                    "total": result.get("total"),
                    "errors": result.get("errors")
                }
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.text else "No response"
                return {
                    "success": False,
                    "error": f"Failed to close all positions: {error_detail}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to MT5 API at {self.mt5_api_url}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    def get_account_balance(self) -> Dict[str, Any]:
        """
        Get account balance and equity
        
        Returns:
            Dict with account info
        """
        try:
            url = f"{self.mt5_api_url}/account/info"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "balance": result.get("balance"),
                    "equity": result.get("equity"),
                    "margin": result.get("margin"),
                    "free_margin": result.get("free_margin"),
                    "currency": result.get("currency", "USD")
                }
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.text else "No response"
                return {
                    "success": False,
                    "error": f"Failed to fetch account info: {error_detail}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to MT5 API at {self.mt5_api_url}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
