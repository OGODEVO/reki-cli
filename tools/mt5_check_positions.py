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
            },
            {
                "type": "function",
                "function": {
                    "name": "get_closed_trades",
                    "description": "Get a list of closed trades (deals) for a specified number of days. Useful for analyzing past performance.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back (default: 30)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_trade_history",
                    "description": "Get a list of historical orders for a specified number of days. Shows order placement, cancellation, and execution history.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back (default: 30)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_account_stats",
                    "description": "Get detailed account statistics including balance, equity, margin, free margin, and current profit. Use this to monitor overall account health.",
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
            "close_all_mt5_positions": self.close_all_positions,
            "get_account_balance": self.get_account_balance,
            "get_closed_trades": self.get_closed_trades,
            "get_trade_history": self.get_trade_history,
            "get_account_stats": self.get_account_stats
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
        Get account balance and equity (Legacy wrapper for get_account_stats)
        
        Returns:
            Dict with account info
        """
        return self.get_account_stats()

    def get_account_stats(self) -> Dict[str, Any]:
        """
        Get detailed account statistics
        
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
                    "free_margin": result.get("margin_free"),
                    "margin_level": result.get("margin_level"),
                    "profit": result.get("profit"),
                    "currency": result.get("currency", "USD"),
                    "server": result.get("server"),
                    "login": result.get("login")
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

    def get_closed_trades(self, days: int = 30) -> Dict[str, Any]:
        """
        Get closed trades (deals)
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict with deals list
        """
        try:
            url = f"{self.mt5_api_url}/history/deals"
            params = {"days": days}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                deals = response.json()
                return {
                    "success": True,
                    "count": len(deals),
                    "days": days,
                    "deals": deals
                }
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.text else "No response"
                return {
                    "success": False,
                    "error": f"Failed to fetch closed trades: {error_detail}"
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

    def get_trade_history(self, days: int = 30) -> Dict[str, Any]:
        """
        Get trade history (orders)
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict with orders list
        """
        try:
            url = f"{self.mt5_api_url}/history/orders"
            params = {"days": days}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                orders = response.json()
                return {
                    "success": True,
                    "count": len(orders),
                    "days": days,
                    "orders": orders
                }
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.text else "No response"
                return {
                    "success": False,
                    "error": f"Failed to fetch trade history: {error_detail}"
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
