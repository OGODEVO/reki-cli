from datetime import datetime
import os
import time
import json
from zoneinfo import ZoneInfo
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.align import Align
from rich.table import Table
from tools.brave_search import BrowserTool

console = Console()

def display_intro():
    ascii_art = """
[bold dark_green]
██████╗ ███████╗██╗  ██╗██╗   ██████╗██╗     ██╗
██╔══██╗██╔════╝██║ ██╔╝██║   ██╔════╝██║     ██║
██████╔╝█████╗  █████╔╝ ██║   ██║     ██║     ██║
██╔══██╗██╔══╝  ██╔═██╗ ██║   ██║     ██║     ██║
██║  ██║███████╗██║  ██╗██║██╗╚██████╗███████╗███████╗
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚═╝ ╚═════╝╚══════╝╚══════╝
[/bold dark_green]
"""
    console.print(Align.center(ascii_art))

    with Live(console=console, refresh_per_second=12, transient=True) as live:
        start_time = time.time()
        while time.time() - start_time < 1.5:
            chicago_tz = ZoneInfo("America/Chicago")
            current_time = datetime.now(chicago_tz).strftime("%H:%M:%S")
            
            subtitle_table = Table.grid()
            subtitle_table.add_column(justify="right")
            subtitle_table.add_column(justify="left")
            
            subtitle_text = f"[bold white]reki-beta[/bold white] | [bold white]{current_time}[/bold white] "
            
            subtitle_table.add_row(subtitle_text, Spinner("dots12", style="bold dark_green"))
            
            live.update(Align.center(subtitle_table))
            time.sleep(0.1)

def get_api_key():
    api_key = os.environ.get("NOVITA_API_KEY")
    if not api_key:
        console.print(
            Panel(
                "[bold red]Error: NOVITA_API_KEY not found.[/bold red]\n\n"
                "Please create a '.env' file in the same directory as the script and add the following line:\n\n"
                "[bold cyan]NOVITA_API_KEY='your-api-key'[/bold cyan]",
                title="[bold red]Configuration Error[/bold red]",
                border_style="bold red",
            )
        )
        exit()
    return api_key


def count_tokens(messages, model="gpt-4"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        for key, value in message.items():
            if value:
                num_tokens += len(encoding.encode(str(value)))
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
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
            
            # Calculate the new stake based on the outcome
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


tools = [
    {
        "type": "function",
        "function": {
            "name": "load_json_file",
            "description": "Load a JSON file from the given path. Use this to read game stats or the current betting ledger.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the JSON file.",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_betting_ledger",
            "description": "Update the betting ledger with the result of a completed pick.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pick_details": {
                        "type": "object",
                        "description": "An object containing the details of the pick.",
                        "properties": {
                            "game": {"type": "string", "description": "The game the pick was for."},
                            "pick": {"type": "string", "description": "The pick that was made (e.g., 'OVER 210.5')."},
                            "stake": {"type": "number", "description": "The amount staked on the pick."},
                            "outcome": {"type": "string", "description": "The outcome of the pick ('win' or 'loss')."},
                            "profit": {"type": "number", "description": "The profit from the pick (if it was a win)."}
                        },
                        "required": ["game", "pick", "stake", "outcome"],
                    }
                },
                "required": ["pick_details"],
            },
        },
    }
]


browser_tool = BrowserTool()
tools.extend(browser_tool.get_tools())


