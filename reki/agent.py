import os
import json
import random
import time
import tiktoken
from openai import OpenAI, RateLimitError
from tools.brave_search import BrowserTool
from tools.web_fetcher import WebFetcherTool
from tools.fx_sma_indicator import FXSMAIndicatorTool
from tools.fx_ema_indicator import FXEMAIndicatorTool
from tools.fx_macd_indicator import FXMACDIndicatorTool
from tools.fx_rsi_indicator import FXRSIIndicatorTool
from tools.fx_market_status import FXMarketStatusTool
from IPython import get_ipython

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
    def __init__(self, api_key, user_id, system_prompt):
        self.client = OpenAI(base_url="https://api.novita.ai/openai", api_key=api_key)
        self.original_system_prompt = system_prompt
        self.messages = [] # Messages will be constructed dynamically
        self.analysis_cache = {} # Cache for the current turn's analysis
        self.tool_emojis = ["📈", "💰", "📊", "💹"]
        
        self.browser_tool = BrowserTool()
        self.web_fetcher_tool = WebFetcherTool()
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
        tools.extend(self.web_fetcher_tool.get_tools())
        tools.extend(self.fx_sma_indicator_tool.get_tools())
        tools.extend(self.fx_ema_indicator_tool.get_tools())
        tools.extend(self.fx_macd_indicator_tool.get_tools())
        tools.extend(self.fx_rsi_indicator_tool.get_tools())
        tools.extend(self.fx_market_status_tool.get_tools())
        return tools

    def _setup_available_functions(self):
        return {
            "browser_search": self.browser_tool.search,
            "url_fetch": self.web_fetcher_tool.fetch,
            "get_sma_indicator": self.fx_sma_indicator_tool.get_sma,
            "get_ema_indicator": self.fx_ema_indicator_tool.get_ema,
            "get_macd_indicator": self.fx_macd_indicator_tool.get_macd,
            "get_rsi_indicator": self.fx_rsi_indicator_tool.get_rsi,
            "get_market_status": self.fx_market_status_tool.get_status,
        }

    def get_response(self, user_input):
        # 1. Construct dynamic system prompt
        dynamic_system_prompt = f"{self.original_system_prompt}"
        
        # 2. Reconstruct messages for this turn
        # We keep the last few messages for short-term context, plus the new dynamic prompt
        short_term_history = self.messages[-4:] # Keep last 2 turns
        self.messages = [{"role": "system", "content": dynamic_system_prompt}] + short_term_history
        self.messages.append({"role": "user", "content": user_input})

        while True:
            max_retries = 5
            base_delay = 1  # in seconds
            chat_completion_res = None

            for attempt in range(max_retries):
                try:
                    chat_completion_res = self.client.chat.completions.create(
                        model="deepseek/deepseek-v3.2-exp", messages=self.messages, tools=self.tools, tool_choice="auto", stream=True, max_tokens=65346, temperature=0.7
                    )
                    break  # If successful, exit the loop
                except RateLimitError as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        yield f"\n[Rate limit exceeded. Retrying in {delay}s...]"
                        time.sleep(delay)
                    else:
                        raise e  # Re-raise the exception after the last attempt
            
            if chat_completion_res is None:
                yield "\n[API call failed after multiple retries.]"
                return

            full_response_content = ""
            tool_call_chunks = []
            
            for chunk in chat_completion_res:
                if chunk.choices:
                    chunk_content = chunk.choices[0].delta.content or ""
                    full_response_content += chunk_content
                    yield chunk_content

                    if chunk.choices[0].delta.tool_calls:
                        for tool_call_chunk in chunk.choices[0].delta.tool_calls:
                            if len(tool_call_chunks) <= tool_call_chunk.index:
                                tool_call_chunks.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                            
                            chunk_data = tool_call_chunks[tool_call_chunk.index]
                            if tool_call_chunk.id: chunk_data["id"] = tool_call_chunk.id
                            if tool_call_chunk.function.name: chunk_data["function"]["name"] = tool_call_chunk.function.name
                            if tool_call_chunk.function.arguments: chunk_data["function"]["arguments"] += tool_call_chunk.function.arguments
            
            # 4. Add the exchange to memory *after* the response is complete, if there's content
            if full_response_content and full_response_content.strip():
                pass

            if tool_call_chunks:
                self.messages.append({"role": "assistant", "tool_calls": tool_call_chunks})
                
                for tool_call in tool_call_chunks:
                    function_name = tool_call["function"]["name"]
                    function_args_str = tool_call["function"]["arguments"]
                    
                    try:
                        if "</tool_sep" in function_args_str:
                            function_args_str = function_args_str.split("</tool_sep")[0]

                        function_args = json.loads(function_args_str)
                        function_to_call = self.available_functions[function_name]
                        
                        # Announce tool execution first
                        emoji = random.choice(self.tool_emojis)
                        yield f"Executing tool {emoji} ... "

                        # Check cache before executing
                        cache_key = f"{function_name}_{json.dumps(function_args, sort_keys=True)}"
                        if cache_key in self.analysis_cache:
                            function_response = self.analysis_cache[cache_key]
                        else:
                            if function_name == "url_fetch":
                                url = function_args.get("url")
                                prompt = f"Please provide a clean, concise summary of the main content of the webpage at the following URL: {url}. Focus on the key facts and information presented on the page, omitting boilerplate like navigation menus, ads, and footers."
                                ipython = get_ipython()
                                function_response = ipython.run_cell_magic('tool', 'web_fetch', prompt)
                            else:
                                function_response = function_to_call(**function_args)
                            
                            # Store result in cache
                            self.analysis_cache[cache_key] = function_response

                        self.messages.append({"tool_call_id": tool_call["id"], "role": "tool", "name": function_name, "content": json.dumps(function_response)})
                    except (json.JSONDecodeError, KeyError) as e:
                        error_message = f"Error processing tool call for {function_name}: {e}"
                        yield f"\n[Error: {error_message}]"
                        self.messages.append({"tool_call_id": tool_call["id"], "role": "tool", "name": function_name, "content": json.dumps({"error": error_message})})
                continue
            else:
                self.messages.append({"role": "assistant", "content": full_response_content})
                break
