import os
import json
import random
import time
import tiktoken
import concurrent.futures
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from openai import OpenAI, RateLimitError
from tools.brave_search import BrowserTool
# from tools.binance_tool import BinanceTool
# from tools.forex_tool import ForexTool
from tools.daily_market_tool import DailyMarketTool
from tools.currency_conversion_tool import CurrencyConversionTool
from tools.minute_aggregates_tool import MinuteAggregatesTool
# from tools.google_finance_tool import GoogleFinanceTool
from tools.fx_sma_indicator import FXSMAIndicatorTool
from tools.fx_ema_indicator import FXEMAIndicatorTool
from tools.fx_macd_indicator import FXMACDIndicatorTool
from tools.fx_rsi_indicator import FXRSIIndicatorTool
from tools.fx_market_status import FXMarketStatusTool
from tools.mt5_execute_trade import MT5ExecuteTradeTool
from tools.mt5_check_positions import MT5CheckPositionsTool
from IPython import get_ipython
from ui import TerminalUI

def count_tokens(messages, model="gpt-4"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    
    num_tokens = 0
    for message in messages:
        num_tokens += 4
        for key, value in message.items():
            if value:
                num_tokens += len(encoding.encode(str(value)))
    num_tokens += 3
    return num_tokens

class ChatAgent:
    def __init__(self, api_key, user_id, system_prompt, model_name, api_base_url, ui, summarizer_config=None):
        self.client = OpenAI(base_url=api_base_url, api_key=api_key)
        
        # Setup summarizer client (default to main client if config not provided)
        if summarizer_config and summarizer_config.get("api_key"):
            self.summarizer_client = OpenAI(
                base_url=summarizer_config.get("base_url"), 
                api_key=summarizer_config.get("api_key")
            )
            self.summarizer_model = summarizer_config.get("model")
        else:
            self.summarizer_client = self.client
            self.summarizer_model = model_name

        self.user_id = user_id
        self.original_system_prompt = system_prompt
        self.model_name = model_name
        self.ui = ui
        self.messages = [] # Messages will be constructed dynamically
        self.analysis_cache = {} # Cache for the current turn's analysis
        self.last_interaction_time = None # Track the last time the user interacted
        
        self.tools_metadata = {
            "browser_search": {"emoji": "🌐", "desc": "Searching the web"},
            # "get_finance_data": {"emoji": "💹", "desc": "Fetching financial data"},
            "get_sma_indicator": {"emoji": "✈️", "desc": "Calculating SMA"},
            "get_ema_indicator": {"emoji": "📈", "desc": "Calculating EMA"},
            "get_macd_indicator": {"emoji": "📊", "desc": "Calculating MACD"},
            "get_rsi_indicator": {"emoji": "🌡️", "desc": "Calculating RSI"},
            "get_market_status": {"emoji": "🚦", "desc": "Checking market status"},
            # "get_latest_binance_price": {"emoji": "💰", "desc": "Fetching Binance price"},
            # "get_forex_rate": {"emoji": "💱", "desc": "Fetching Forex rate"},
            "get_daily_market_summary": {"emoji": "📖", "desc": "Fetching daily market summary"},
            "get_currency_conversion": {"emoji": "💱", "desc": "Converting currency"},
            "get_minute_aggregates": {"emoji": "🚀", "desc": "Streaming minute aggregates"},
            "execute_mt5_trade": {"emoji": "💸", "desc": "Executing MT5 trade"},
            "check_mt5_positions": {"emoji": "📋", "desc": "Checking MT5 positions"},
            "close_mt5_position": {"emoji": "🔒", "desc": "Closing MT5 position"},
            "close_all_mt5_positions": {"emoji": "🚨", "desc": "Closing all MT5 positions"},
        }
        
        self.browser_tool = BrowserTool()
        # self.google_finance_tool = GoogleFinanceTool()
        self.fx_sma_indicator_tool = FXSMAIndicatorTool()
        self.fx_ema_indicator_tool = FXEMAIndicatorTool()
        self.fx_macd_indicator_tool = FXMACDIndicatorTool()
        self.fx_rsi_indicator_tool = FXRSIIndicatorTool()
        self.fx_market_status_tool = FXMarketStatusTool()
        # self.binance_tool = BinanceTool()
        # self.forex_tool = ForexTool()
        self.daily_market_tool = DailyMarketTool()
        self.currency_conversion_tool = CurrencyConversionTool()
        self.minute_aggregates_tool = MinuteAggregatesTool()
        self.mt5_execute_tool = MT5ExecuteTradeTool()
        self.mt5_positions_tool = MT5CheckPositionsTool()
        
        self.tools, self.available_functions = self._setup_tools_and_functions()

    def _setup_tools_and_functions(self):
        """
        Dynamically registers tools and their corresponding functions.
        """
        tools = []
        available_functions = {}
        
        tool_instances = [
            self.browser_tool,
            # self.google_finance_tool,
            self.fx_sma_indicator_tool,
            self.fx_ema_indicator_tool,
            self.fx_macd_indicator_tool,
            self.fx_rsi_indicator_tool,
            self.fx_market_status_tool,
            # self.binance_tool,
            # self.forex_tool,
            self.daily_market_tool,
            self.currency_conversion_tool,
            self.minute_aggregates_tool,
            self.mt5_execute_tool,
            self.mt5_positions_tool
        ]
        
        for tool in tool_instances:
            tools.extend(tool.get_tools())
            available_functions.update(tool.get_functions())
            
        return tools, available_functions

    def save_memory_entry(self, command):
        """
        Generates a summary of the current conversation and appends it as a JSON object
        to the memory file, with an optional expiration time.
        """
        summary_prompt = "Your task is to create a concise, single-paragraph summary of the following conversation for long-term memory. Identify the user's primary goal or question, and the key information or resolution provided by the assistant. Distill the most critical information needed to quickly understand the context of this conversation in the future."
        
        messages_for_summary = self.messages + [{"role": "user", "content": summary_prompt}]
        
        try:
            completion_params = {
                "model": self.summarizer_model,
                "messages": messages_for_summary,
                "temperature": 0.7,
            }
            
            # Adjust tokens based on the summarizer model, not the main model
            if self.summarizer_model.startswith("gpt-5") or self.summarizer_model.startswith("o1"):
                completion_params["max_completion_tokens"] = 2000
            else:
                completion_params["max_tokens"] = 500

            response = self.summarizer_client.chat.completions.create(**completion_params)
            
            summary = response.choices[0].message.content
            if summary:
                summary = summary.strip()
            else:
                print(f"Warning: Model returned empty summary. Finish reason: {response.choices[0].finish_reason}")
                summary = "No summary generated."
            
            # --- Expiration Logic ---
            parts = command.lower().split()
            expires_at = None
            if len(parts) == 3:
                try:
                    value = int(parts[1])
                    unit = parts[2]
                    
                    if unit in ["h", "hr", "hrs", "hour", "hours"]:
                        delta = timedelta(hours=value)
                    elif unit in ["d", "day", "days"]:
                        delta = timedelta(days=value)
                    elif unit in ["w", "wk", "wks", "week", "weeks"]:
                        delta = timedelta(weeks=value)
                    else:
                        delta = None
                    
                    if delta:
                        expires_at = (datetime.now() + delta).isoformat()
                except (ValueError, IndexError):
                    pass # Ignore malformed commands
            # --- End Expiration Logic ---

            memory_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id,
                "summary": summary,
                "conversation_token_count": count_tokens(self.messages),
                "expires_at": expires_at
            }
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            memory_path = os.path.join(script_dir, "memory.jsonl")
            
            with open(memory_path, "a") as f:
                f.write(json.dumps(memory_entry) + "\n")
                
        except Exception as e:
            print(f"Error saving memory: {e}")

    def get_response(self, user_input):
        # 1. Construct message history
        # If this is the first message of a session, add the system prompt.
        # The '/reset' command also clears the history, allowing this to trigger again.
        if not self.messages:
            self.messages.append({"role": "system", "content": self.original_system_prompt})
        
        # Add the new user message to the full conversation history
        
        # --- Time Context Injection ---
        chicago_tz = ZoneInfo("America/Chicago")
        current_time = datetime.now(chicago_tz)
        time_str = current_time.strftime("%I:%M %p")
        
        time_context = f"Current Time: {time_str}"
        
        if self.last_interaction_time:
            time_diff = current_time - self.last_interaction_time
            minutes_diff = int(time_diff.total_seconds() / 60)
            
            if minutes_diff > 0:
                time_context += f" | Time since last message: {minutes_diff} minutes"
        
        self.last_interaction_time = current_time
        
        # Inject time context as a system message before the user message
        self.messages.append({"role": "system", "content": f"[{time_context}]"})
        # ------------------------------

        self.messages.append({"role": "user", "content": user_input})

        # --- Start of Autonomous Loop ---
        max_retries = 3
        retry_count = 0
        while True:
            # 2. Call the LLM
            try:
                completion_params = {
                    "model": self.model_name,
                    "messages": self.messages,
                    "tools": self.tools,
                    "tool_choice": "auto",
                    "temperature": 0.7,
                }

                if self.model_name.startswith("gpt-5") or self.model_name.startswith("o1"):
                    completion_params["max_completion_tokens"] = 65536
                else:
                    completion_params["max_tokens"] = 65536

                response = self.client.chat.completions.create(**completion_params)
                response_message = response.choices[0].message
            except Exception as e:
                self.ui.display_error(f"An API error occurred: {e}")
                return

            # 3. Decide what to do based on the LLM's response
            tool_calls = response_message.tool_calls
            response_content = response_message.content if response_message.content else ""

            # Case 1: The LLM wants to call tools.
            if tool_calls:
                # Enforce singular focal: only process the first tool call
                tool_calls = tool_calls[:1]

                # If the model returned a concatenated/malformed tool-call string, parse only the first embedded call.
                import types

                def _wrap(obj):
                    # Wrap dict-like or SDK objects to a simple namespace with .id and .function.{name,arguments}
                    if isinstance(obj, dict):
                        fn = obj.get("function", {}) or {}
                        return types.SimpleNamespace(
                            id=obj.get("id", f"call_{random.randint(1000,9999)}"),
                            function=types.SimpleNamespace(name=fn.get("name"), arguments=fn.get("arguments", ""))
                        )
                    return obj  # assume SDK-style object; downstream code will access attributes

                first = tool_calls[0]
                first = _wrap(first)

                # If concatenated markers appear in the function name, extract only the first embedded call.
                fn_name = getattr(first.function, "name", "") or ""
                if "<tool_call_begin>" in fn_name or "<tool_sep>" in fn_name:
                    # find first block and parse "name<tool_sep>json_args"
                    parts = [p for p in fn_name.split("<tool_call_begin>") if p]
                    if parts:
                        block = parts[0].split("<tool_call_end>")[0].strip()
                        if "<tool_sep>" in block:
                            name_part, args_part = block.split("<tool_sep>", 1)
                            first = types.SimpleNamespace(
                                id=f"call_{random.randint(1000,9999)}",
                                function=types.SimpleNamespace(name=name_part.strip(), arguments=args_part.strip())
                            )
                # Replace tool_calls with a single-element list (singular focal)
                tool_calls = [first]
                # --- End of Preprocessing Step ---

                # Append the assistant's decision to call tools to the message history
                # We must ensure the stored message only contains the tool calls we actually process (singular focal),
                # otherwise the API will error complaining about missing tool outputs.
                
                def _tool_call_to_dict(tc):
                    if hasattr(tc, 'model_dump'):
                        return tc.model_dump()
                    if isinstance(tc, dict):
                        return tc
                    # Handle SimpleNamespace or similar objects
                    return {
                        "id": getattr(tc, "id", ""),
                        "type": "function",
                        "function": {
                            "name": getattr(tc.function, "name", ""),
                            "arguments": getattr(tc.function, "arguments", "")
                        }
                    }

                assistant_msg = response_message.model_dump()
                assistant_msg["tool_calls"] = [_tool_call_to_dict(t) for t in tool_calls]
                self.messages.append(assistant_msg) 

                def process_tool_call(tool_call):
                    """Helper function to process a single tool call."""
                    function_name = tool_call.function.name
                    try:
                        # The arguments should already be a valid JSON string from the regex capture
                        function_args = json.loads(tool_call.function.arguments)

                        # Display the tool call in the UI immediately
                        metadata = self.tools_metadata.get(function_name, {})
                        self.ui.display_tool_call(function_name, function_args, metadata)
                        
                        # Execute the tool function
                        function_to_call = self.available_functions[function_name]
                        function_response = function_to_call(**function_args)
                        
                        return {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(function_response),
                        }
                    except Exception as e:
                        error_message = f"Error executing tool {function_name}: {e}"
                        self.ui.display_error(error_message)
                        return {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps({"error": error_message}),
                        }

                # Execute all tool calls sequentially with a delay
                tool_results = []
                for tool_call in tool_calls:
                    result = process_tool_call(tool_call)
                    tool_results.append(result)
                    time.sleep(1)  # Add a 1-second delay to respect rate limits
                
                # Append all results to the message history
                for result in tool_results:
                    self.messages.append(result)
                
                # Loop back to the start to call the LLM again with the tool results
                continue
            # Case 1B: The LLM is putting the tool call in the content (fallback)
            if "<tool_calls_begin>" in response_content:
                self.messages.append(response_message.model_dump()) # Save the model's response
                
                tool_results = []
                # Split the response content to handle multiple tool calls
                potential_calls = response_content.split("<tool_call_begin>")
                
                for call_block in potential_calls:
                    if "<tool_call_end>" not in call_block:
                        continue

                    try:
                        # Extract content for a single tool call
                        call_str = call_block.split("<tool_call_end>")[0].strip()
                        
                        # Skip empty or malformed calls
                        if not call_str or "<tool_sep>" not in call_str:
                            continue
                            
                        # Split function name and arguments
                        name_and_args = call_str.split("<tool_sep>")
                        if len(name_and_args) != 2:
                            continue
                            
                        function_name = name_and_args[0].strip()
                        args_str = name_and_args[1].strip()
                        
                        # Validate function name exists in available functions
                        if function_name not in self.available_functions:
                            continue
                            
                        # Ensure args_str is proper JSON
                        try:
                            function_args = json.loads(args_str)
                        except json.JSONDecodeError:
                            continue

                        # Execute the tool
                        metadata = self.tools_metadata.get(function_name, {})
                        self.ui.display_tool_call(function_name, function_args, metadata)
                        function_to_call = self.available_functions[function_name]
                        function_response = function_to_call(**function_args)

                        tool_results.append({
                            "tool_call_id": f"call_{random.randint(1000, 9999)}",
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(function_response),
                        })

                    except Exception as e:
                        error_message = f"Error executing tool {function_name}: {e}"
                        self.ui.display_error(error_message)
                        tool_results.append({
                            "tool_call_id": f"error_{random.randint(1000, 9999)}",
                            "role": "tool",
                            "name": "error_handler",
                            "content": json.dumps({"error": error_message}),
                        })
                
                # Append all collected tool results to the message history
                for result in tool_results:
                    self.messages.append(result)

                continue # Loop back to the LLM with the tool results

            # Case 2: The LLM has finished and is providing the final text response.
            elif response_content:
                final_content = response_content
                self.messages.append({"role": "assistant", "content": final_content})
                # Yield the final content to the UI's character-by-character streamer
                yield final_content
                break # Exit the autonomous loop
            else:
                # Handle cases where the model returns neither content nor tool calls
                retry_count += 1
                if retry_count < max_retries:
                    self.ui.display_message(f"Model returned an empty response. Retrying ({retry_count}/{max_retries})...", "Retry", "yellow")
                    time.sleep(1)  # Optional: wait a moment before retrying
                    continue
                else:
                    yield "[The model is not responding after multiple attempts.]"
                    break