def main():
    load_dotenv()
    display_intro()
    api_key = get_api_key()
    client = OpenAI(
        base_url="https://api.novita.ai/openai",
        api_key=api_key
    )

    console.print("\nType 'exit' or press Ctrl+C to end the chat.")

    try:
        with open("system_prompt.txt", "r") as f:
            system_prompt_template = f.read()
    except FileNotFoundError:
        console.print(
            Panel(
                "[bold red]Error: system_prompt.txt not found.[/bold red]\n\n"
                "Please create this file and add the system prompt template.",
                title="[bold red]Configuration Error[/bold red]",
                border_style="bold red",
            )
        )
        exit()

    chicago_tz = ZoneInfo("America/Chicago")
    current_date = datetime.now(chicago_tz).strftime("%A, %d %B %Y %I:%M:%S %p")
    system_prompt = system_prompt_template.replace("{current_date}", current_date)

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]α You:[/bold green]")
            if user_input.lower() == "exit":
                break

            if user_input.startswith("/load"):
                console.print(
                    Panel(
                        "[bold yellow]The /load command is deprecated. The AI will call tools for you.[/bold yellow]",
                        title="[bold yellow]Deprecated Command[/bold yellow]",
                        border_style="bold yellow",
                    )
                )

            messages.append({"role": "user", "content": user_input})

            while True:
                prompt_tokens = count_tokens(messages)
                with Live(
                    Spinner("dots", text="[bold white]Ω Reki:[/bold white] Thinking..."),
                    console=console,
                    transient=True,
                ) as live:
                    start_time = time.time()
                    model = "deepseek/deepseek-v3.2-exp"
                    stream = True
                    max_tokens = 65346
                    temperature = 1
                    top_p = 1
                    min_p = 0
                    top_k = 50
                    presence_penalty = 0
                    frequency_penalty = 0
                    repetition_penalty = 1
                    response_format = { "type": "text" }

                    chat_completion_res = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        stream=stream,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        presence_penalty=presence_penalty,
                        frequency_penalty=frequency_penalty,
                        response_format=response_format,
                        extra_body={
                        "top_k": top_k,
                        "repetition_penalty": repetition_penalty,
                        "min_p": min_p
                        }
                    )
                    live.stop()

                console.print(f"\n[bold white]Ω Reki:[/bold white]")
                full_response_content = ""
                tool_call_chunks = []
                
                if stream:
                    with Live(console=console, auto_refresh=False) as live_markdown:
                        for chunk in chat_completion_res:
                            if chunk.choices:
                                chunk_content = chunk.choices[0].delta.content or ""
                                full_response_content += chunk_content
                                live_markdown.update(Markdown(full_response_content), refresh=True)
                                
                                if chunk.choices[0].delta.tool_calls:
                                    for tool_call_chunk in chunk.choices[0].delta.tool_calls:
                                        if len(tool_call_chunks) <= tool_call_chunk.index:
                                            tool_call_chunks.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                                        
                                        chunk_data = tool_call_chunks[tool_call_chunk.index]
                                        if tool_call_chunk.id:
                                            chunk_data["id"] = tool_call_chunk.id
                                        if tool_call_chunk.function.name:
                                            chunk_data["function"]["name"] = tool_call_chunk.function.name
                                        if tool_call_chunk.function.arguments:
                                            chunk_data["function"]["arguments"] += tool_call_chunk.function.arguments
                else:
                    response_message = chat_completion_res.choices[0].message
                    full_response_content = response_message.content
                    if response_message.tool_calls:
                        tool_call_chunks = [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                            }
                            for tc in response_message.tool_calls
                        ]
                    console.print(Markdown(full_response_content))

                end_time = time.time()
                
                if tool_call_chunks:
                    response_message = {"role": "assistant", "tool_calls": tool_call_chunks}
                    messages.append(response_message)
                    
                    available_functions = {
                        "load_json_file": load_json_file,
                        "update_betting_ledger": update_betting_ledger,
                        "browser_search": browser_tool.search,
                    }
                    
                    for tool_call in tool_call_chunks:
                        function_name = tool_call["function"]["name"]
                        function_args_str = tool_call["function"]["arguments"]
                        
                        try:
                            function_args = json.loads(function_args_str)
                            function_to_call = available_functions[function_name]
                            
                            with Live(
                                Spinner("dots", text=f"[bold white]Executing function {function_name}... 🛠️[/bold white]"),
                                console=console,
                                transient=True,
                            ) as live_spinner:
                                if function_name == "load_json_file":
                                    function_response = function_to_call(file_path=function_args.get("file_path"))
                                elif function_name == "update_betting_ledger":
                                    function_response = function_to_call(pick_details=function_args.get("pick_details"))
                                elif function_name == "browser_search":
                                    function_response = function_to_call(query=function_args.get("query"))
                                else:
                                    function_response = {"error": "Unknown function"}
                                live_spinner.stop()
                                
                            messages.append(
                                {
                                    "tool_call_id": tool_call["id"],
                                    "role": "tool",
                                    "name": function_name,
                                    "content": json.dumps(function_response),
                                }
                            )
                        except json.JSONDecodeError:
                            console.print(Panel(f"[bold red]Error: Could not decode tool call arguments for {function_name}: {function_args_str}[/bold red]"))
                            break
                    continue

                else:
                    messages.append({"role": "assistant", "content": full_response_content})
                    completion_tokens = count_tokens([{"role": "assistant", "content": full_response_content}])
                    total_tokens = prompt_tokens + completion_tokens
                    
                    response_time = end_time - start_time
                    cps = len(full_response_content) / response_time if response_time > 0 else 0

                    stats_table = Table(show_header=False, show_edge=False, box=None, padding=(0, 1))
                    stats_table.add_column(style="dim")
                    stats_table.add_row(f"Response Time: {response_time:.2f}s | CPS: {cps:.2f} | Prompt: {prompt_tokens} tokens | Completion: {completion_tokens} tokens | Total: {total_tokens} tokens")
                    console.print(stats_table)
                    break

        except KeyboardInterrupt:
            console.print("\n[bold red]Exiting chat.[/bold red]")
            break
        except Exception as e:
            console.print(Panel(f"[bold red]An error occurred: {e}[/bold red]", title="[bold red]Error[/bold red]"))
            break

if __name__ == "__main__":
    main()

