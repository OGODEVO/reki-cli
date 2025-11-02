import os
import sys
import time
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import ChatAgent, count_tokens
from ui import TerminalUI

def get_env_vars():
    config = {
        "user_id": os.environ.get("USER_ID", "default_user"),
        "services": {
            "1": {
                "name": "reki-fast",
                "api_key": os.environ.get("XAI_API_KEY"),
                "base_url": os.environ.get("XAI_API_BASE_URL"),
                "model": os.environ.get("XAI_MODEL")
            },
            "2": {
                "name": "reki",
                "api_key": os.environ.get("NOVITA_API_KEY"),
                "base_url": os.environ.get("NOVITA_API_BASE_URL"),
                "model": os.environ.get("NOVITA_MODEL")
            }
        }
    }
    return config

def main():
    load_dotenv()
    ui = TerminalUI()
    ui.display_intro()

    config = get_env_vars()
    user_id = config["user_id"]

    # Interactive model selection
    choice = ui.prompt_for_model_choice()
    selected_service = config["services"][choice]
    
    api_key = selected_service["api_key"]
    api_base_url = selected_service["base_url"]
    model_name = selected_service["model"]
    service_name = selected_service["name"]

    if not api_key or not api_base_url or not model_name:
        ui.display_error(f"Configuration for {service_name} is missing from your .env file.")
        exit()

    ui.display_selection("🎲", "Model Selected", service_name)

    try:
        # Construct the path to system_prompt.txt relative to this file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(script_dir, "system_prompt.txt")
        with open(prompt_path, "r") as f:
            system_prompt_template = f.read()
    except FileNotFoundError:
        ui.display_error("system_prompt.txt not found in the 'reki' directory.")
        exit()

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        memory_path = os.path.join(script_dir, "memory.jsonl")
        summaries = []
        with open(memory_path, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    expires_at_str = entry.get("expires_at")
                    
                    is_expired = False
                    if expires_at_str:
                        expiration_dt = datetime.fromisoformat(expires_at_str)
                        if datetime.now() > expiration_dt:
                            is_expired = True
                    
                    if not is_expired:
                        summaries.append(entry.get("summary", ""))

                except (json.JSONDecodeError, ValueError):
                    # Handle cases where a line is not valid JSON or timestamp is malformed
                    continue
        memory_content = "\n".join(summaries)
    except FileNotFoundError:
        memory_content = ""

    chicago_tz = ZoneInfo("America/Chicago")
    current_date = datetime.now(chicago_tz).strftime("%A, %d %B %Y %I:%M:%S %p")
    system_prompt = system_prompt_template.replace("{current_date}", current_date)
    
    if memory_content:
        system_prompt = f"--- Previous Conversation Summaries ---\n{memory_content}\n\n--- Current Task ---\n{system_prompt}"

    agent = ChatAgent(api_key, user_id, system_prompt, model_name, api_base_url, ui)

    ui.console.print(f"\n[dim]Type 'exit' or press Ctrl+C to end the chat.[/dim]")

    while True:
        try:
            user_input = ui.get_user_input()
            if user_input.lower() == "exit":
                break

            if user_input.lower() == "/reset":
                agent.messages = [{"role": "system", "content": system_prompt}]
                ui.display_message("Conversation history has been reset.", "Reset", "yellow")
                continue
            
            if user_input.lower().startswith("/save"):
                agent.save_memory_entry(user_input)
                ui.display_message("Conversation thread saved to memory.", "Memory Saved", "cyan")
                continue

            prompt_tokens = count_tokens(agent.messages)
            start_time = time.time()
            
            response_stream = agent.get_response(user_input)
            full_response_content = ui.display_response_stream(response_stream)
            
            end_time = time.time()
            
            completion_tokens = count_tokens([{"role": "assistant", "content": full_response_content}])
            total_tokens = prompt_tokens + completion_tokens
            response_time = end_time - start_time
            cps = len(full_response_content) / response_time if response_time > 0 else 0

            ui.display_stats(response_time, cps, prompt_tokens, completion_tokens, total_tokens)

        except KeyboardInterrupt:
            ui.console.print("\n[bold red]Exiting chat.[/bold red]")
            break
        except Exception as e:
            ui.display_error(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    main()