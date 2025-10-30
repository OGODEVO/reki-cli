import os
import json
import tiktoken
from openai import OpenAI
from helpers.mem0_helper import Mem0Helper
from tools.brave_search import BrowserTool
from tools.web_fetcher import WebFetcherTool
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

def load_json_file(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "File not found."}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format."}

def update_betting_ledger(pick_details):
    try:
        with open("betting_ledger.json", "r+") as f:
            ledger = json.load(f)
            ledger["picks"].append(pick_details)
            
            if pick_details.get("outcome") == "win":
                ledger["current_stake"] += pick_details.get("profit", 0)
            elif pick_details.get("outcome") == "loss":
                ledger["current_stake"] -= pick_details.get("stake", 0)
            
            f.seek(0)
            json.dump(ledger, f, indent=2)
            f.truncate()
            return {"status": "success", "new_stake": ledger["current_stake"]}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return {"error": str(e)}

def read_text_file(file_path):
    try:
        with open(file_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return {"error": "File not found."}

class ChatAgent:
    def __init__(self, api_key, mem0_api_key, user_id, system_prompt):
        self.client = OpenAI(base_url="https://api.novita.ai/openai", api_key=api_key)
        self.mem0_helper = Mem0Helper(api_key=mem0_api_key, user_id=user_id)
        self.messages = [{"role": "system", "content": system_prompt}]
        
        self.browser_tool = BrowserTool()
        self.web_fetcher_tool = WebFetcherTool()
        
        self.tools = self._setup_tools()
        self.available_functions = self._setup_available_functions()

    def _setup_tools(self):
        tools = [
            {"type": "function", "function": {"name": "load_json_file", "description": "Load and parse a JSON file from a given path.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string", "description": "The path to the JSON file."}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "update_betting_ledger", "description": "Update the betting ledger with the result of a completed pick.", "parameters": {"type": "object", "properties": {"pick_details": {"type": "object", "description": "An object containing the details of the pick.", "properties": {"game": {"type": "string"}, "pick": {"type": "string"}, "stake": {"type": "number"}, "outcome": {"type": "string", "enum": ["win", "loss"]}, "profit": {"type": "number"}}, "required": ["game", "pick", "stake", "outcome"]}}, "required": ["pick_details"]}}},
            {"type": "function", "function": {"name": "read_text_file", "description": "Read a plain text file from the given path.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string", "description": "The path to the text file."}}, "required": ["file_path"]}}}
        ]
        tools.extend(self.browser_tool.get_tools())
        tools.extend(self.web_fetcher_tool.get_tools())
        return tools

    def _setup_available_functions(self):
        return {
            "load_json_file": load_json_file,
            "update_betting_ledger": update_betting_ledger,
            "read_text_file": read_text_file,
            "browser_search": self.browser_tool.search,
            "url_fetch": self.web_fetcher_tool.fetch,
        }

    def get_response(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        self.mem0_helper.add(user_input)

        while True:
            chat_completion_res = self.client.chat.completions.create(
                model="deepseek/deepseek-v3.2-exp", messages=self.messages, tools=self.tools, tool_choice="auto", stream=True, max_tokens=65346, temperature=1, top_p=1,
                presence_penalty=0, frequency_penalty=0, response_format={"type": "text"}, extra_body={"top_k": 50, "repetition_penalty": 1, "min_p": 0}
            )

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
                        
                        yield f"\n\nExecuting function: `{function_name}` with arguments: `{function_args}`\n\n"
                        
                        if function_name == "url_fetch":
                            url = function_args.get("url")
                            prompt = f"Please provide a clean, concise summary of the main content of the webpage at the following URL: {url}. Focus on the key facts and information presented on the page, omitting boilerplate like navigation menus, ads, and footers."
                            ipython = get_ipython()
                            function_response = ipython.run_cell_magic('tool', 'web_fetch', prompt)
                        else:
                            function_response = function_to_call(**function_args)
                        
                        self.messages.append({"tool_call_id": tool_call["id"], "role": "tool", "name": function_name, "content": json.dumps(function_response)})
                    except (json.JSONDecodeError, KeyError) as e:
                        error_message = f"Error processing tool call for {function_name}: {e}"
                        yield f"\n[Error: {error_message}]"
                        self.messages.append({"tool_call_id": tool_call["id"], "role": "tool", "name": function_name, "content": json.dumps({"error": error_message})})
                continue
            else:
                self.messages.append({"role": "assistant", "content": full_response_content})
                self.mem0_helper.add(full_response_content)
                break
