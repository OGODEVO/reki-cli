import os
import json
import random
import time
import tiktoken
import concurrent.futures
from datetime import datetime, timedelta
from openai import OpenAI, RateLimitError
from tools.brave_search import BrowserTool
from tools.google_finance_tool import GoogleFinanceTool
from tools.fx_sma_indicator import FXSMAIndicatorTool
from tools.fx_ema_indicator import FXEMAIndicatorTool
from tools.fx_macd_indicator import FXMACDIndicatorTool
from tools.fx_rsi_indicator import FXRSIIndicatorTool
from tools.fx_market_status import FXMarketStatusTool
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
    def __init__(self, api_key, user_id, system_prompt, model_name, api_base_url, ui):
        self.client = OpenAI(base_url=api_base_url, api_key=api_key)
        self.user_id = user_id
        self.original_system_prompt = system_prompt
        self.model_name = model_name
        self.ui = ui
        self.messages = [] # Messages will be constructed dynamically
        self.analysis_cache = {} # Cache for the current turn's analysis
        self.tool_emojis = ["📈", "💰", "📊", "💹"]
        
        self.browser_tool = BrowserTool()
        self.google_finance_tool = GoogleFinanceTool()
        self.fx_sma_indicator_tool = FXSMAIndicatorTool()
        self.fx_ema_indicator_tool = FXEMAIndicatorTool()
        self.fx_macd_indicator_tool = FXMACDIndicatorTool()
        self.fx_rsi_indicator_tool = FXRSIIndicatorTool()
        self.fx_market_status_tool = FXMarketStatusTool()
        
        self.tools = self._setup_tools()
        self.available_functions = self._setup_available_functions()

    def _setup_tools(self):
        tools = []
        tools.extend(self.browser_tool.get_tools())
        tools.extend(self.google_finance_tool.get_tools())
        tools.extend(self.fx_sma_indicator_tool.get_tools())
        tools.extend(self.fx_ema_indicator_tool.get_tools())
        tools.extend(self.fx_macd_indicator_tool.get_tools())
        tools.extend(self.fx_rsi_indicator_tool.get_tools())
        tools.extend(self.fx_market_status_tool.get_tools())
        return tools

    def _setup_available_functions(self):
        return {
            "browser_search": self.browser_tool.search,
            "get_finance_data": self.google_finance_tool.get_finance_data,
            "get_sma_indicator": self.fx_sma_indicator_tool.get_sma,
            "get_ema_indicator": self.fx_ema_indicator_tool.get_ema,
            "get_macd_indicator": self.fx_macd_indicator_tool.get_macd,
            "get_rsi_indicator": self.fx_rsi_indicator_tool.get_rsi,
            "get_market_status": self.fx_market_status_tool.get_status,
        }

    def save_memory_entry(self, command):
        """
        Generates a summary of the current conversation and appends it as a JSON object
        to the memory file, with an optional expiration time.
        """
        summary_prompt = "Your task is to create a concise, single-paragraph summary of the following conversation for long-term memory. Identify the user's primary goal or question, and the key information or resolution provided by the assistant. Distill the most critical information needed to quickly understand the context of this conversation in the future."
        
        messages_for_summary = self.messages + [{"role": "user", "content": summary_prompt}]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages_for_summary,
                temperature=0.5,
                max_tokens=250
            )
            
            summary = response.choices[0].message.content.strip()
            
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
        # 1. Construct dynamic system prompt and message history
        dynamic_system_prompt = f"{self.original_system_prompt}"
        short_term_history = self.messages[-4:]
        self.messages = [{"role": "system", "content": dynamic_system_prompt}] + short_term_history
        self.messages.append({"role": "user", "content": user_input})

        # --- Start of Autonomous Loop ---
        while True:
            # 2. Call the LLM
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=self.messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0.7
                )
                response_message = response.choices[0].message
            except Exception as e:
                self.ui.display_error(f"An API error occurred: {e}")
                return

            # 3. Decide what to do based on the LLM's response
            tool_calls = response_message.tool_calls
            response_content = response_message.content if response_message.content else ""

            # Case 1: The LLM wants to call tools.
            if tool_calls:
                # Append the assistant's decision to call tools, but ignore any conversational content
                self.messages.append(response_message) 

                def process_tool_call(tool_call):
                    """Helper function to process a single tool call."""
                    function_name = tool_call.function.name
                    try:
                        # Robustly parse arguments
                        function_args_str = tool_call.function.arguments
                        start_brace = function_args_str.find('{')
                        end_brace = function_args_str.rfind('}')
                        if start_brace != -1 and end_brace != -1 and start_brace < end_brace:
                            json_str = function_args_str[start_brace:end_brace+1]
                            function_args = json.loads(json_str)
                        else:
                            raise json.JSONDecodeError("No valid JSON object found.", function_args_str, 0)

                        # Display the tool call in the UI immediately
                        self.ui.display_tool_call(function_name, function_args)
                        
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

                # Execute all tool calls in parallel
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    tool_results = list(executor.map(process_tool_call, tool_calls))
                
                # Append all results to the message history
                for result in tool_results:
                    self.messages.append(result)
                
                # Loop back to the start to call the LLM again with the tool results
                continue

            # Case 1B: The LLM is putting the tool call in the content (fallback)
            if "<tool_calls_begin>" in response_content:
                self.messages.append(response_message) # Save the model's response

                # --- Parsing the custom tool call format ---
                try:
                    # Extract content between markers
                    call_str = response_content.split("<tool_call_begin>")[1].split("<tool_call_end>")[0].strip()
                    
                    # Split function name and arguments
                    parts = call_str.split("<tool_sep>")
                    function_name = parts[0].strip()
                    
                    # The arguments part might be empty JSON '{}' or have content
                    args_str = parts[1].strip() if len(parts) > 1 else "{}"
                    function_args = json.loads(args_str)

                    # --- Executing the tool ---
                    self.ui.display_tool_call(function_name, function_args)
                    function_to_call = self.available_functions[function_name]
                    function_response = function_to_call(**function_args)

                    # --- Appending the result ---
                    tool_result = {
                        "tool_call_id": f"call_{random.randint(1000, 9999)}", # Generate a random ID
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(function_response),
                    }
                    self.messages.append(tool_result)

                except Exception as e:
                    error_message = f"Error parsing or executing tool from content: {e}"
                    self.ui.display_error(error_message)
                    # Append an error message for the model to see
                    self.messages.append({
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps({"error": error_message}),
                    })

                continue # Loop back to the LLM with the tool result

            # Case 2: The LLM has finished and is providing the final text response.
            elif response_content:
                final_content = response_content
                self.messages.append({"role": "assistant", "content": final_content})
                # Yield the final content to the UI's character-by-character streamer
                yield final_content
                break # Exit the autonomous loop
            else:
                # Handle cases where the model returns neither content nor tool calls
                yield "[The model returned an empty response.]"
                break
