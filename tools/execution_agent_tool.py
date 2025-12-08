"""
Execution Agent Tool - Passes trades to DeepSeek for execution via MT5 API
"""
import json
import os
import requests
from typing import Dict, Any, List
from reki.config import config


# System prompt for the DeepSeek execution agent
EXECUTION_SYSTEM_PROMPT = """You are a TRADE EXECUTION AGENT for XAUUSD (Gold) on MT5.

You will receive a trade decision from the main trading agent. Your job is to EXECUTE it immediately.

WHAT YOU WILL RECEIVE:
- ACTION: BUY or SELL
- SYMBOL: XAUUSD
- LOT_SIZE: 0.01
- TAKE_PROFIT: price like 4196.50
- STOP_LOSS: price like 4188.50

WHAT YOU MUST DO:
1. Call the execute_mt5_order tool IMMEDIATELY
2. Pass the EXACT parameters you received
3. Do not analyze, question, or modify anything

SYMBOL: Always use "XAUUSD" exactly as given.

YOU MUST CALL THE TOOL. DO NOT RESPOND WITH TEXT."""


class ExecutionAgentTool:
    """
    Passes trade commands to DeepSeek which executes via MT5.
    """
    
    def __init__(self):
        # DeepSeek API config
        self.deepseek_url = config.get("candle_model.url", "https://api.novita.ai/v3/openai/chat/completions")
        self.deepseek_model = config.get("candle_model.model", "deepseek/deepseek_v3")
        self.api_key = os.environ.get("NOVITA_API_KEY", "")
        
        # MT5 API config
        self.mt5_api_url = config.get("trading.mt5.api_url", "http://185.202.236.27:8000")
        self.timeout = 30.0

    def get_tools(self) -> List[Dict[str, Any]]:
        return [{
            "type": "function",
            "function": {
                "name": "execute_trade_via_agent",
                "description": "Execute a BUY or SELL trade via the execution agent. The agent will place the order on MT5.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["BUY", "SELL"],
                            "description": "BUY or SELL"
                        },
                        "symbol": {
                            "type": "string",
                            "description": "Symbol - use XAUUSD"
                        },
                        "lot_size": {
                            "type": "number",
                            "description": "Lot size - use 0.01"
                        },
                        "take_profit": {
                            "type": "number",
                            "description": "Take profit price"
                        },
                        "stop_loss": {
                            "type": "number",
                            "description": "Stop loss price"
                        }
                    },
                    "required": ["action", "symbol", "lot_size", "take_profit", "stop_loss"]
                }
            }
        }]

    def get_functions(self) -> Dict[str, Any]:
        return {
            "execute_trade_via_agent": self.execute_trade
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
        Pass trade to DeepSeek for execution.
        """
        if not self.api_key:
            return {"error": "NOVITA_API_KEY not set"}

        try:
            # Build user message with trade command
            user_message = f"""EXECUTE THIS TRADE NOW:

ACTION: {action}
SYMBOL: {symbol}
LOT_SIZE: {lot_size}
TAKE_PROFIT: {take_profit}
STOP_LOSS: {stop_loss}

Call execute_mt5_order with these exact values."""

            # Tool definition for DeepSeek
            mt5_tool = {
                "type": "function",
                "function": {
                    "name": "execute_mt5_order",
                    "description": "Place order on MT5",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["BUY", "SELL"]},
                            "symbol": {"type": "string"},
                            "lot_size": {"type": "number"},
                            "take_profit": {"type": "number"},
                            "stop_loss": {"type": "number"}
                        },
                        "required": ["action", "symbol", "lot_size", "take_profit", "stop_loss"]
                    }
                }
            }

            # Call DeepSeek
            payload = {
                "model": self.deepseek_model,
                "messages": [
                    {"role": "system", "content": EXECUTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "tools": [mt5_tool],
                "tool_choice": "auto",
                "temperature": 0.0,
                "max_tokens": 200
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            response = requests.post(self.deepseek_url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            message = result['choices'][0]['message']
            
            # Check for tool call
            if message.get('tool_calls'):
                tool_call = message['tool_calls'][0]
                tool_args = json.loads(tool_call['function']['arguments'])
                
                # Execute on MT5
                return self._call_mt5(
                    action=tool_args.get('action', action),
                    symbol=tool_args.get('symbol', symbol),
                    lot_size=tool_args.get('lot_size', lot_size),
                    take_profit=tool_args.get('take_profit', take_profit),
                    stop_loss=tool_args.get('stop_loss', stop_loss)
                )
            else:
                # DeepSeek didn't call tool - execute directly
                return self._call_mt5(action, symbol, lot_size, take_profit, stop_loss)
                
        except requests.exceptions.RequestException as e:
            return {"error": f"DeepSeek API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}

    def _call_mt5(
        self,
        action: str,
        symbol: str,
        lot_size: float,
        take_profit: float,
        stop_loss: float
    ) -> Dict[str, Any]:
        """
        Execute the actual MT5 API call.
        """
        try:
            endpoint = "/order/buy" if action.upper() == "BUY" else "/order/sell"
            url = f"{self.mt5_api_url}{endpoint}"
            
            payload = {
                "symbol": symbol,
                "lot_size": lot_size,
                "take_profit": take_profit,
                "stop_loss": stop_loss
            }
            
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": f"{action} executed via DeepSeek agent",
                    "ticket": result.get("ticket"),
                    "symbol": result.get("symbol"),
                    "price": result.get("price"),
                    "volume": result.get("volume"),
                    "take_profit": result.get("take_profit"),
                    "stop_loss": result.get("stop_loss")
                }
            else:
                try:
                    error_detail = response.json().get("detail", "Unknown")
                except:
                    error_detail = response.text
                return {"success": False, "error": f"MT5 error: {error_detail}"}
                
        except Exception as e:
            return {"success": False, "error": f"MT5 connection error: {str(e)}"}
