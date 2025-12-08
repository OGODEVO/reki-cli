import json
import os
import requests
from typing import Dict, Any, List
from reki.config import config

class ConsultCandleModelTool:
    def __init__(self):
        self.url = config.get("candle_model.url", "https://api.novita.ai/openai/v1/chat/completions")
        self.model = config.get("candle_model.model", "deepseek/deepseek-v3.2")
        self.timeout = config.get("candle_model.timeout", 30.0)
        self.api_key = os.environ.get("NOVITA_API_KEY", "")

    def get_tools(self) -> List[Dict[str, Any]]:
        return [{
            "type": "function",
            "function": {
                "name": "consult_candle_model",
                "description": "Consults the DeepSeek V3.2 model for a supporting trading opinion based on candle data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "candles": {
                            "type": "array",
                            "description": "List of the last 5-10 candles. Each candle must be a dict with keys: 'o', 'h', 'l', 'c', 'v'.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "o": {"type": "number", "description": "Open price"},
                                    "h": {"type": "number", "description": "High price"},
                                    "l": {"type": "number", "description": "Low price"},
                                    "c": {"type": "number", "description": "Close price"},
                                    "v": {"type": "number", "description": "Volume"}
                                },
                                "required": ["o", "h", "l", "c", "v"]
                            }
                        }
                    },
                    "required": ["candles"]
                }
            }
        }]

    def get_functions(self) -> Dict[str, Any]:
        return {
            "consult_candle_model": self.consult_candle_model
        }

    def consult_candle_model(self, candles: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Sends candle data to DeepSeek V3.2 via Novita API and returns the prediction.
        """
        if not config.get("candle_model.enabled", False):
            return {"error": "Candle model is disabled in config."}
        
        if not self.api_key:
            return {"error": "NOVITA_API_KEY environment variable not set."}

        try:
            # Extract data from candles
            last_candle = candles[-1] if candles else {}
            current_price = last_candle.get('c', 0)
            
            opens = [c['o'] for c in candles]
            closes = [c['c'] for c in candles]
            highs = [c['h'] for c in candles]
            lows = [c['l'] for c in candles]
            
            range_high = max(highs)
            range_low = min(lows)
            avg_range = sum(h - l for h, l in zip(highs, lows)) / len(candles) if candles else 0
            
            # Calculate trend slope (price change from first to last)
            trend_slope = closes[-1] - opens[0] if candles else 0
            
            # Simple momentum score based on closes vs opens
            bullish_candles = sum(1 for c in candles if c['c'] > c['o'])
            momentum_score = int((bullish_candles / len(candles)) * 100) if candles else 50
            
            # Volatility based on average range
            if avg_range > 5:
                volatility = "HIGH"
                tempo = "HIGH"
            elif avg_range > 2:
                volatility = "MODERATE"
                tempo = "MOD"
            else:
                volatility = "LOW"
                tempo = "LOW"
            
            # Build the market snapshot table
            prompt_content = f"""=== MARKET SNAPSHOT ===
| Metric           | Value              |
|------------------|--------------------|
| Price            | {current_price:.2f} |
| Range High/Low   | {range_high:.2f}/{range_low:.2f} |
| Avg Candle Range | {avg_range:.2f} pts |
| Trend Slope      | {'+' if trend_slope > 0 else ''}{trend_slope:.2f} |
| Momentum Score   | {momentum_score}/100 |
| Volatility State | {volatility} |
| Tempo            | {tempo} |

Support: ~{range_low:.2f} | Resistance: ~{range_high:.2f}

Based on this snapshot, what is your trading bias? Reply with: **LONG**, **SHORT**, or **STAY OUT**, followed by a brief reason (2-3 sentences max)."""
            
            # Construct payload
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a trading assistant for XAUUSD (Gold) micro-scalping. Analyze the market snapshot and give a concise trading opinion. Focus on momentum and quick $3-$10 moves."
                    },
                    {
                        "role": "user",
                        "content": prompt_content
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 300
            }
            
            # Headers with API key
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Send request
            response = requests.post(self.url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse response
            result_json = response.json()
            content = result_json['choices'][0]['message']['content']
            
            return {"prediction": content}
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to contact DeepSeek API: {str(e)}"}
        except KeyError as e:
            return {"error": f"Unexpected response format: {str(e)}"}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}
