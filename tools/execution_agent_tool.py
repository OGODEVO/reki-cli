"""
Execution Agent Tool - Passes trade decisions to DeepSeek which executes via MT5 API
The main agent (Gemini) makes the decision, DeepSeek handles execution.
"""
import json
import os
import requests
from typing import Dict, Any, List
from reki.config import config


class ExecutionAgentTool:
    """
    Execution agent that receives trade commands from the main agent,
    passes them to DeepSeek V3.2, which then executes via MT5 API.
    """
    
    def __init__(self):
        # DeepSeek API config (via Novita)
        self.deepseek_url = config.get("candle_model.url", "https://api.novita.ai/openai/v1/chat/completions")
        self.deepseek_model = config.get("candle_model.model", "deepseek/deepseek-v3.2")
        self.api_key = os.environ.get("NOVITA_API_KEY", "")
        
        # MT5 API config (for DeepSeek to call)
        self.mt5_api_url = config.get("trading.mt5.api_url", "http://185.202.236.27:8000")
        self.timeout = config.get("execution_agent.timeout", 30.0)

    def get_tools(self) -> List[Dict[str, Any]]:
        return [{
            "type": "function",
            "function": {
                "name": "execute_trade_via_agent",
                "description": "Execute a trade through the DeepSeek execution agent. Pass your trade decision and the agent will execute it via MT5.",
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
                            "description": "Trading symbol (e.g., 'XAUUSD')"
                        },
                        "lot_size": {
                            "type": "number",
                            "description": "Position size in lots (default 0.01)"
                        },
                        "take_profit": {
                            "type": "number",
                            "description": "Take profit price level"
                        },
                        "stop_loss": {
                            "type": "number",
                            "description": "Stop loss price level"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Brief reason for the trade"
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
        stop_loss: float,
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        Pass trade decision to DeepSeek, which executes via MT5.
        """
        if not self.api_key:
            return {"error": "NOVITA_API_KEY environment variable not set."}

        try:
            # Build the execution prompt for DeepSeek
            execution_prompt = f"""You are a trade execution agent. Execute the following trade via the MT5 API.

TRADE COMMAND:
- Action: {action}
- Symbol: {symbol}
- Lot Size: {lot_size}
- Take Profit: {take_profit}
- Stop Loss: {stop_loss}
- Reason: {reason or 'N/A'}

MT5 API URL: {self.mt5_api_url}
Endpoint: /order/buy (for BUY) or /order/sell (for SELL)

Execute this trade NOW by calling the execute_mt5_order tool with the parameters above."""

            # Define the MT5 execution tool for DeepSeek
            mt5_tools = [{
                "type": "function",
                "function": {
                    "name": "execute_mt5_order",
                    "description": "Execute an order on MT5",
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
            }]

            # Call DeepSeek
            payload = {
                "model": self.deepseek_model,
                "messages": [
                    {"role": "system", "content": "You are a trade execution agent. When given a trade command, immediately execute it using the execute_mt5_order tool. Do not hesitate or ask questions."},
                    {"role": "user", "content": execution_prompt}
                ],
                "tools": mt5_tools,
                "tool_choice": "auto",
                "temperature": 0.1,
                "max_tokens": 500
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            response = requests.post(self.deepseek_url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            message = result['choices'][0]['message']
            
            # Check if DeepSeek made a tool call
            if message.get('tool_calls'):
                tool_call = message['tool_calls'][0]
                tool_args = json.loads(tool_call['function']['arguments'])
                
                # Now execute the actual MT5 API call
                return self._execute_mt5_order(
                    action=tool_args.get('action', action),
                    symbol=tool_args.get('symbol', symbol),
                    lot_size=tool_args.get('lot_size', lot_size),
                    take_profit=tool_args.get('take_profit', take_profit),
                    stop_loss=tool_args.get('stop_loss', stop_loss),
                    reason=reason
                )
            else:
                # DeepSeek didn't make a tool call, execute directly
                return self._execute_mt5_order(action, symbol, lot_size, take_profit, stop_loss, reason)
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to contact DeepSeek API: {str(e)}"}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}

    def _execute_mt5_order(
        self,
        action: str,
        symbol: str,
        lot_size: float,
        take_profit: float,
        stop_loss: float,
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        Actually execute the MT5 order via API.
        """
        try:
            endpoint = "/order/buy" if action.upper() == "BUY" else "/order/sell"
            url = f"{self.mt5_api_url}{endpoint}"
            
            payload = {
                "symbol": symbol,
                "lot_size": lot_size,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "comment": f"Reki: {reason[:50]}" if reason else "Reki Auto Trade"
            }
            
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": f"{action} order executed successfully via DeepSeek agent",
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
            return {"success": False, "error": f"Cannot connect to MT5 API at {self.mt5_api_url}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request to MT5 API timed out"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
