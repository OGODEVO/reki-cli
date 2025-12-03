"""
MT5 Execute Trade Tool - For Reki agent to execute trades via Windows VPS API
"""
import os
import requests
from typing import Dict, Any
from reki.config import config


class MT5ExecuteTradeTool:
    """Tool for executing trades through MT5 API"""
    
    def __init__(self):
        self.mt5_api_url = config.get("trading.mt5.api_url", "http://localhost:8000")
    
    def get_tools(self):
        """Return tool definitions for the agent"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_mt5_trade",
                    "description": "Execute a BUY or SELL trade on MT5. Use this when you've analyzed the market and decided to enter a position. You MUST specify take_profit and stop_loss for risk management.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["BUY", "SELL"],
                                "description": "Trade direction: BUY (long) or SELL (short)"
                            },
                            "symbol": {
                                "type": "string",
                                "description": "Trading symbol (e.g., 'EURUSD', 'GBPUSD'). Must match MT5 broker symbol naming."
                            },
                            "lot_size": {
                                "type": "number",
                                "description": "Position size in lots (e.g., 0.01 for micro lot, 0.1 for mini lot, 1.0 for standard lot)"
                            },
                            "take_profit": {
                                "type": "number",
                                "description": "Take profit price level. REQUIRED for risk management."
                            },
                            "stop_loss": {
                                "type": "number",
                                "description": "Stop loss price level. REQUIRED for risk management."
                            }
                        },
                        "required": ["action", "symbol", "lot_size", "take_profit", "stop_loss"]
                    }
                }
            }
        ]
    
    def get_functions(self):
        """Return function mappings for the agent"""
        return {
            "execute_mt5_trade": self.execute_trade
        }
    
    def execute_trade(
        self,
        action: str,
        symbol: str,
        lot_size: float,
        take_profit: float,
        stop_loss: float
    ) -> Dict[str, Any]:
        """
        Execute a trade on MT5
        
        Args:
            action: "BUY" or "SELL"
            symbol: Trading symbol (e.g., "EURUSD")
            lot_size: Position size in lots
            take_profit: Take profit price
            stop_loss: Stop loss price
            
        Returns:
            Dict with trade result
        """
        try:
            # Determine endpoint
            endpoint = "/order/buy" if action.upper() == "BUY" else "/order/sell"
            url = f"{self.mt5_api_url}{endpoint}"
            
            # Prepare request payload
            payload = {
                "symbol": symbol,
                "lot_size": lot_size,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "comment": "Reki Auto Trade"
            }
            
            # Make HTTP request to MT5 API
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": f"{action} order executed successfully",
                    "ticket": result.get("ticket"),
                    "symbol": result.get("symbol"),
                    "price": result.get("price"),
                    "volume": result.get("volume"),
                    "take_profit": result.get("take_profit"),
                    "stop_loss": result.get("stop_loss")
                }
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.text else "No response"
                return {
                    "success": False,
                    "error": f"Trade execution failed: {error_detail}",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to MT5 API at {self.mt5_api_url}. Is the Windows VPS service running?"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request to MT5 API timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
