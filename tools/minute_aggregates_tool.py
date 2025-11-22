import os
import time
import threading
from typing import List
from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage, Feed, Market

class MinuteAggregatesTool:
    def __init__(self):
        self.api_key = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY")
        if not self.api_key:
            pass

    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_minute_aggregates",
                    "description": "Stream real-time minute-by-minute OHLC aggregates for a Forex pair. Collects bars for a specified duration.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pair": {
                                "type": "string",
                                "description": "The currency pair (e.g., 'USD/EUR', 'USD/CAD')."
                            },
                            "duration_seconds": {
                                "type": "integer",
                                "description": "How long to collect data in seconds. Defaults to 60."
                            }
                        },
                        "required": ["pair"]
                    }
                }
            }
        ]

    def get_functions(self):
        return {
            "get_minute_aggregates": self.get_minute_aggregates
        }

    def get_minute_aggregates(self, pair: str, duration_seconds: int = 60):
        """
        Streams minute aggregates for the specified pair and duration.
        """
        if not self.api_key:
            return {"error": "MASSIVE_API_KEY or POLYGON_API_KEY environment variable not set."}

        collected_messages = []
        collection_complete = threading.Event()

        def handle_msg(msgs: List[WebSocketMessage]):
            for m in msgs:
                collected_messages.append({
                    "type": str(type(m).__name__),
                    "data": str(m)
                })

        try:
            client = WebSocketClient(
                api_key=self.api_key,
                feed=Feed.RealTime,
                market=Market.Forex
            )

            # Subscribe to the pair
            subscription = f"CA.{pair}"
            client.subscribe(subscription)

            # Run in a separate thread with timeout
            def run_client():
                try:
                    client.run(handle_msg)
                except Exception as e:
                    collected_messages.append({"error": f"WebSocket error: {e}"})
                finally:
                    collection_complete.set()

            client_thread = threading.Thread(target=run_client, daemon=True)
            client_thread.start()

            # Wait for specified duration
            time.sleep(duration_seconds)

            # Signal the thread to stop by setting the event
            # The WebSocket client will stop naturally when the thread ends
            collection_complete.set()
            
            # Wait for thread cleanup
            client_thread.join(timeout=2)

            if not collected_messages:
                return {
                    "message": f"No data received for {pair} during {duration_seconds} seconds. Market may be closed or pair may be invalid.",
                    "subscription": subscription
                }

            return {
                "pair": pair,
                "duration_seconds": duration_seconds,
                "messages_collected": len(collected_messages),
                "data": collected_messages
            }

        except Exception as e:
            return {"error": f"An error occurred: {e}"}

if __name__ == '__main__':
    # Example usage
    import json
    tool = MinuteAggregatesTool()
    print("Testing get_minute_aggregates for EUR/USD (10 seconds)...")
    result = tool.get_minute_aggregates("USD/EUR", duration_seconds=10)
    print(json.dumps(result, indent=2))
